#!/usr/bin/env python3
"""Monitoriza beacons BLE del reto (UUID 0x4242) y captura el payload de 'Brunwald'.
Escanea en bucle; cuando ve un device cuyo nombre contiene 'brunwald' O que emite
ServiceData bajo UUID 0000**4242**, extrae los bytes -> ASCII y lo guarda.
"""
import subprocess, re, time, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "brunwald_capture.log")
OUT = os.path.join(HERE, "brunwald_payload.txt")
TARGET_NAME = "brunwald"
SIG_UUID = "4242"          # firma del reto (0x4242), como Venezia
MAX_MINUTES = 25
CYCLE_SCAN = 12            # segundos de escaneo por ciclo

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
    # escaneo activo que refresca ServiceData/RSSI y devuelve
    bctl(["--timeout", str(secs), "scan", "on"], timeout=secs + 8)

def list_devices():
    out = bctl(["devices"])
    devs = []
    for ln in out.splitlines():
        m = re.match(r"Device ([0-9A-F:]{17})\s?(.*)", ln.strip())
        if m:
            devs.append((m.group(1), m.group(2).strip()))
    return devs

def extract_servicedata_4242(info):
    """Devuelve (uuid, ascii) del bloque ServiceData que contenga 4242, si existe."""
    lines = info.splitlines()
    for i, ln in enumerate(lines):
        if "ServiceData." in ln and SIG_UUID in ln:
            uuid = ln.strip().split("ServiceData.")[1].rstrip(":")
            hexbytes = []
            for j in range(i + 1, len(lines)):
                # las líneas de datos empiezan con espacios y pares hex
                hexpart = lines[j][:49]  # primeros 16 bytes
                found = re.findall(r"\b([0-9a-fA-F]{2})\b", hexpart)
                if not found:
                    break
                hexbytes += found
            raw = bytes(int(h, 16) for h in hexbytes)
            ascii_ = raw.decode("latin1")
            return uuid, ascii_, raw.hex()
    return None

def main():
    open(LOG, "w").close()
    log(f"== monitor Brunwald arrancado (max {MAX_MINUTES} min) ==")
    deadline = time.time() + MAX_MINUTES * 60
    seen_names = set()
    cycle = 0
    while time.time() < deadline:
        cycle += 1
        scan(CYCLE_SCAN)
        devs = list_devices()
        # log de novedades por nombre
        for mac, name in devs:
            if name and name not in seen_names:
                seen_names.add(name)
                log(f"nuevo device: {mac}  '{name}'")
        # revisa cada device por firma 4242 o nombre objetivo
        for mac, name in devs:
            info = bctl(["info", mac])
            hit_name = TARGET_NAME in name.lower()
            hit_uuid = ("ServiceData." in info and SIG_UUID in info)
            if hit_name or hit_uuid:
                res = extract_servicedata_4242(info)
                if res:
                    uuid, ascii_, hx = res
                    log(f"*** CAPTURA {mac} '{name}' UUID={uuid}")
                    log(f"*** ASCII : {ascii_!r}")
                    log(f"*** HEX   : {hx}")
                    with open(OUT, "w") as f:
                        f.write(f"mac={mac}\nname={name}\nuuid={uuid}\nascii={ascii_}\nhex={hx}\n")
                    log("payload guardado en brunwald_payload.txt -> FIN")
                    return 0
                elif hit_name:
                    log(f"'{name}' visto ({mac}) pero aún sin ServiceData {SIG_UUID}; reintento…")
        log(f"ciclo {cycle}: {len(devs)} devices, sin captura todavía")
    log("== timeout sin capturar Brunwald ==")
    return 1

if __name__ == "__main__":
    sys.exit(main())
