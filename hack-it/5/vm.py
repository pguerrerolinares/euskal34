"""Compressed-IR Brainfuck VM for prog.bf, with instrumentation hooks."""
import os, pickle
D=os.path.dirname(os.path.abspath(__file__))
bf=open(os.path.join(D,'prog.bf')).read()
N=len(bf)

# ---- build compressed program ----
# ops: (opcode, arg, srcidx)  opcode: 0=mv 1=add 2=in 3=jz(fwd) 4=jnz(back) 5=hash
_prog=[]
_srcmap=[]
i=0
while i<N:
    c=bf[i]
    if c in '><':
        st=i; k=0
        while i<N and bf[i] in '><':
            k += 1 if bf[i]=='>' else -1
            i+=1
        if k: _prog.append([0,k,st])
    elif c in '+-':
        st=i; k=0
        while i<N and bf[i] in '+-':
            k += 1 if bf[i]=='+' else -1
            i+=1
        k&=0xff
        if k: _prog.append([1,k,st])
    elif c==',':
        _prog.append([2,0,i]); i+=1
    elif c=='[':
        _prog.append([3,0,i]); i+=1
    elif c==']':
        _prog.append([4,0,i]); i+=1
    elif c=='#':
        _prog.append([5,0,i]); i+=1
    else:
        i+=1
# link brackets
st=[]
for pi,op in enumerate(_prog):
    if op[0]==3: st.append(pi)
    elif op[0]==4:
        j=st.pop(); _prog[j][1]=pi; op[1]=j
assert not st
PROG=[tuple(o) for o in _prog]
SRC2PI={o[2]:pi for pi,o in enumerate(PROG)}

def run(inp, patches=None, watch=None, stop_at_hash=True):
    """patches: dict src_index -> replacement list of (opcode,arg) executed instead (only for '[' handled specially)
       watch: dict src_index -> callable(tape,dp) called before executing that op
       returns (status, value, log)"""
    prog=PROG
    n=len(prog)
    tape=bytearray(0x60)
    dp=0; ii=0; pi=0
    log=[]
    while pi<n:
        op,a,src=prog[pi]
        if watch is not None and src in watch:
            log.append((src, watch[src], bytes(tape), dp))
        if op==0: dp+=a
        elif op==1: tape[dp]=(tape[dp]+a)&0xff
        elif op==2:
            tape[dp]=inp[ii] if ii<len(inp) else 0
            ii+=1
        elif op==3:
            if tape[dp]==0: pi=a
        elif op==4:
            if tape[dp]!=0: pi=a
        elif op==5:
            if stop_at_hash: return ('HASH', tape[dp], log, bytes(tape), dp)
        pi+=1
    return ('END', None, log, bytes(tape), dp)

if __name__=='__main__':
    import time
    t0=time.time()
    r=run(b'ABCDEFGH')
    print(r[0], hex(r[1]) if r[1] is not None else None, 'time', round(time.time()-t0,2))
    print('nops', len(PROG))
