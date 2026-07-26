import sys,struct
from capstone import *
b=open(sys.argv[1],'rb').read()
md=Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
md.detail=False
start=int(sys.argv[2],0)
length=int(sys.argv[3],0) if len(sys.argv)>3 else 256
for ins in md.disasm(b[start:start+length], start):
    print(f"{ins.address:06x}: {ins.bytes.hex():<12} {ins.mnemonic}\t{ins.op_str}")
