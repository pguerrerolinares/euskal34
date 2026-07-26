import asyncio,websockets,sys,time
async def m():
    async with websockets.connect('ws://hackit.party.eus:7826/ws',additional_headers={'Origin':'http://hackit.party.eus:7826'}) as ws:
        banner=''
        try:
            while True: banner+=await asyncio.wait_for(ws.recv(),timeout=1.0)
        except: pass
        print('BANNER',repr(banner),flush=True)
        out=''
        n=int(sys.argv[1]) if len(sys.argv)>1 else 120
        for i in range(n):
            await ws.send(' ')
            try:
                ch=await asyncio.wait_for(ws.recv(),timeout=2.5)
            except asyncio.TimeoutError:
                print(f'[{i}] TIMEOUT',flush=True); break
            out+=ch
            print(f'[{i}] {ch!r}  sofar={out!r}',flush=True)
        open('synctap_out.txt','w').write(out)
        print('DONE',repr(out),flush=True)
asyncio.run(m())
