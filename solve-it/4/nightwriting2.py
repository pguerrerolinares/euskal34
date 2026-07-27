"""Extractor v2 de las senales de Fail Island.

Modelo: dos tipos de celda conviven en el mismo cartel.
  - celda ANCHA-6: 6 barras de ~6px por columna -> night writing (tally por columna)
  - celda ANCHA-3: 3 barras de ~19px por columna -> braille de 6 puntos (bitmap)
Nivel: <150 = punto marcado, 150..244 = hueco dibujado, >=245 = fondo.
"""
from PIL import Image
import numpy as np, sys, os

HERE=os.path.dirname(os.path.abspath(__file__))
IMG=os.environ.get('SENALES') or next(
    (p for p in (os.path.join(HERE,'imagenes-isla-fail'),
                 os.path.join(HERE,'..','..','solve-it-4','imagenes-isla-fail'))
       if os.path.isdir(p)), os.path.join(HERE,'imagenes-isla-fail'))

def panel(im):
    bg=(im==255)
    ys=np.where(bg.sum(axis=1)>im.shape[1]*0.4)[0]
    xs=np.where(bg.sum(axis=0)>im.shape[0]*0.3)[0]
    return im[ys.min()+8:ys.max()-8, xs.min()+8:xs.max()-8]

def bands(prof, thr, minlen):
    out=[]; cur=None
    for i,v in enumerate(prof):
        if v>thr: cur=[i,i] if cur is None else [cur[0],i]
        else:
            if cur and cur[1]-cur[0]+1>=minlen: out.append(tuple(cur))
            cur=None
    if cur and cur[1]-cur[0]+1>=minlen: out.append(tuple(cur))
    return out

NW={}
for r,row in enumerate([['a','i','o','u','é','è'],['an','in','on','un','eu','ou'],
                        ['b','d','g','j','v','z'],['p','t','q','ch','f','s'],
                        ['l','m','n','r','gn','ll'],['oi','oin','ian','ien','ion','ieu']]):
    for c,s in enumerate(row): NW[(r+1,c+1)]=s

BR={'1':'a','12':'b','14':'c','145':'d','15':'e','124':'f','1245':'g','125':'h',
 '24':'i','245':'j','13':'k','123':'l','134':'m','1345':'n','135':'o','1234':'p',
 '12345':'q','1235':'r','234':'s','2345':'t','136':'u','1236':'v','2456':'w',
 '1346':'x','13456':'y','1356':'z','123456':'é','12356':'à','2346':'è','23456':'ù',
 '16':'â','126':'ê','146':'î','1456':'ô','156':'û','1246':'ë','12456':'ï','1256':'ü',
 '12346':'ç','246':'œ','2':',','23':';','25':':','256':'.','236':'?','235':'!',
 '3':"'",'36':'-','35':'*','26':'(',  '6':'^CAP','45':'^','56':'#','3456':'#N'}

def colruns(P,y0,y1,a,b):
    col=np.array([int(np.median(P[y,a+2:b-1])) for y in range(y0,y1+1)])
    rs=[]; cur=None
    for i,v in enumerate(col):
        t='#' if v<150 else ('o' if v<245 else '.')
        if t=='.':
            if cur: rs.append(cur); cur=None
        elif cur and cur[2]==t: cur=(cur[0],i,t)
        elif cur: rs.append(cur); cur=(i,i,t)
        else: cur=(i,i,t)
    if cur: rs.append(cur)
    return rs

def extract(name):
    P=panel(np.array(Image.open(f'{IMG}/{name}.png').convert('L')).astype(int))
    m=(P<245); prof=m.sum(axis=1)
    rows=[i for i,v in enumerate(prof) if v>0]
    L=[]; cur=[rows[0]]
    for i in rows[1:]:
        if i-cur[-1]>25: L.append((cur[0],cur[-1])); cur=[i]
        else: cur.append(i)
    L.append((cur[0],cur[-1]))
    out=[]
    for y0,y1 in L:
        vb=bands(m[y0:y1+1].sum(axis=0),0,4)
        assert len(vb)%2==0, (name,len(vb))
        cells=[]; prev=None
        for i in range(0,len(vb),2):
            (la,lb),(ra,rb)=vb[i],vb[i+1]
            if prev is not None and la-prev>60: cells.append(None)
            lr=colruns(P,y0,y1,la,lb); rr=colruns(P,y0,y1,ra,rb)
            cells.append((lr,rr)); prev=rb
        out.append(cells)
    return out

def read(cell):
    lr,rr=cell
    n=len(lr)
    if n==6 and len(rr)==6:            # night writing
        li=sum(1 for s,e,t in lr if t=='#'); ri=sum(1 for s,e,t in rr if t=='#')
        cont = all(t=='#' for _,_,t in lr[:li]) and all(t=='#' for _,_,t in rr[:ri])
        return ('nw',(li,ri), NW.get((li,ri),'?'), cont)
    if n==3 and len(rr)==3:            # braille
        dots=''.join(d for d,(s,e,t) in zip('123',lr) if t=='#')+ \
             ''.join(d for d,(s,e,t) in zip('456',rr) if t=='#')
        return ('br',dots, BR.get(dots,'?'), True)
    return ('??',(n,len(rr)),'?',False)

if __name__=='__main__':
  for name in [f'S{i}' for i in range(1,10)]:
      print(f'=== {name}')
      for li,cells in enumerate(extract(name),1):
          pares=[];glosa=[]
          for c in cells:
              if c is None: pares.append('/'); glosa.append(' / '); continue
              k,v,g,ok=read(c)
              pares.append((f'{v[0]}{v[1]}' if k=='nw' else f'[{v}]')+('' if ok else '!'))
              glosa.append(g)
          print(f'  L{li} '+' '.join(pares))
          print(f'     '+''.join(glosa))
