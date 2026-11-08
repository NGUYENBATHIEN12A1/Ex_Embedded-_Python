# Code explained — Environmental Monitoring Station

A line-by-line walkthrough of the code written for this project, grouped by part.
Each row starts with the line numbers it explains. In the Markdown files they are links: open them in VS Code (preview with Ctrl+Shift+V) and click to jump to that exact line. `code-explained.html` shows the same tables with the source code next to each explanation.

| Part | Files | What it covers |
|---|---|---|
| [1. Firmware](01-firmware.md) | `firmware/*.py`, `firmware/lib/*.py` | MicroPython on the ESP32: Wi-Fi, sensors, BMP180 maths, MQTT, Last Will, watchdog, reconnect with backoff |
| [2. Tests and tools](02-tests-and-tools.md) | `tests/*`, `tools/*`, `broker/*` | The firmware maths test, the ESP32 simulator, broker and Node-RED configuration |

Not explained line by line, because it is third-party code: `firmware/lib/umqtt/simple.py` (the official MicroPython MQTT library, summarised at the end of Part 1). The dashboard is a Node-RED flow (`node-red/flows.json`), edited in the Node-RED editor rather than as code.

## The whole system in one picture

```
 ESP32 (firmware)                    Computer
 ┌──────────────────┐   MQTT    ┌───────────┐   MQTT   ┌─────────────────────────┐  WebSocket  ┌────────────┐
 │ sensors.py reads │ ───────►  │ Mosquitto │ ───────► │ Node-RED flow           │ ──────────► │ Browser    │
 │ main.py publishes│ ◄───────  │  broker   │ ◄─────── │ (gauges, charts, alerts)│ ◄────────── │ :1880/ui   │
 └──────────────────┘ commands  └───────────┘ commands └─────────────────────────┘   buttons   └────────────┘
```

Suggested reading order for a presentation or defence: **Part 1 §1.7** (main loop), then the Node-RED flow in the editor (tab **VKU Weather**). Together they follow one reading from the sensor to the screen.
