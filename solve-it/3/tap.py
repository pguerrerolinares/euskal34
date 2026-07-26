import asyncio, sys, time
import websockets

URL = "ws://hackit.party.eus:7826/ws"

async def main():
    taps = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
    hdrs = {"Origin": "http://hackit.party.eus:7826"}
    async with websockets.connect(URL, max_size=None, additional_headers=hdrs) as ws:
        buf = []
        start = time.time()
        sent = 0
        async def reader():
            try:
                while True:
                    msg = await ws.recv()
                    if isinstance(msg, bytes):
                        buf.append("[BYTES] " + repr(msg))
                    else:
                        buf.append(msg)
                    sys.stderr.write(msg if isinstance(msg,str) else repr(msg))
                    sys.stderr.flush()
            except Exception as e:
                buf.append(f"\n[reader end: {e}]")
        rt = asyncio.create_task(reader())
        # send taps spaced out
        for i in range(taps):
            await asyncio.sleep(0.4)
            await ws.send(" ")
            sent += 1
        # wait remaining
        while time.time() - start < duration:
            await asyncio.sleep(0.2)
        rt.cancel()
        out = "".join(buf)
        with open("stream_dump.txt","w") as f:
            f.write(out)
        sys.stderr.write(f"\n\n=== sent {sent} taps, dump {len(out)} chars ===\n")

asyncio.run(main())
