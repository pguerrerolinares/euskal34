"""Verificacion cruzada: glifos extraidos de los PNG  vs  bytes del texto en la ROM."""
import os
import nightwriting2 as D

ROM=os.environ.get('ROM') or os.path.join(os.path.dirname(os.path.abspath(__file__)),'pokemon-esmeralda.gba')
rom=open(ROM,'rb').read()   # la ROM no se redistribuye: pon la tuya aqui o en $ROM
OFF={'S1':0x2a73c2,'S2':0x2a73e5,'S3':0x2a73ff,'S4':0x2a741d,'S5':0x2a743b,
     'S6':0x2a7458,'S7':0x2a7472,'S8':0x2a748d,'S9':0x2a74a3}

# byte = bitmap braille con pesos dot1=1 dot2=4 dot3=16 dot4=2 dot5=8 dot6=32
W={1:1,2:4,3:16,4:2,5:8,6:32}
LAT={}
for ch,dots in {'a':'1','b':'12','c':'14','d':'145','e':'15','f':'124','g':'1245','h':'125',
  'i':'24','j':'245','k':'13','l':'123','m':'134','n':'1345','o':'135','p':'1234','q':'12345',
  'r':'1235','s':'234','t':'2345','u':'136','v':'1236','w':'2456','x':'1346','y':'13456',
  'z':'1356','.':'256',',':'2'}.items():
    LAT[sum(W[int(d)] for d in dots)]=ch
LAT[0x00]=' '; LAT[0xFE]='\n'

def rom_text(name):
    a=OFF[name]+6; out=[]
    while rom[a]!=0xFF: out.append(rom[a]); a+=1
    return out

pairs={}   # byte -> glifo extraido del PNG
allok=True
for n in [f'S{i}' for i in range(1,10)]:
    by=rom_text(n)
    # glifos del PNG, en orden, insertando ' ' en los separadores y '\n' entre lineas
    gl=[]
    for li,cells in enumerate(D.extract(n)):
        if li: gl.append(('NL',))
        for c in cells:
            if c is None: gl.append(('SP',)); continue
            k,v,g,ok=D.read(c)
            gl.append((k,v))
    if len(by)!=len(gl):
        print(f'{n}: LONGITUD distinta rom={len(by)} png={len(gl)}'); allok=False; continue
    for b,g in zip(by,gl):
        if b in pairs and pairs[b]!=g:
            print(f'{n}: byte {b:#04x} tiene dos glifos: {pairs[b]} vs {g}'); allok=False
        pairs[b]=g
inv={}
for b,g in pairs.items():
    if g in inv: print(f'glifo {g} usado por dos bytes {inv[g]:#04x} y {b:#04x}'); allok=False
    inv[g]=b
print(f'biyeccion byte<->glifo: {"OK" if allok else "FALLA"}  ({len(pairs)} simbolos distintos)')
print()
print(f'{"byte":>5} {"braille/latin":>13}  {"glifo en el PNG":<22} lectura')
for b in sorted(pairs):
    k,*v = pairs[b]
    if k=='nw':  gl=f'nightwriting {v[0]}'; rd=D.NW[v[0]]
    elif k=='br':gl=f'braille [{v[0]}]';     rd=D.BR[v[0]]
    else:        gl=k;                       rd={'SP':'(espacio)','NL':'(salto)'}[k]
    print(f'{b:#05x} {LAT.get(b,"?"):>13}  {gl:<22} {rd}')
