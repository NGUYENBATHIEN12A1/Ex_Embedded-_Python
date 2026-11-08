import argparse
import json
import math
import random
import threading
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


class FakeDevice:
    def __init__(self, device_id: str, args):
        self.device_id = device_id
        self.args = args
        self.base = f"{args.prefix}/{device_id}"
        self.interval = args.interval
        self.seq = 0
        self.wake = threading.Event()
        self.phase = random.uniform(0, 2 * math.pi)
        self.client = self._make_client()

    def _make_client(self):
        c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=self.device_id)
        c.will_set(f"{self.base}/status", "offline", qos=1, retain=True)
        c.on_connect = self._on_connect
        c.on_message = self._on_message
        c.reconnect_delay_set(1, 30)
        return c

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[{self.device_id}] connected ({reason_code})")
        client.publish(f"{self.base}/status", "online", qos=1, retain=True)
        client.subscribe(f"{self.base}/cmd", qos=1)

    def _ack(self, cmd, ok, **extra):
        self.client.publish(f"{self.base}/ack", json.dumps({"cmd": cmd, "ok": ok, "ts": int(time.time()), **extra}), qos=1)

    def _on_message(self, client, userdata, msg):
        try:
            c = json.loads(msg.payload)
            name = c.get("cmd")
        except (ValueError, AttributeError):
            print(f"[{self.device_id}] bad cmd {msg.payload!r}")
            return
        print(f"[{self.device_id}] cmd {c}")
        if name == "set_interval":
            try:
                self.interval = max(2, min(3600, int(c.get("value"))))
            except (TypeError, ValueError):
                self._ack(name, False, msg="invalid value")
                return
            self._ack(name, True, value=self.interval)
            self.wake.set()
        elif name == "read_now":
            self._ack(name, True)
            self.wake.set()
        elif name == "reboot":
            self._ack(name, True)
            threading.Thread(target=self._reboot, daemon=True).start()
        else:
            self._ack(str(name), False, msg="unknown command")

    def _reboot(self):
        time.sleep(0.5)
        self.client.publish(f"{self.base}/status", "offline", qos=1, retain=True)
        self.client.disconnect()
        self.client.loop_stop()
        print(f"[{self.device_id}] rebooting...")
        time.sleep(3)
        self.seq = 0
        self.client = self._make_client()
        self.start()

    def reading(self, t: float) -> dict:
        day = (t % 86400) / 86400 * 2 * math.pi
        temp = 28 + 4 * math.sin(day - math.pi / 2 + self.phase / 6) + random.gauss(0, 0.2)
        if self.args.hot:
            temp = 36 + random.uniform(0, 2)
        hum = max(0, min(100, 75 - 2.5 * (temp - 28) + random.gauss(0, 1)))
        pres = 1009 + 1.5 * math.sin(day * 2 + self.phase) + random.gauss(0, 0.1)
        sun = max(0.0, math.sin(day - math.pi / 2))
        light = max(0, 20000 * sun ** 2 + random.gauss(0, 15) + 5)
        data = {
            "device_id": self.device_id, "ts": int(t), "seq": self.seq,
            "temperature": round(temp, 1), "humidity": round(hum, 1),
            "pressure": round(pres, 2), "light": round(light, 1),
            "rssi": random.randint(-75, -50), "interval": self.interval, "errors": [],
        }
        if random.random() * 100 < self.args.sensor_fail:
            data.update(temperature=None, humidity=None, errors=["dht22"])
        return data

    def bad_payload(self) -> str:
        return random.choice([
            "{not json",
            json.dumps({"device_id": self.device_id, "temperature": 999, "humidity": 50}),
            json.dumps({"device_id": self.device_id, "humidity": -5}),
            json.dumps({"device_id": "other-device", "temperature": 25}),
            json.dumps({"temperature": "hot"}),
        ])

    def start(self):
        self.client.connect_async(self.args.host, self.args.port, keepalive=15)
        self.client.loop_start()

    def run(self):
        self.start()
        while not self.client.is_connected():
            time.sleep(0.1)
        while True:
            if self.client.is_connected():
                if random.random() * 100 < self.args.bad:
                    self.client.publish(f"{self.base}/data", self.bad_payload(), qos=1)
                    print(f"[{self.device_id}] sent BAD payload")
                if random.random() * 100 < self.args.drop:
                    print(f"[{self.device_id}] dropped seq {self.seq}")
                else:
                    data = self.reading(time.time())
                    self.client.publish(f"{self.base}/data", json.dumps(data), qos=1)
                    print(f"[{self.device_id}] seq={data['seq']} T={data['temperature']} H={data['humidity']} "
                          f"P={data['pressure']} L={data['light']}")
                self.seq += 1
            self.wake.wait(self.interval)
            self.wake.clear()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--prefix", default="vku/weather")
    p.add_argument("--devices", type=int, default=1, help="số thiết bị giả lập (esp32-01, esp32-02, ...)")
    p.add_argument("--first", type=int, default=1, help="số thứ tự thiết bị đầu tiên (--first 3 → esp32-03)")
    p.add_argument("--interval", type=int, default=5, help="chu kỳ gửi (giây)")
    p.add_argument("--drop", type=float, default=0, help="%% gói bị bỏ qua (test phát hiện mất gói)")
    p.add_argument("--bad", type=float, default=0, help="%% bản tin lỗi (test validate)")
    p.add_argument("--sensor-fail", type=float, default=0, help="%% lần DHT22 đọc lỗi")
    p.add_argument("--hot", action="store_true", help="nhiệt độ > 35 °C để test cảnh báo")
    args = p.parse_args()

    devices = [FakeDevice(f"esp32-{i + args.first:02d}", args) for i in range(args.devices)]
    threads = [threading.Thread(target=d.run, daemon=True) for d in devices]
    for t in threads:
        t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("stopped (không gửi DISCONNECT → broker phát LWT offline)")


if __name__ == "__main__":
    main()
