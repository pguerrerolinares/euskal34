#!/usr/bin/env python3
"""
temple_run.py - CLI text-in / text-out contra TempleOS (variante file-drop B1).

  python3 temple_run.py 'GodBitsIns(63,6697221640600119645);GodBiblePassage;'
      -> imprime a stdout el texto que TempleOS escribio en C:/RESULT.TXT

Flujo (cero screenshots, cero vision):
  1) Crea un overlay qcow2 con backing = temple.qcow2 (NO toca el disco original).
  2) Arranca QEMU headless con KVM y monitor HMP en un socket unix.
  3) Navega el menu de boot a ciegas (sleeps configurables) hasta el prompt C:/Home.
  4) Teclea via 'sendkey' un wrapper HolyC que redirige Fs->put_doc a un
     DolDoc DOCF_PLAIN_TEXT ligado a C:/RESULT.TXT, ejecuta el comando del
     usuario, y hace DocWrite (vuelca texto plano a disco, sincrono).
  5) Mata la VM. El overlay ya contiene RESULT.TXT.
  6) Convierte el overlay a raw y lee C:/RESULT.TXT del FAT32 (reusa ouija/extract.py).
  7) Imprime el texto y limpia temporales (salvo --keep).

El wrapper resuelve el problema real: GodWord/GodBiblePassage son U0 (imprimen,
no devuelven), asi que MStrPrint/StrPrint NO capturan su salida. Redirigir el
put_doc SI la captura (idioma confirmado en el source: LinkChk.HC/SpriteEd.HC).
"""
import argparse, os, shutil, signal, socket, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(HERE)          # el paquete 'ouija' vive en la raiz del repo, no aqui
sys.path.insert(0, RAIZ)
from ouija.extract import FAT32, read_partitions   # reuso del parser FAT32

# --- keymap HMP sendkey (de type_slow.py) ---
KM = {' ':'spc','.':'dot',',':'comma',';':'semicolon',"'":'apostrophe',
 '(':'shift-9',')':'shift-0','"':'shift-apostrophe',':':'shift-semicolon',
 '/':'slash','-':'minus','_':'shift-minus','=':'equal','+':'shift-equal',
 '*':'shift-8','&':'shift-7','!':'shift-1','%':'shift-5','#':'shift-3',
 '<':'shift-comma','>':'shift-dot','{':'shift-bracket_left','}':'shift-bracket_right',
 '[':'bracket_left',']':'bracket_right','?':'shift-slash','$':'shift-4','@':'shift-2',
 '\\':'backslash','^':'shift-6','|':'shift-backslash','~':'shift-grave_accent','`':'grave_accent'}
def keyfor(c):
    if c.isalpha(): return ('shift-' if c.isupper() else '') + c.lower()
    if c.isdigit(): return c
    return KM.get(c)

class Mon:
    """Monitor HMP sobre socket unix."""
    def __init__(s, path):
        for _ in range(50):
            if os.path.exists(path): break
            time.sleep(0.1)
        s.s = socket.socket(socket.AF_UNIX); s.s.connect(path); s.s.settimeout(2)
        time.sleep(0.2); s._drain()
    def _drain(s):
        try: s.s.recv(65536)
        except Exception: pass
    def cmd(s, c):
        s.s.sendall((c+"\n").encode()); time.sleep(0.08); s._drain()
    def key(s, k, delay=0.06):
        s.cmd("sendkey "+k); time.sleep(delay)
    def type(s, text, cps_delay=0.06):
        bad = [c for c in text if keyfor(c) is None]
        if bad: raise ValueError("sin tecla para: %r" % set(bad))
        for c in text:
            s.key(keyfor(c), cps_delay)
    def enter(s): s.key('ret', 0.15)
    def close(s):
        try: s.s.close()
        except Exception: pass

WRAP = ('CDoc *o=DocPut,*d=DocNew("C:/RESULT.TXT");d->flags|=DOCF_PLAIN_TEXT;'
        'Fs->put_doc=d;{cmd}Fs->put_doc=o;DocWrite(d);DocDel(d);')

def read_result(raw_path, fname="RESULT.TXT"):
    m = open(raw_path, 'rb').read()
    for lba, _ in read_partitions(m):
        fs = FAT32(m, lba)
        for name, attr, clus, size in fs.listdir(fs.root):
            if name.upper() == fname.upper() and not (attr & 0x10):
                return fs.read(clus, size).decode('latin1')
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command', help='HolyC a ejecutar, p.ej. "GodWord;"')
    ap.add_argument('--qcow', default=os.path.join(HERE, 'temple.qcow2'))
    ap.add_argument('--boot-wait', type=float, default=35.0, help='seg de arranque hasta el prompt')
    ap.add_argument('--exec-wait', type=float, default=6.0, help='seg tras teclear el comando')
    ap.add_argument('--mem', default='768')
    ap.add_argument('--no-kvm', action='store_true')
    ap.add_argument('--keep', action='store_true', help='no borrar overlay/raw ni matar limpio (debug)')
    ap.add_argument('--no-tour', action='store_true', help='no contestar "n" al prompt Take Tour')
    a = ap.parse_args()

    work = tempfile.mkdtemp(prefix='temple_run_')
    overlay = os.path.join(work, 'overlay.qcow2')
    sock = os.path.join(work, 'mon.sock')
    raw = os.path.join(work, 'result.raw')
    qemu = None
    try:
        subprocess.run(['qemu-img','create','-f','qcow2','-b',os.path.abspath(a.qcow),
                        '-F','qcow2', overlay], check=True, capture_output=True)
        cmd = ['qemu-system-x86_64','-m',a.mem,
               '-drive','file=%s,format=qcow2'%overlay,
               '-display','none','-vga','std',
               '-monitor','unix:%s,server,nowait'%sock,
               '-rtc','base=localtime']
        if not a.no_kvm and os.path.exists('/dev/kvm'):
            cmd += ['-enable-kvm']
        qemu = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mon = Mon(sock)

        # --- navegacion del boot a ciegas ---
        time.sleep(2.0)
        mon.key('1'); mon.enter()          # menu de boot: Drive C
        print("[*] arrancando, esperando %.0fs..." % a.boot_wait, file=sys.stderr)
        time.sleep(a.boot_wait)
        if not a.no_tour:
            mon.key('n'); time.sleep(1.5)  # prompt "Take Tour(y or n)?" -> n

        # --- teclear el wrapper ---
        holyc = WRAP.format(cmd=a.command.rstrip())
        if not holyc.rstrip().endswith(';'): holyc += ';'
        print("[*] tecleando %d chars de HolyC..." % len(holyc), file=sys.stderr)
        mon.type(holyc); mon.enter()
        time.sleep(a.exec_wait)
        mon.close()

        # --- apagar y extraer ---
        if not a.keep:
            qemu.send_signal(signal.SIGTERM)
        try: qemu.wait(timeout=8)
        except subprocess.TimeoutExpired: qemu.kill(); qemu.wait()
        qemu = None

        subprocess.run(['qemu-img','convert','-O','raw', overlay, raw],
                       check=True, capture_output=True)
        txt = read_result(raw)
        if txt is None:
            print("[!] RESULT.TXT no encontrado. Sube --boot-wait/--exec-wait o usa --keep para depurar.",
                  file=sys.stderr)
            sys.exit(2)
        sys.stdout.write(txt)
        if not txt.endswith('\n'): sys.stdout.write('\n')
    finally:
        if qemu is not None:
            try: qemu.kill(); qemu.wait()
            except Exception: pass
        if a.keep:
            print("[keep] work dir: %s" % work, file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)

if __name__ == '__main__':
    main()
