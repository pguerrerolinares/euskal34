import asyncio,websockets,time,sys
async def m():
    async with websockets.connect('ws://hackit.party.eus:7826/ws',additional_headers={'Origin':'http://hackit.party.eus:7826'}) as ws:
        t0=time.time(); got=[]
        async def rd():
            try:
                while True:
                    x=await ws.recv(); got.append(x)
                    print(f'{time.time()-t0:6.2f} {x!r}',flush=True)
            except: pass
        rt=asyncio.create_task(rd())
        await asyncio.sleep(1.2)
        n=int(sys.argv[1]) if len(sys.argv)>1 else 120
        gap=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
        for i in range(n):
            await ws.send(' ')
            await asyncio.sleep(gap)
        await asyncio.sleep(3); rt.cancel()
        body=''.join(v for v in got if 'HAL' not in v)
        print('=== BODYJOIN ===',flush=True); print(repr(body),flush=True)
        open('slowtap_out.txt','w').write(''.join(got))
asyncio.run(m())
