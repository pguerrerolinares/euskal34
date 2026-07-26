import os, sys, itertools, time
from multiprocessing import Pool
from vm import PROG, SRC2PI

SPLIT = 103443   # src index of the 5th ','  (state here is constant)
CHK   = 197901   # end of char blocks, before final compare chain
TARGET = [1,0,1,1,1,0,0,1,0,0,1,1,0,1,1,1,1,0,1,1,1,0,1,0,0,1,1,0,1,1,0,1]

PI_SPLIT = SRC2PI[SPLIT]
PI_CHK   = SRC2PI[CHK]

def _core(prog, tape, dp, ii, pi, inp, stop_pi):
    n=len(prog)
    while pi < stop_pi:
        op,a,src=prog[pi]
        if op==0: dp+=a
        elif op==1: tape[dp]=(tape[dp]+a)&0xff
        elif op==2:
            tape[dp]=inp[ii] if ii<len(inp) else 0; ii+=1
        elif op==3:
            if tape[dp]==0: pi=a
        elif op==4:
            if tape[dp]!=0: pi=a
        pi+=1
    return tape, dp, ii

def snapshot():
    tape=bytearray(0x60)
    t,dp,ii=_core(PROG, tape, 0, 0, 0, b'AAAA'+b'A'*4, PI_SPLIT)
    return bytes(t), dp, ii

SNAP=None
def init():
    global SNAP
    SNAP=snapshot()

# ---------- second half: chars 4..7 -> c0..c31 == TARGET ----------
def half2(prefix):
    snap_t,snap_dp,snap_ii=SNAP
    res=[]
    for b,c,d in itertools.product(range(65,91),repeat=3):
        inp=bytes([65,65,65,65,prefix,b,c,d])
        tape=bytearray(snap_t)
        t,_,_=_core(PROG, tape, snap_dp, 4, PI_SPLIT, inp, PI_CHK)
        if all((1 if t[i] else 0)==TARGET[i] for i in range(32)):
            res.append(inp[4:].decode())
    return res

# ---------- first half: chars 0..3 -> c44 != 0 ----------
def half1(prefix):
    res=[]
    for b,c,d in itertools.product(range(65,91),repeat=3):
        inp=bytes([prefix,b,c,d,65,65,65,65])
        tape=bytearray(0x60)
        t,_,_=_core(PROG, tape, 0, 0, 0, inp, PI_SPLIT)
        if t[44]:
            res.append(inp[:4].decode())
    return res

if __name__=='__main__':
    which=sys.argv[1]
    init()
    t0=time.time()
    fn = half2 if which=='2' else half1
    with Pool(8, initializer=init) as p:
        out=[]
        for i,r in enumerate(p.imap(fn, range(65,91))):
            out+=r
            print(f"  {chr(65+i)} done ({round(time.time()-t0)}s) hits so far {len(out)}", flush=True)
    print("HITS:", out)
