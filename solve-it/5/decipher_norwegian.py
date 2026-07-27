#!/usr/bin/env python3
"""
Verificador final solve5: elamita lineal -> noruego (modelo abjad).

Tabla cerrada: signo -> (celda Desset, clase fonetica).
Frase objetivo: se comprueba signo a signo que el cifrado de la frase
noruega reconstruida reproduce exactamente los 71 signos del criptograma.
"""

CRYPTO = [[1,2],[3,4],[1,5],[6,7,8,1],[9,3,1,6,10,1,5],[11],[1,2],[12,8,13,6,7],[14,7,2],[15,14,16,2],
     [17],[18,14,1,5],[16,19],[12,8,13,5],[12,6,20,8,15,11,5],[16,19],[1,13,4,7,4],[17,4],[21,5,7,5],
     [22,23],[15,24,5],[9,25,4]]
# La segmentacion de palabra la fija row3.png: 6 glifos en dos grupos de 3, con
# separador simple entre ambos y doble barra de fin de frase al cierre. S22-S23
# ("og") es la ultima palabra de L2; L3 son S15-S24-S05 ("tusen") y S09-S25-S04
# ("huler"). El verificador reproduce los 71 signos igual con cualquier
# agrupacion -- comprueba la lectura, no la segmentacion -- pero la imagen es
# quien manda aqui.

TABLE = {  # signo: (celda elamita Desset, clase, letras noruegas que cubre)
    1:  ('te',  'T', 'd/t'),
    2:  ('ta',  'T', 't/d'),
    3:  ('wi',  'W', 'v'),
    4:  ('ra',  'R', 'r'),
    5:  ('na',  'N', 'n'),
    6:  ('sa',  'S', 's'),
    7:  ('ki',  'K', 'k/g'),
    8:  ('la',  'L', 'l'),
    9:  ('hu',  'H', 'h'),
    10: ('ti',  'T', 't'),
    11: ('i',   'I', 'i'),
    12: ('e',   'E', 'e (y la a de alviske)'),
    13: ('wi2', 'W', 'v'),
    14: ('ri2', 'R', 'r'),
    15: ('tu2', 'T', 'd/t'),
    16: ('a',   'A', 'a'),
    17: ('pu2', 'P', 'p/f (sila "pa" completa en "paa")'),
    18: ('pe',  'P', 'b'),
    19: ('u2',  'U', 'v (grafia latina u~v)'),
    20: ('ka',  'K', 'g'),
    21: ('ku2', 'K', 'k'),
    22: ('u',   'U', 'o'),
    23: ('ka2', 'K', 'g'),
    24: ('si',  'S', 's'),
    25: ('li',  'L', 'l'),
}

# Frase noruega reconstruida, palabra a palabra, con el cifrado esperado:
# cada palabra -> lista de (letra(s) del noruego, signo que las representa)
PHRASE = [
    ("det",         [('d',1),('e',None),('t',2)]),
    ("var",         [('v',3),('a',None),('r',4)]),
    ("den",         [('d',1),('e',None),('n',5)]),
    ("skjulte",     [('s',6),('k',7),('j',None),('u',None),('l',8),('t',1),('e',None)]),
    ("hovedstaden", [('h',9),('o',None),('v',3),('e',None),('d',1),('s',6),('t',10),('a',None),('d',1),('e',None),('n',5)]),
    ("i",           [('i',11)]),
    ("det",         [('d',1),('e',None),('t',2)]),
    ("alviske",     [('a',12),('l',8),('v',13),('i',None),('s',6),('k',7),('e',None)]),
    ("riket",       [('r',14),('i',None),('k',7),('e',None),('t',2)]),
    ("Doriath",     [('d',15),('o',None),('r',14),('i',None),('a',16),('t',2),('h',None)]),
    ("på",          [('på',17)]),
    ("bredden",     [('b',18),('r',14),('e',None),('dd',1),('e',None),('n',5)]),
    ("av",          [('a',16),('v',19)]),
    ("elven",       [('e',12),('l',8),('v',13),('e',None),('n',5)]),
    ("Esgalduin",   [('e',12),('s',6),('g',20),('a',None),('l',8),('d',15),('u',None),('i',11),('n',5)]),
    ("av",          [('a',16),('v',19)]),
    ("dverger",     [('d',1),('v',13),('e',None),('r',4),('g',7),('e',None),('r',4)]),
    ("for",         [('f',17),('o',None),('r',4)]),
    ("kongen",      [('k',21),('o',None),('n',5),('g',7),('e',None),('n',5)]),
    ("og",          [('o',22),('g',23)]),
    ("tusen",       [('t',15),('u',None),('s',24),('e',None),('n',5)]),
    ("huler",       [('h',9),('u',None),('l',25),('e',None),('r',4)]),
]

print(f"{'#':>3} {'criptograma':<28} {'palabra':<14} cifrado letra a letra")
ok_all = True
for wi, (signs, (word, enc)) in enumerate(zip(CRYPTO, PHRASE)):
    produced = [s for _, s in enc if s is not None]
    match = "OK " if produced == signs else "FAIL"
    if produced != signs: ok_all = False
    sig_str = '-'.join(f"S{s:02d}" for s in signs)
    det = ' '.join(f"{l}»S{s:02d}" if s else f"({l})" for l, s in enc)
    print(f"w{wi+1:>2} {sig_str:<28} {word:<14} {det}   [{match}]")

print()
print("TOTAL:", "los 71 signos reproducen el criptograma EXACTAMENTE" if ok_all else "HAY DISCREPANCIAS")
print()
print("Tabla signo -> celda elamita (Desset 2022) -> valor:")
for s in sorted(TABLE):
    c, cl, uso = TABLE[s]
    print(f"  S{s:02d}: {c:<4} clase {cl}  ({uso})")
