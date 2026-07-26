#!/usr/bin/env python3
"""Captura CUALQUIER beacon BLE del reto (ServiceData UUID 0x4242) cuyo payload
sea nuevo (distinto de Venezia/Brunwald ya vistos). Pensado para pasearlo por la
zona de 'componentes electrónicos'. Guarda nombre + payload ASCII y sale.
"""
import subprocess, re, time, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "next_capture.log")
OUT = os.path.join(HERE, "next_payload.txt")
SIG_UUID = "4242"
SEEN = {"tinyurl.com/4vt9d7ut", "tinyurl.com/4zykhx5e", "tinyurl.com/4zykhx5eD",
        "tinyurl.com/4zcrcvek", "tinyurl.com/4zcrcvekR",
        "tinyurl.com/2dt4387w", "tinyurl.com/2dt4387wf"}
MAX_MINUTES = 30
CYCLE_SCAN = 12

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def bctl(cmd, timeout=20):
    try:
        return subprocess.run(["bluetoothctl", *cmd], capture_output=True,
                              text=True, timeout=timeout).stdout
    except Exception as e:
        return f"__err__ {e}"

def scan(secs):
    bctl(["--timeout", str(secs), "scan", "on"], timeout=secs + 8)

def list_devices():
    devs = []
    for ln in bctl(["devices"]).splitlines():
        m = re.match(r"Device ([0-9A-F:]{17})\s?(.*)", ln.strip())
        if m:
            devs.append((m.group(1), m.group(2).strip()))
    return devs

def extract_4242(info):
    lines = info.splitlines()
    for i, ln in enumerate(lines):
        if "ServiceData." in ln and SIG_UUID in ln:
            uuid = ln.strip().split("ServiceData.")[1].rstrip(":")
            hexbytes = []
            for j in range(i + 1, len(lines)):
                found = re.findall(r"\b([0-9a-fA-F]{2})\b", lines[j][:49])
                if not found:
                    break
                hexbytes += found
            raw = bytes(int(h, 16) for h in hexbytes)
            return uuid, raw.decode("latin1"), raw.hex()
    return None

def main():
    open(LOG, "w").close()
    log(f"== monitor beacon 0x4242 NUEVO (max {MAX_MINUTES} min) ==")
    deadline = time.time() + MAX_MINUTES * 60
    seen_names = set()
    cycle = 0
    while time.time() < deadline:
        cycle += 1
        scan(CYCLE_SCAN)
        devs = list_devices()
        for mac, name in devs:
            if name and name not in seen_names:
                seen_names.add(name)
                log(f"nuevo device: {mac}  '{name}'")
        for mac, name in devs:
            info = bctl(["info", mac])
            if "ServiceData." in info and SIG_UUID in info:
                res = extract_4242(info)
                if not res:
                    continue
                uuid, ascii_, hx = res
                ascii_clean = ascii_.strip()
                # ¿payload nuevo? (normaliza quitando último char por si trae byte espurio)
                if ascii_clean in SEEN or ascii_clean[:-1] in SEEN:
                    continue
                log(f"*** CAPTURA NUEVA {mac} '{name}' UUID={uuid}")
                log(f"*** ASCII : {ascii_!r}")
                log(f"*** HEX   : {hx}")
                with open(OUT, "w") as f:
                    f.write(f"mac={mac}\nname={name}\nuuid={uuid}\nascii={ascii_}\nhex={hx}\n")
                log("payload nuevo guardado en next_payload.txt -> FIN")
                return 0
        log(f"ciclo {cycle}: {len(devs)} devices, sin beacon nuevo")
    log("== timeout sin beacon nuevo ==")
    return 1

if __name__ == "__main__":
    sys.exit(main())
