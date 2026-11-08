import gc
import json
import time

import machine
from machine import WDT, Pin
from umqtt.simple import MQTTClient

import config
import wifi
from sensors import Sensors

BASE = "%s/%s" % (config.TOPIC_PREFIX, config.DEVICE_ID)
T_DATA = BASE + "/data"
T_STATUS = BASE + "/status"
T_CMD = BASE + "/cmd"
T_ACK = BASE + "/ack"
STATE_FILE = "state.json"

EPOCH_OFFSET = 946684800 if time.gmtime(0)[0] == 2000 else 0

led = Pin(config.LED_PIN, Pin.OUT)
wdt = WDT(timeout=config.WDT_TIMEOUT_MS)
sensors = Sensors()
print("I2C scan:", sensors.scan())

client = None
seq = 0
read_now = False
reboot_pending = False
last_io = 0


def clamp_interval(v):
    return max(config.MIN_INTERVAL_S, min(config.MAX_INTERVAL_S, int(v)))


def load_interval():
    try:
        with open(STATE_FILE) as f:
            return clamp_interval(json.load(f)["interval"])
    except (OSError, ValueError, KeyError):
        return clamp_interval(config.INTERVAL_S)


def save_interval(v):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"interval": v}, f)
    except OSError as e:
        print("save state error:", e)


interval = load_interval()


def unix_time():
    t = int(time.time()) + EPOCH_OFFSET
    return t if t > 1700000000 else None


def sleep_feed(seconds):
    end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        wdt.feed()
        led.value(not led.value())
        time.sleep_ms(250)


def publish(topic, payload, retain=False):
    global last_io
    client.publish(topic, payload, retain=retain, qos=1)
    last_io = time.ticks_ms()


def ack(cmd, ok, **extra):
    extra.update({"cmd": cmd, "ok": ok, "ts": unix_time()})
    publish(T_ACK, json.dumps(extra))


def on_cmd(topic, msg):
    global interval, read_now, reboot_pending
    try:
        c = json.loads(msg)
        name = c.get("cmd")
    except (ValueError, AttributeError):
        print("bad cmd:", msg)
        return
    print("cmd:", c)
    if name == "set_interval":
        try:
            interval = clamp_interval(c.get("value"))
        except (TypeError, ValueError):
            ack(name, False, msg="invalid value")
            return
        save_interval(interval)
        ack(name, True, value=interval)
    elif name == "read_now":
        read_now = True
        ack(name, True)
    elif name == "reboot":
        reboot_pending = True
        ack(name, True)
    else:
        ack(str(name), False, msg="unknown command")


def mqtt_connect():
    global client
    c = MQTTClient(
        config.DEVICE_ID,
        config.MQTT_HOST,
        port=config.MQTT_PORT,
        user=config.MQTT_USER,
        password=config.MQTT_PASSWORD,
        keepalive=config.MQTT_KEEPALIVE,
    )
    c.set_last_will(T_STATUS, "offline", retain=True, qos=1)
    c.set_callback(on_cmd)
    try:
        c.connect(timeout=10)
    except TypeError:
        c.connect()
    client = c
    publish(T_STATUS, "online", retain=True)
    client.subscribe(T_CMD, qos=1)
    led.on()
    print("MQTT: connected to", config.MQTT_HOST)


def mqtt_close():
    global client
    if client:
        try:
            client.sock.close()
        except Exception:
            pass
    client = None


def send_reading():
    global seq
    data = sensors.read_all()
    data["device_id"] = config.DEVICE_ID
    data["ts"] = unix_time()
    data["seq"] = seq
    data["rssi"] = wifi.rssi()
    data["interval"] = interval
    led.off()
    publish(T_DATA, json.dumps(data))
    led.on()
    seq += 1
    if data["errors"]:
        print("sensor errors:", data["errors"])


def run():
    global read_now, last_io
    backoff = 1
    last_send = None
    while True:
        wdt.feed()
        if not wifi.is_connected():
            mqtt_close()
            if not wifi.connect(wdt=wdt, led=led):
                sleep_feed(2)
            continue

        if client is None:
            try:
                mqtt_connect()
                backoff = 1
            except Exception as e:
                print("MQTT: connect failed (%s), retry in %ds" % (e, backoff))
                mqtt_close()
                sleep_feed(backoff)
                backoff = min(backoff * 2, 60)
                continue

        try:
            client.check_msg()
            if reboot_pending:
                publish(T_STATUS, "offline", retain=True)
                client.disconnect()
                time.sleep_ms(500)
                machine.reset()
            now = time.ticks_ms()
            if read_now or last_send is None or time.ticks_diff(now, last_send) >= interval * 1000:
                read_now = False
                last_send = now
                send_reading()
                gc.collect()
            elif time.ticks_diff(now, last_io) > config.MQTT_KEEPALIVE * 500:
                client.ping()
                last_io = now
        except Exception as e:
            print("MQTT: connection lost:", e)
            led.off()
            mqtt_close()
        time.sleep_ms(50)


run()
