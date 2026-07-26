import struct
import os
_HERE=os.path.dirname(os.path.abspath(__file__))
data=open(os.path.join(_HERE,'pokemon-esmeralda.sav'),'rb').read()
# rebuild slot A PC to get BOX[31]
def sec(base,i): return data[base+i*0x1000:base+i*0x1000+0x1000]
# find sections by id in slot A
secs={}
for i in range(14):
    s=sec(0,i); sid=struct.unpack('<H',s[0xFF4:0xFF6])[0]; secs[sid]=s
pc=b''
for sid in range(5,14): pc+=secs[sid][0:0xF80]
box=pc[4:]
m=box[31*80:31*80+80]
pid,otid=struct.unpack('<II',m[0:8])
key=pid^otid
order=pid%24
ORD=['GAEM','GAME','GEAM','GEMA','GMAE','GMEA','AGEM','AGME','AEGM','AEMG','AMGE','AMEG',
     'EGAM','EGMA','EAGM','EAMG','EMGA','EMAG','MGAE','MGEA','MAGE','MAEG','MEGA','MEAG']
raw=m[32:32+48]
dw=b''.join(struct.pack('<I',struct.unpack('<I',raw[w*4:w*4+4])[0]^key) for w in range(12))
subs={}
for j,c in enumerate(ORD[order]):
    subs[c]=dw[j*12:j*12+12]
G=subs['G']; M=subs['M']; A=subs['A']; E=subs['E']
species,item,exp = struct.unpack('<HHI',G[0:8])
ppbonus,friend = G[8],G[9]
# Misc substructure M: 0 pokerus,1 met location,2-3 origins,4-7 IVs+eggflag+ability,8-11 ribbons
pokerus=M[0]; metloc=M[1]
origins=struct.unpack('<H',M[2:4])[0]
level_met=origins&0x7F
game_origin=(origins>>7)&0xF
ball=(origins>>11)&0xF
ot_gender=(origins>>15)&1
ivword=struct.unpack('<I',M[4:8])[0]
ivs=[(ivword>>(5*k))&0x1F for k in range(6)]
isegg=(ivword>>30)&1
ability=(ivword>>31)&1
ribbons=struct.unpack('<I',M[8:12])[0]
GAMEMAP={0:'?',1:'Sapphire',2:'Ruby',3:'Emerald',4:'FireRed',5:'LeafGreen',15:'Colosseum/XD'}
print('PID  %08x  TID(vis)=%d SID=%d'%(pid, otid&0xFFFF, otid>>16))
print('species',species,'item',item,'exp',exp,'friendship',friend)
print('met location byte:',metloc, hex(metloc))
print('level met:',level_met,'game origin:',game_origin,GAMEMAP.get(game_origin,'?'),'ball:',ball,'otgender:',ot_gender)
print('IVs',ivs,'egg',isegg,'ability',ability)
print('ribbons %08x'%ribbons)
# shininess
tid=otid&0xFFFF; sid=otid>>16
shiny=(tid^sid^ (pid&0xFFFF) ^ (pid>>16)) < 8
print('SHINY?',shiny)
# nickname/OT bytes raw
print('nick bytes',m[8:18].hex(),'OT bytes',m[20:27].hex())
