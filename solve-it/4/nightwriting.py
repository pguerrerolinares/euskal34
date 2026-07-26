"""Extractor de las senales de Fail Island (Solve It 4, EE34).

Las senales usan *night writing* (sonografia de Barbier): celda de 6 filas x 2
columnas; el numero de puntos MARCADOS de cada columna da una coordenada sobre
una rejilla 6x6 de sonidos.  Izquierda -> fila, derecha -> columna.

Detalles de render que hay que respetar:
  - tres niveles: <150 punto marcado, 150..244 hueco dibujado, >=245 fondo.
  - cada linea logica se ve como TRES bandas horizontales de dos filas cada una.
  - la primera celda de cada linea es un ORNAMENTO (barras ~3x mas altas),
    no es dato.
"""
from PIL import Image
import numpy as np, glob, os, sys

_HERE=os.path.dirname(os.path.abspath(__file__))

def bands(prof, thr, minlen):
    out=[]; cur=None
    for i,v in enumerate(prof):
        if v>thr:
            cur=[i,i] if cur is None else [cur[0],i]
        else:
            if cur and cur[1]-cur[0]+1>=minlen: out.append(tuple(cur))
            cur=None
    if cur and cur[1]-cur[0]+1>=minlen: out.append(tuple(cur))
    return out

def panel(im):
    bg=(im==255)
    ys=np.where(bg.sum(axis=1)>im.shape[1]*0.4)[0]
    xs=np.where(bg.sum(axis=0)>im.shape[0]*0.3)[0]
    return im[ys.min()+8:ys.max()-8, xs.min()+8:xs.max()-8]

def extract(path):
    P=panel(np.array(Image.open(path).convert('L')).astype(int))
    mark=(P<245)
    hb=bands(mark.sum(axis=1), 2, 10)
    out=[]
    for g in [hb[i:i+3] for i in range(0,len(hb),3)]:
        if len(g)<3: continue
        y0,y1=g[0][0], g[-1][1]
        rows=[a+3 for a,b in g]+[b-3 for a,b in g]; rows.sort()
        vb=bands(mark[y0:y1+1].sum(axis=0), 0, 4)
        cols=[]
        for a,b in vb:
            cx=(a+b)//2
            # conteo POR POSICION sobre las 6 filas; contar "runs" de pixel oscuro
            # infravalora, porque con 5-6 puntos las barras quedan pegadas y se funden
            n=sum(1 for y in rows if int(np.median(P[y-1:y+2, cx-3:cx+4]))<150)
            cols.append({'x0':a,'x1':b,'cx':cx,'n':n})
        line=[]; prev=None
        for i in range(0, len(cols)-1, 2):
            L,R=cols[i],cols[i+1]
            if prev is not None and L['x0']-prev>60: line.append(None)
            line.append((L['n'],R['n'])); prev=R['x1']
        out.append(line)
    return out

T={}
for r,row in enumerate([['a','i','o','u','é','è'],['an','in','on','un','eu','ou'],
                        ['b','d','g','j','v','z'],['p','t','q','ch','f','s'],
                        ['l','m','n','r','gn','ll'],['oi','oin','ian','ien','ion','ieu']]):
    for c,s in enumerate(row): T[(r+1,c+1)]=s

if __name__=='__main__':
    for p in sorted(glob.glob(sys.argv[1] if len(sys.argv)>1
                              else os.path.join(_HERE,'..','..','solve-it-4',
                                                  'imagenes-isla-fail','*.png'))):
        print(os.path.basename(p))
        for j,l in enumerate(extract(p),1):
            pares=' '.join('/' if c is None else f'{c[0]}{c[1]}' for c in l)
            son  =''.join(' / ' if c is None else T.get(c,f'<{c[0]}{c[1]}>') for c in l)
            print(f'  L{j} {pares}')
            print(f'     {son}')
