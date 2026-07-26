import os, sys, pickle
D=os.path.dirname(os.path.abspath(__file__))
bf=open(os.path.join(D,'prog.bf')).read()
dpat=pickle.load(open(os.path.join(D,'dpat.pkl'),'rb'))
n=len(bf)

def ops(lo,hi):
    """yield (kind, arg, idx, cell)"""
    i=lo
    while i<hi:
        c=bf[i]
        if c in '><':
            st=i
            while i<hi and bf[i] in '><': i+=1
            if dpat[i]!=dpat[st]: yield ('mv', dpat[i]-dpat[st], st, dpat[i])
        elif c in '+-':
            st=i; k=0
            while i<hi and bf[i] in '+-':
                k += 1 if bf[i]=='+' else -1
                i+=1
            if k: yield ('add', k, st, dpat[st])
        else:
            yield (c, 0, i, dpat[i]); i+=1

def dump(lo,hi,out=sys.stdout):
    depth=0
    for kind,a,i,cell in ops(lo,hi):
        if kind==']': depth-=1
        pre='  '*depth
        if kind=='mv':   print(f"{i:6d} c{cell:<3d} {pre}>>", file=out)
        elif kind=='add':print(f"{i:6d} c{cell:<3d} {pre}c{cell} {a:+d}", file=out)
        elif kind=='[':  print(f"{i:6d} c{cell:<3d} {pre}while c{cell}:", file=out)
        elif kind==']':  print(f"{i:6d} c{cell:<3d} {pre}endw(c{cell})", file=out)
        else:            print(f"{i:6d} c{cell:<3d} {pre}{kind}  (c{cell})", file=out)
        if kind=='[': depth+=1

if __name__=='__main__':
    dump(int(sys.argv[1],0), int(sys.argv[2],0))
