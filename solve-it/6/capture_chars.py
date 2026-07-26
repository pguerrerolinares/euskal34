#!/usr/bin/env python3
"""Captura CADA frame de advertising (sin cache/dedupe) de los beacons del reto
(MAC A0:F2:62:8x, ServiceData UUID 0x4242) y acumula, por beacon, el SET de
payloads y el CARÁCTER EXTRA (byte 21) con su case exacto. Objetivo: sacar la
palabra completa (hipótesis: ADRIFT / case mixto por 'cambio de estilo').

Corre esto PEGADO a un beacon (o paseándolo por la ruta). Loguea en vivo.
"""
import asyncio, os, time
from bleak import BleakScanner

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "chars_capture.log")
UUID_4242 = "00004242-0000-1000-8000-00805f9b34fb"
PREFIX = "A0:F2:62"
NAMES = {"A0:F2:62:85:7E:1A": "Venezia",
         "A0:F2:62:85:86:E6": "Brunwald",
         "A0:F2:62:85:72:6E": "Brody",
         "A0:F2:62:87:33:4E": "Iskenderun",
         "A0:F2:62:87:79:E2": "final"}
DURATION = 1200  # 20 min

seen = {}  # mac -> set(payloads)

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def cb(device, adv):
    mac = device.address.upper()
    if not mac.startswith(PREFIX):
        return
    sd = adv.service_data or {}
    payload = None
    for u, v in sd.items():
        if u.lower() == UUID_4242:
            payload = bytes(v)
    if payload is None:
        return
    txt = payload.decode("latin1")
    s = seen.setdefault(mac, set())
    if txt not in s:
        s.add(txt)
        extra = txt[20:] if len(txt) > 20 else ""
        nm = NAMES.get(mac, "?")
        log(f"{nm:10s} {mac}  len={len(txt):2d}  payload={txt!r}  EXTRA={extra!r}")

async def main():
    open(LOG, "w").close()
    log(f"== captura de chars extra (cada frame, {DURATION}s) ==")
    scanner = BleakScanner(detection_callback=cb, scanning_mode="active")
    await scanner.start()
    t0 = time.time()
    while time.time() - t0 < DURATION:
        await asyncio.sleep(5)
    await scanner.stop()
    log("== RESUMEN por beacon ==")
    order = ["Venezia", "Brunwald", "Brody", "Iskenderun", "final"]
    macbyname = {v: k for k, v in NAMES.items()}
    word = []
    for nm in order:
        mac = macbyname[nm]
        payloads = seen.get(mac, set())
        extras = sorted({p[20:] for p in payloads if len(p) > 20})
        log(f"  {nm:10s} extras={extras}")
        word.append("/".join(extras) if extras else "?")
    log("  PALABRA (orden cadena): " + " ".join(word))

asyncio.run(main())
