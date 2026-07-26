import sys, os
D=os.path.dirname(os.path.abspath(__file__))
bf=open(os.path.join(D,'prog.bf')).read()
# precompute bracket matches
stack=[]; match={}
for i,c in enumerate(bf):
    if c=='[':stack.append(i)
    elif c==']':
        j=stack.pop(); match[i]=j; match[j]=i
assert not stack

def run(inp, stop_at_hash=True, max_steps=200_000_000):
    tape=bytearray(0x60)
    dp=0; pc=0; ii=0; steps=0
    n=len(bf)
    while pc<n:
        c=bf[pc]; steps+=1
        if steps>max_steps: return ('TIMEOUT',None,steps)
        if c=='>':
            if dp<=0x50: dp+=1
        elif c=='<':
            if dp!=0: dp-=1
        elif c=='+':
            tape[dp]=(tape[dp]+1)&0xff
        elif c=='-':
            tape[dp]=(tape[dp]-1)&0xff
        elif c==',':
            if ii<8:
                tape[dp]=inp[ii]; ii+=1
            else:
                tape[dp]=0
        elif c=='[':
            if tape[dp]==0: pc=match[pc]
        elif c==']':
            if tape[dp]!=0: pc=match[pc]
        elif c=='#':
            if stop_at_hash:
                return ('HASH', tape[dp], steps)
        pc+=1
    return ('END', None, steps)

if __name__=='__main__':
    import itertools,time
    base=b'A'*8
    t0=time.time()
    r=run(base)
    print("AAAAAAAA ->", r, "cellhex=0x%02x"%(r[1] if r[1] is not None else 0), "time",round(time.time()-t0,2))
    # probe each position independently over A-Z, record hash cell value
    for pos in range(8):
        row=[]
        for ch in range(ord('A'),ord('Z')+1):
            inp=bytearray(base); inp[pos]=ch
            st,val,stp=run(bytes(inp))
            row.append((chr(ch),val))
        # print letters whose val==0x4f
        hits=[c for c,v in row if v==0x4f]
        print(f"pos{pos}: hits(0x4f)={hits}  sample={[(c,None if v is None else hex(v)) for c,v in row[:6]]}")
