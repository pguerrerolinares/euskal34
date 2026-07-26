import os
_HERE=os.path.dirname(os.path.abspath(__file__))
data=open(os.path.join(_HERE,'pokemon-esmeralda.sav'),'rb').read()
CH={0x00:' ',0x1B:'e'}
for i,ch in enumerate('0123456789'): CH[0xA1+i]=ch
CH[0xAB]='!';CH[0xAC]='?';CH[0xAD]='.';CH[0xAE]='-';CH[0xB8]=',';CH[0xBA]='/';CH[0xB3]="'";CH[0xB4]="'"
for i,ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): CH[0xBB+i]=ch
for i,ch in enumerate('abcdefghijklmnopqrstuvwxyz'): CH[0xD5+i]=ch
# find runs of >=5 valid non-space Gen3 chars
runs=[]
cur=''; start=0
for i,b in enumerate(data):
    if b in CH:
        if not cur: start=i
        cur+=CH[b]
    else:
        if len(cur.strip())>=5 and any(c.isalpha() for c in cur):
            runs.append((start,cur))
        cur=''
seen=set()
for s,r in runs:
    key=r.strip()
    if key in seen: continue
    seen.add(key)
    print(f'{s:#07x}  {r!r}')
print('total unique runs', len(seen))
