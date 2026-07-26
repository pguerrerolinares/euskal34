import struct, sys, os

_HERE = os.path.dirname(os.path.abspath(__file__))
data = open(os.path.join(_HERE, 'pokemon-esmeralda.sav'), 'rb').read()

# Gen3 charset (English/Western)
CHARS = {
 0x00:' ',0x1B:'é',0x2D:'&',0x2E:'+',
 0xA1:'0',0xA2:'1',0xA3:'2',0xA4:'3',0xA5:'4',0xA6:'5',0xA7:'6',0xA8:'7',0xA9:'8',0xAA:'9',
 0xAB:'!',0xAC:'?',0xAD:'.',0xAE:'-',0xAF:'・',0xB0:'...',0xB1:'"',0xB2:'"',0xB3:"'",0xB4:"'",
 0xB5:'♂',0xB6:'♀',0xB7:'$',0xB8:',',0xB9:'x',0xBA:'/',
 0xBB:'A',0xBC:'B',0xBD:'C',0xBE:'D',0xBF:'E',0xC0:'F',0xC1:'G',0xC2:'H',0xC3:'I',0xC4:'J',
 0xC5:'K',0xC6:'L',0xC7:'M',0xC8:'N',0xC9:'O',0xCA:'P',0xCB:'Q',0xCC:'R',0xCD:'S',0xCE:'T',
 0xCF:'U',0xD0:'V',0xD1:'W',0xD2:'X',0xD3:'Y',0xD4:'Z',
 0xD5:'a',0xD6:'b',0xD7:'c',0xD8:'d',0xD9:'e',0xDA:'f',0xDB:'g',0xDC:'h',0xDD:'i',0xDE:'j',
 0xDF:'k',0xE0:'l',0xE1:'m',0xE2:'n',0xE3:'o',0xE4:'p',0xE5:'q',0xE6:'r',0xE7:'s',0xE8:'t',
 0xE9:'u',0xEA:'v',0xEB:'w',0xEC:'x',0xED:'y',0xEE:'z',
 0xFF:'',  # terminator
}
def dec(b):
    out=''
    for c in b:
        if c==0xFF: break
        out+=CHARS.get(c, '<%02X>'%c)
    return out

SIG=0x08012025
def sections(base):
    secs={}
    for i in range(14):
        off=base+i*0x1000
        sec=data[off:off+0x1000]
        sid=struct.unpack('<H',sec[0xFF4:0xFF6])[0]
        sig=struct.unpack('<I',sec[0xFF8:0xFFC])[0]
        idx=struct.unpack('<I',sec[0xFFC:0x1000])[0]
        if sig==SIG:
            secs[sid]=(sec,idx,off)
    return secs

A=sections(0x0000)
B=sections(0xE000)
def saveidx(secs):
    for sid,(s,idx,o) in secs.items():
        return idx
    return -1
iA=saveidx(A); iB=saveidx(B)
print(f'Slot A sections={sorted(A)} idx={iA}')
print(f'Slot B sections={sorted(B)} idx={iB}')
use = A if iA>=iB else B
print('USING slot', 'A' if use is A else 'B')

# trainer name section 0 offset 0
if 0 in use:
    tn=use[0][0][0x00:0x08]
    print('Trainer name:', repr(dec(tn)))

# reconstruct: team in section 1
def mon_headers(blob, size, count, label):
    res=[]
    for i in range(count):
        m=blob[i*size:(i+1)*size]
        if len(m)<32: break
        pid=struct.unpack('<I',m[0:4])[0]
        otid=struct.unpack('<I',m[4:8])[0]
        nick=dec(m[8:18])
        ot=dec(m[20:27])
        # decrypt substructures to get species
        key=pid^otid
        order=pid%24
        # growth substructure position
        ORDERS=['GAEM','GAME','GEAM','GEMA','GMAE','GMEA','AGEM','AGME','AEGM','AEMG','AMGE','AMEG',
                'EGAM','EGMA','EAGM','EAMG','EMGA','EMAG','MGAE','MGEA','MAGE','MAEG','MEGA','MEAG']
        species=None
        if pid or otid:
            data32=m[32:32+48]
            dec_words=b''
            for w in range(12):
                val=struct.unpack('<I',data32[w*4:w*4+4])[0]^key
                dec_words+=struct.pack('<I',val)
            gpos=ORDERS[order].index('G')
            growth=dec_words[gpos*12:gpos*12+12]
            species=struct.unpack('<H',growth[0:2])[0]
        if pid==0 and otid==0 and not nick:
            continue
        res.append((label,i,pid,otid,nick,ot,species))
    return res

allmons=[]
if 1 in use:
    s1=use[1][0]
    teamsize=struct.unpack('<I',s1[0x234:0x238])[0]
    print('Team size:', teamsize)
    allmons+=mon_headers(s1[0x238:0x238+600],100,min(teamsize,6),'PARTY')

# boxes: sections 5..13 form PC buffer; box mon 80 bytes. PC storage starts in section 5.
pc=b''
for sid in range(5,14):
    if sid in use:
        # each PC section uses 0xF80 bytes of data (3968) except maybe
        pc+=use[sid][0][0:0xF80]
# PC structure: first 4 bytes current box, then 14 boxes*30*80 mon data, then box names
# box mons start at offset 4
boxblob=pc[4:4+14*30*80]
allmons+=mon_headers(boxblob,80,14*30,'BOX')

print('\n=== NON-EMPTY MONS (species, nick, OT) ===')
for label,i,pid,otid,nick,ot,sp in allmons:
    print(f'{label}[{i:3}] sp={sp} nick={nick!r} OT={ot!r} pid={pid:08x} otid={otid:08x}')
print('total mons:', len(allmons))

# --- box names ---
print('\n=== BOX NAMES ===')
# pc buffer already reconstructed above as `pc`
namebase=4+14*30*80
for b in range(14):
    nm=pc[namebase+b*9:namebase+b*9+9]
    print(f'Box{b+1}: {dec(nm)!r}  hex={nm.hex()}')
# current box
import struct as _s
print('current box idx u32@0:', _s.unpack('<I',pc[0:4])[0])
