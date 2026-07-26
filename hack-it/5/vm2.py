"""VM with tape-injection at a source index."""
from vm import PROG

def run(inp, inject=None, snap=None, stop_at_hash=True):
    """inject: (src_index, dict cell->value) applied when reaching that op
       snap:   src_index -> returns tape copy at that point (list)"""
    prog=PROG; n=len(prog)
    tape=bytearray(0x60); dp=0; ii=0; pi=0
    snaps=[]
    isrc = inject[0] if inject else -1
    while pi<n:
        op,a,src=prog[pi]
        if src==isrc:
            for c,v in inject[1].items(): tape[c]=v
            isrc=-1
        if snap is not None and src==snap:
            snaps.append(bytes(tape))
        if op==0: dp+=a
        elif op==1: tape[dp]=(tape[dp]+a)&0xff
        elif op==2:
            tape[dp]=inp[ii] if ii<len(inp) else 0; ii+=1
        elif op==3:
            if tape[dp]==0: pi=a
        elif op==4:
            if tape[dp]!=0: pi=a
        elif op==5:
            if stop_at_hash: return (tape[dp], snaps)
        pi+=1
    return (None, snaps)
