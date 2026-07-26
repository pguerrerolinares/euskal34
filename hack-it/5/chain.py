"""Extract the tail compare chain: sequence of (cell, required_polarity)."""
import os,sys,pickle
D=os.path.dirname(os.path.abspath(__file__))
bf=open(os.path.join(D,'prog.bf')).read()
dpat=pickle.load(open(os.path.join(D,'dpat.pkl'),'rb'))

def ops(lo,hi):
    i=lo; out=[]
    while i<hi:
        c=bf[i]
        if c in '><':
            st=i
            while i<hi and bf[i] in '><': i+=1
            if dpat[i]!=dpat[st]: out.append(('mv',dpat[i],st,dpat[i]))
        elif c in '+-':
            st=i;k=0
            while i<hi and bf[i] in '+-':
                k+= 1 if bf[i]=='+' else -1
                i+=1
            if k: out.append(('add',k,st,dpat[st]))
        else:
            out.append((c,0,i,dpat[i])); i+=1
    return out

LO=int(sys.argv[1],0) if len(sys.argv)>1 else 150000
HI=206347
O=ops(LO,HI)

# find top-level (depth 0) structures
depth=0
top=[]   # list of (kind, ...) at depth 0
i=0
seq=[]
while i<len(O):
    k,a,src,cell=O[i]
    if k=='[':
        # find matching ] at same depth within O
        d=1;j=i+1
        while d:
            if O[j][0]=='[':d+=1
            elif O[j][0]==']':d-=1
            j+=1
        body=O[i+1:j-1]
        seq.append(('loop',cell,src,body))
        i=j
    else:
        seq.append((k,cell,src,a))
        i+=1

def clearloop(item):
    """is it  while cX: cX-=1 ?"""
    return item[0]=='loop' and len(item[3])==1 and item[3][0][0]=='add' and item[3][0][3]==item[1]

# classify
out=[]
for idx,it in enumerate(seq):
    if it[0]=='loop':
        body=it[3]
        # first non-mv-effect: find cells touched
        touched=[b[3] for b in body if b[0] in ('add','[')]
        out.append((it[2], it[1], sorted(set(touched))))
for src,cell,touched in out:
    print(f"{src:7d}  while c{cell:<3d} touches {touched}")
