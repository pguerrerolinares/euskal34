import asyncio, sys, re
import websockets

URL="ws://hackit.party.eus:7826/ws"
HDRS={"Origin":"http://hackit.party.eus:7826"}

PAIRS = [
 ("You fight like a dairy farmer.", "How appropriate. You fight like a cow."),
 ("This is the END for you, you gutter-crawling cur!", "And I've got a little TIP for you. Get the POINT?"),
 ("Soon you'll be wearing my sword like a shish kebab!", "First you'd better stop waving it like a feather-duster."),
 ("People fall at my feet when they see me coming.", "Even BEFORE they smell your breath?"),
 ("I once owned a dog that was smarter than you.", "He must have taught everything you know."),
 ("Nobody's ever drawn blood from me and nobody ever will.", "You run THAT fast?"),
 ("You make me want to puke.", "You make me think somebody already did."),
 ("My handkerchief will wipe up your blood!", "So you got that job as janitor, after all."),
 ("I got this scar on my face during a mighty struggle!", "I hope now you've learned to stop picking your nose."),
 ("I've spoken with apes more polite than you.", "I'm glad to hear you attended your family reunion."),
 ("Have you stopped wearing diapers yet?", "Why, did you want to borrow one?"),
 ("There are no words for how disgusting you are.", "Yes there are. You just never learned them."),
 ("You're no match for my brains, you poor fool.", "I'd be in real trouble if you ever used them."),
 ("I'm not going to take your insolence sitting down!", "Your hemorrhoids are flaring up again, eh?"),
 ("I've heard you were a contemptible sneak.", "Too bad no one's ever heard of YOU at all."),
 ("You have the manners of a beggar.", "I wanted to make sure you'd feel comfortable with me."),
 # Sword Master
 ("I will milk every drop of blood from your body!", "How appropriate. You fight like a cow."),
 ("I've got a long, sharp lesson for you to learn today.", "And I've got a little TIP for you. Get the POINT?"),
 ("My tongue is sharper than any sword!", "First you'd better stop waving it like a feather-duster."),
 ("My wisest enemies run away at the first sight of me!", "Even BEFORE they smell your breath?"),
 ("Only once I have met such a coward!", "He must have taught everything you know."),
 ("No one will ever catch ME fighting as badly as you do.", "You run THAT fast?"),
 ("If your brother is like you, better to marry a pig.", "You make me think somebody already did."),
 ("My name is feared in every dirty corner of this island!", "So you got that job as janitor, after all."),
 ("My last fight ended with my hands covered with blood.", "I hope now you've learned to stop picking your nose."),
 ("Now I know what filth and stupidity really are.", "I'm glad to hear you attended your family reunion."),
 ("I hope you have a boat ready for a quick escape.", "Why, did you want to borrow one?"),
 ("There are no clever moves that can help you now.", "Yes there are. You just never learned them."),
 ("I've got the courage and skill of a master swordsman!", "I'd be in real trouble if you ever used them."),
 ("You are a pain in the backside, sir!", "Your hemorrhoids are flaring up again, eh?"),
 ("My sword is famous all over the Caribbean!", "Too bad no one's ever heard of YOU at all."),
]

def norm(s):
    s=s.strip().lower()
    s=re.sub(r"[^a-z0-9 ]","",s)
    s=re.sub(r"\s+"," ",s)
    return s

LOOKUP={norm(i):r for i,r in PAIRS}

async def drain(ws,t):
    out=''
    end=asyncio.get_event_loop().time()+t
    while asyncio.get_event_loop().time()<end:
        try: out+=await asyncio.wait_for(ws.recv(),timeout=t)
        except asyncio.TimeoutError: break
        except Exception: break
    return out

def get_insult(text):
    lines=[l.strip() for l in text.replace('\r','').split('\n') if l.strip() and 'HAL terminal' not in l and l.strip()!='>']
    return lines[-1] if lines else None

async def main():
    async with websockets.connect(URL,additional_headers=HDRS,max_size=None) as ws:
        b=await drain(ws,1.5)
        print('BANNER:',repr(b))
        insult=get_insult(b)
        print('INSULT:',insult)
        resp=LOOKUP.get(norm(insult))
        print('LOOKUP RESP:',repr(resp))
        if not resp:
            print('NO MATCH in lookup'); return
        await ws.send(resp+'\n')
        r=await drain(ws,4.0)
        print('AFTER CORRECT:',repr(r))
        # keep listening in case of multi-round
        r2=await drain(ws,3.0)
        print('MORE:',repr(r2))

asyncio.run(main())
