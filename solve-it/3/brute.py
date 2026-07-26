import asyncio, websockets, time, sys

RESPONSES = [
 "How appropriate. You fight like a cow.",
 "And I've got a little TIP for you. Get the POINT?",
 "First you'd better stop waving it like a feather-duster.",
 "First you'd better stop waving it about like a feather-duster.",
 "Even BEFORE they smell your breath?",
 "He must have taught everything you know.",
 "He must have taught you everything you know.",
 "You run THAT fast?",
 "You make me think somebody already did.",
 "So you got that job as janitor, after all.",
 "I hope now you've learned to stop picking your nose.",
 "I'm glad to hear you attended your family reunion.",
 "Why, did you want to borrow one?",
 "Yes there are. You just never learned them.",
 "I'd be in real trouble if you ever used them.",
 "Your hemorrhoids are flaring up again, eh?",
 "Too bad no one's ever heard of YOU at all.",
 "I wanted to make sure you'd feel comfortable with me.",
]

def variants(r):
    vs=[r]
    base=r.rstrip('.!?')
    for end in ['', '.', '!', '?']:
        vs.append(base+end)
    return list(dict.fromkeys(vs))

ALL=[]
for r in RESPONSES:
    ALL.extend(variants(r))
ALL=list(dict.fromkeys(ALL))

async def drain(ws,t):
    out=''
    end=time.time()+t
    while time.time()<end:
        try: out+=await asyncio.wait_for(ws.recv(),timeout=t)
        except: break
    return out

async def main():
    async with websockets.connect('ws://hackit.party.eus:7826/ws',additional_headers={'Origin':'http://hackit.party.eus:7826'},max_size=None) as ws:
        b=await drain(ws,1.5)
        ins=[l.strip() for l in b.replace('\r','').split('\n') if l.strip() and 'HAL' not in l and l.strip()!='>']
        insult=ins[-1] if ins else '?'
        print('INSULT:',insult,flush=True)
        for r in ALL:
            await ws.send(r+'\n')
            resp=await drain(ws,1.5)
            clean=resp.strip()
            if clean not in ('','?'):
                print(f'*** HIT r={r!r} -> {resp!r}',flush=True)
                more=await drain(ws,3.0)
                print('MORE:',repr(more),flush=True)
                return
            else:
                print(f'  no  {r!r} -> {resp!r}',flush=True)
        print('exhausted, no hit',flush=True)

asyncio.run(main())
