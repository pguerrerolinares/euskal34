import struct
import os
_HERE=os.path.dirname(os.path.abspath(__file__))
data=open(os.path.join(_HERE,'pokemon-esmeralda.sav'),'rb').read()
def sec(i): return data[i*0x1000:i*0x1000+0x1000]
secs={}
for i in range(14):
    s=sec(i); sid=struct.unpack('<H',s[0xFF4:0xFF6])[0]; secs[sid]=s
pc=b''
for sid in range(5,14): pc+=secs[sid][0:0xF80]
m=pc[4+31*80:4+31*80+80]
pid,otid=struct.unpack('<II',m[0:8]); key=pid^otid; order=pid%24
ORD=['GAEM','GAME','GEAM','GEMA','GMAE','GMEA','AGEM','AGME','AEGM','AEMG','AMGE','AMEG',
     'EGAM','EGMA','EAGM','EAMG','EMGA','EMAG','MGAE','MGEA','MAGE','MAEG','MEGA','MEAG']
raw=m[32:32+48]
dw=b''.join(struct.pack('<I',struct.unpack('<I',raw[w*4:w*4+4])[0]^key) for w in range(12))
S={c:dw[j*12:j*12+12] for j,c in enumerate(ORD[order])}
G,A,E,M=S['G'],S['A'],S['E'],S['M']
sp,item,exp=struct.unpack('<HHI',G[0:8])
moves=struct.unpack('<4H',A[0:8]); pp=A[8:12]
evs=E[0:6]; contest=E[6:12]
print('species',sp,'item',item,'exp',exp)
print('moves',moves,'pp',list(pp))
print('EVs (hp,atk,def,spe,spa,spd)',list(evs))
print('contest (cool,beauty,cute,smart,tough,feel)',list(contest))
print('EVs as ascii:', bytes(evs))
print('IV word raw:', M[4:8].hex())
# nature from PID
NAT=['Hardy','Lonely','Brave','Adamant','Naughty','Bold','Docile','Relaxed','Impish','Lax','Timid','Hasty','Serious','Jolly','Naive','Modest','Mild','Quiet','Bashful','Rash','Calm','Gentle','Sassy','Careful','Quirky']
print('nature', NAT[pid%25])
# move names for the 4 moves (gen3 move index) - print numbers, we map key ones
print('move ids:', moves)
# all 80 bytes hex
print('raw80', m.hex())
