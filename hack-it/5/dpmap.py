"""Static dp resolution: assumes every [..] body is net-zero displacement."""
import os, pickle, sys
D=os.path.dirname(os.path.abspath(__file__))
bf=open(os.path.join(D,'prog.bf')).read()
n=len(bf)

def build():
    dp=0
    dpat=[0]*n
    stack=[]
    bad=[]
    for i,c in enumerate(bf):
        dpat[i]=dp
        if c=='>': dp+=1
        elif c=='<': dp-=1
        elif c=='[': stack.append((i,dp))
        elif c==']':
            j,d0=stack.pop()
            if d0!=dp: bad.append((j,i,d0,dp))
    return dpat,bad,dp

if __name__=='__main__':
    dpat,bad,fin=build()
    print("final dp",fin,"unbalanced loops:",len(bad))
    for b in bad[:20]: print(b)
    print("dp range", min(dpat), max(dpat))
    pickle.dump(dpat, open(os.path.join(D,'dpat.pkl'),'wb'))
