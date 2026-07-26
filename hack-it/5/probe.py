import vm, sys, random
CHK=197901   # right after per-char blocks, before scratch clear + compare chain

REQ = {}  # cell -> required (0 = must be zero, 1 = must be nonzero)
for c in [1,5,6,8,9,12,17,21,23,24,27,30]: REQ[c]=0
for c in [0,2,3,4,7,10,11,13,14,15,16,18,19,20,22,25,26,28,29,31,44]: REQ[c]=1

def hashbits(inp):
    r=vm.run(inp, watch={CHK:'chk'})
    for src,tag,tape,dp in r[2]:
        if src==CHK: return tape
    return None

def show(inp):
    t=hashbits(inp)
    bits=[t[i] for i in range(32)]
    return bits, t[44]

if __name__=='__main__':
    for s in [b'AAAAAAAA', b'BAAAAAAA', b'ABAAAAAA', b'ZZZZZZZZ', b'ABCDEFGH']:
        b,c44=show(s)
        print(s.decode(), ''.join('%02x'%x for x in b), 'c44=%02x'%c44)
    print()
    print('REQ    ', ''.join(('1 ' if REQ.get(i)==1 else '0 ') for i in range(32)))
    b,_=show(b'AAAAAAAA')
    print('AAA bits', ''.join(('1' if x else '0') for x in b))
