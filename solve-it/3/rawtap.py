import asyncio,websockets,time
async def m():
    async with websockets.connect('ws://hackit.party.eus:7826/ws',additional_headers={'Origin':'http://hackit.party.eus:7826'}) as ws:
        t0=time.time()
        async def rd():
            try:
                while True:
                    x=await ws.recv()
                    typ='B' if isinstance(x,bytes) else 'T'
                    print(f'{time.time()-t0:6.2f} [{typ}] {x!r}',flush=True)
            except Exception as e: print('rd end',e,flush=True)
        rt=asyncio.create_task(rd()); await asyncio.sleep(1.3)
        for i in range(25):
            await ws.send(' ')
            await asyncio.sleep(2.0)
        await asyncio.sleep(2); rt.cancel()
        print('END',flush=True)
asyncio.run(m())
