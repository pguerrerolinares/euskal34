#!/usr/bin/env python3
"""Figura propia para el writeup de Solve It 2 «Lost Fest» (EE34).

Genera figura_geoglifos_light.png y figura_geoglifos_dark.png:
  - banda superior: 7 geoglifos (uno por pais, orden alfabetico ES) sobre
    silueta del pais; vertices numerados en orden cronologico, flechas de
    direccion, inicio marcado; debajo, la letra/digito que se lee.
  - inset en Japon: poligono original (8 bandas) vs corregido (5, cerrado).
  - banda inferior: tabla dia -> bandas -> pais -> glifo -> letra + control EN.

Ni un pixel del cartel original: solo datos (ciudades, orden, paises).

DEPENDENCIA EXTERNA: las siluetas de los paises salen de world.geo.json, que no
se incluye aqui por no ser nuestro. Es de dominio publico y se baja con:

    curl -sLO https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json
    mv countries.geo.json world.geo.json

Paleta: instancia de referencia del skill dataviz, validada (2 series PASS
light y dark con validate_palette.js).
"""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD_PATH = f'{HERE}/world.geo.json'
if not os.path.exists(_WORLD_PATH):
    sys.exit(
        'Falta world.geo.json (siluetas de paises, no se redistribuye aqui).\n'
        'Bajalo con:\n'
        '  curl -sLO https://raw.githubusercontent.com/johan/world.geo.json/'
        'master/countries.geo.json\n'
        f'  mv countries.geo.json {_WORLD_PATH}'
    )
WORLD = json.load(open(_WORLD_PATH))

# ---------------------------------------------------------------- paletas
PAL = {
    'light': dict(surface='#fcfcfb', country_fill='#f0efec', country_edge='#c3c2b7',
                  ink='#0b0b0b', ink2='#52514e', muted='#898781',
                  serie='#2a78d6', serie_old='#eb6834', num_ink='#ffffff',
                  grid='#e1e0d9'),
    'dark':  dict(surface='#1a1a19', country_fill='#2c2c2a', country_edge='#383835',
                  ink='#ffffff', ink2='#c3c2b7', muted='#898781',
                  serie='#3987e5', serie_old='#d95926', num_ink='#1a1a19',
                  grid='#2c2c2a'),
}

# ------------------------------------------------- datos (verificados antes)
# (ciudad, lat, lon) en orden cronologico de actuacion; cartel corregido (NEW)
GLIFOS = [  # ya en orden alfabetico ES — el orden ES es la clave del reto
    dict(pais='Australia', dia='MIÉ', letra='C',
         bbox=(112, 154.5, -44.5, -9.5),
         ruta=[('Brisbane', -27.470, 153.026), ('Cairns', -16.920, 145.771),
               ('Broome', -17.955, 122.239), ('Perth', -31.951, 115.860),
               ('Adelaida', -34.929, 138.601), ('Melbourne', -37.814, 144.963),
               ('Sídney', -33.869, 151.209)]),
    dict(pais='Brasil', dia='VIE', letra='4',
         bbox=(-74.2, -34, -34, 5.5),
         ruta=[('Belém', -1.456, -48.504), ('Cuiabá', -15.601, -56.097),
               ('Salvador', -12.977, -38.501), ('Fortaleza', -3.717, -38.543),
               ('Vitória', -20.320, -40.338)]),
    dict(pais='China', dia='MAR', letra='M',
         bbox=(96, 127, 19, 46),   # mitad este: el glifo vive ahi y la costa se reconoce
         ruta=[('Chengdu', 30.573, 104.067), ('Lanzhou', 36.061, 103.834),
               ('Wuhan', 30.593, 114.306), ('Qingdao', 36.067, 120.383),
               ('Shanghái', 31.230, 121.474)]),
    dict(pais='España', dia='DOM', letra='1',
         bbox=(-10, 4.5, 35.5, 44.4),
         ruta=[('Valladolid', 41.652, -4.724), ('Bilbao', 43.263, -2.935),
               ('Madrid', 40.417, -3.703), ('Córdoba', 37.888, -4.779),
               ('Sevilla', 37.389, -5.984), ('Murcia', 37.992, -1.131)]),
    dict(pais='Francia', dia='SÁB', letra='N',
         bbox=(-5.5, 9.8, 41, 51.5),
         ruta=[('Burdeos', 44.838, -0.579), ('Nantes', 47.218, -1.554),
               ('Rennes', 48.117, -1.678), ('Marsella', 43.297, 5.370),
               ('Estrasburgo', 48.573, 7.752)]),
    dict(pais='Japón', dia='JUE', letra='O',
         bbox=(134, 142.5, 32.5, 39.5),  # zoom al glifo; el inset da el pais entero
         ruta=[('Kanazawa', 36.561, 136.656), ('Nagoya', 35.184, 136.906),
               ('Tokio', 35.676, 139.650), ('Nagano', 36.649, 138.181),
               ('Kanazawa', 36.561, 136.656)]),
    dict(pais='México', dia='LUN', letra='S',
         bbox=(-118.5, -85.5, 13.5, 33.5),
         ruta=[('Monterrey', 25.686, -100.316), ('Hermosillo', 29.073, -110.956),
               ('Tijuana', 32.515, -117.038), ('Guadalajara', 20.677, -103.347),
               ('CDMX', 19.433, -99.133), ('Zinacantán', 16.760, -92.708),
               ('Acapulco', 16.853, -99.882)]),
]
GEOJSON_NAME = {'Australia': 'Australia', 'Brasil': 'Brazil', 'China': 'China',
                'España': 'Spain', 'Francia': 'France', 'Japón': 'Japan',
                'México': 'Mexico'}

# jueves original (8 bandas) — solo para el inset de la correccion
JUE_OLD = [('Tokio', 35.676, 139.650), ('Osaka', 34.694, 135.502),
           ('Hiroshima', 34.385, 132.455), ('Kanazawa', 36.561, 136.656),
           ('Jōetsu', 37.148, 138.236), ('Sapporo', 43.062, 141.354),
           ('Sendai', 38.268, 140.870), ('Tokio', 35.676, 139.650)]

# offsets manuales de etiquetas de ciudad (pais, ciudad_idx) -> (dx, dy) puntos
LABEL_OFFSETS = {
    ('Australia', 0): (-56, -3),   # Brisbane, a la izquierda (borde derecho)
    ('Australia', 3): (-10, -15),  # Perth debajo
    ('Australia', 4): (-24, -14),  # Adelaida
    ('Australia', 5): (-8, -15),   # Melbourne
    ('Australia', 6): (-14, -15),  # Sidney debajo
    ('Brasil', 1): (-48, -4),      # Cuiaba, a la izquierda
    ('Brasil', 2): (-56, -6),      # Salvador (borde derecho)
    ('Brasil', 3): (-58, -12),     # Fortaleza debajo-izq (borde derecho)
    ('Brasil', 4): (6, -10),       # Vitoria
    ('China', 0): (-10, -14),      # Chengdu debajo
    ('China', 1): (-12, 9),        # Lanzhou encima
    ('China', 2): (8, -7),         # Wuhan
    ('China', 3): (-4, 9),         # Qingdao
    ('China', 4): (7, -5),         # Shanghai
    ('España', 0): (-62, -3),      # Valladolid, a la izquierda
    ('España', 2): (8, -4),        # Madrid
    ('España', 3): (-6, 9),        # Cordoba encima
    ('España', 4): (-16, -14),     # Sevilla debajo
    ('España', 5): (5, 7),         # Murcia
    ('Francia', 0): (-50, -4),     # Burdeos a la izquierda
    ('Francia', 1): (-42, 0),      # Nantes a la izquierda
    ('Francia', 3): (2, -14),      # Marsella debajo
    ('Francia', 4): (-48, -14),    # Estrasburgo debajo-izq (borde derecho)
    ('Japón', 0): (-10, 9),        # Kanazawa (inicio=fin) encima
    ('Japón', 1): (6, -11),        # Nagoya
    ('Japón', 2): (8, -3),         # Tokio
    ('Japón', 3): (-12, -15),      # Nagano debajo (interior del cuadrilatero)
    ('México', 3): (-72, -3),      # Guadalajara a la izquierda
    ('México', 4): (9, 1),         # CDMX a la derecha
    ('México', 5): (0, 8),         # Zinacantan encima
    ('México', 6): (-54, -8),      # Acapulco a la izquierda
}

TABLA = [  # dia, n bandas, pais, glifo (forma), letra, posicion alfabetica ES
    ('LUN', 7, 'México',    'zigzag',            'S', 7),
    ('MAR', 5, 'China',     'dos picos',         'M', 3),
    ('MIÉ', 7, 'Australia', 'bucle abierto',     'C', 1),
    ('JUE', 5, 'Japón',     'bucle cerrado',     'O', 6),
    ('VIE', 5, 'Brasil',    'cuatro',            '4', 2),
    ('SÁB', 5, 'Francia',   'zigzag vertical',   'N', 5),
    ('DOM', 6, 'España',    'trazo con base',    '1', 4),
]


def rings(name):
    """Anillos exteriores (lon, lat) del pais en el GeoJSON."""
    feat = next(f for f in WORLD['features'] if f['properties']['name'] == name)
    geom = feat['geometry']
    polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
    return [np.array(p[0]) for p in polys]


def draw_country(ax, pais, C):
    for r in rings(GEOJSON_NAME[pais]):
        ax.fill(r[:, 0], r[:, 1], color=C['country_fill'], zorder=1)
        ax.plot(r[:, 0], r[:, 1], color=C['country_edge'], lw=0.7, zorder=2)


def draw_ruta(ax, ruta, C, color, numbered=True, labels=True, pais='',
              lw=2.6, ms=150, num_fs=8.5):
    xs = [lon for _, _, lon in ruta]
    ys = [lat for _, lat, _ in ruta]
    ax.plot(xs, ys, '-', color=color, lw=lw, zorder=4,
            solid_capstyle='round', solid_joinstyle='round')
    # flecha de direccion en el punto medio de cada segmento
    for i in range(len(ruta) - 1):
        mx, my = (xs[i] + xs[i+1]) / 2, (ys[i] + ys[i+1]) / 2
        dx, dy = xs[i+1] - xs[i], ys[i+1] - ys[i]
        ax.annotate('', xy=(mx + dx*0.01, my + dy*0.01), xytext=(mx, my),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=0,
                                    mutation_scale=16), zorder=5)
    # vertices: circulo con numero de orden; inicio con anillo
    seen = {}
    for i, (ciudad, lat, lon) in enumerate(ruta):
        if (lat, lon) in seen:          # cierre del bucle (Kanazawa 2 veces)
            continue
        seen[(lat, lon)] = i
        ring = (i == 0)
        ax.scatter([lon], [lat], s=ms * (1.55 if ring else 1), color=color,
                   zorder=6, edgecolors=C['surface'], linewidths=2.2 if ring else 1.2)
        if numbered:
            ax.text(lon, lat, str(i + 1), color=C['num_ink'], fontsize=num_fs,
                    ha='center', va='center', zorder=7, fontweight='bold')
        if labels:
            dx, dy = LABEL_OFFSETS.get((pais, i), (6, 6))
            ax.annotate(ciudad, (lon, lat), xytext=(dx, dy),
                        textcoords='offset points', fontsize=7.5,
                        color=C['ink2'], zorder=8)


def render(mode):
    C = PAL[mode]
    fig = plt.figure(figsize=(22, 9.0), facecolor=C['surface'])
    gs = fig.add_gridspec(2, 7, height_ratios=[4.0, 3.0],
                          left=0.015, right=0.985, top=0.845, bottom=0.035,
                          wspace=0.06, hspace=0.24)

    fig.text(0.015, 0.955, 'LOST FEST — siete países, siete trazos, una palabra',
             fontsize=21, fontweight='bold', color=C['ink'], ha='left')
    fig.text(0.015, 0.912,
             'Ciudad natal de cada banda, unida en el orden cronológico de actuación de su día. '
             'Los países —deducidos, no impresos— se leen en orden alfabético en castellano.',
             fontsize=12.5, color=C['ink2'], ha='left')

    panels = []
    for k, g in enumerate(GLIFOS):
        ax = fig.add_subplot(gs[0, k], facecolor=C['surface'])
        x0, x1, y0, y1 = g['bbox']
        draw_country(ax, g['pais'], C)
        draw_ruta(ax, g['ruta'], C, C['serie'], pais=g['pais'])
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        ax.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2)))  # lon*cos(lat) vs lat
        ax.set_anchor('N')
        for s in ax.spines.values():
            s.set_color(C['grid']); s.set_linewidth(0.8)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{g['pais']}  ·  {g['dia']}", fontsize=13,
                     color=C['ink'], pad=6, fontweight='bold')
        panels.append(ax)

        if g['pais'] == 'Japón':
            # inset: pais entero, poligono original (naranja) vs corregido (azul)
            axi = ax.inset_axes([0.55, 0.60, 0.43, 0.38], facecolor=C['surface'])
            draw_country(axi, 'Japón', C)
            draw_ruta(axi, JUE_OLD, C, C['serie_old'], numbered=False,
                      labels=False, lw=1.4, ms=14)
            draw_ruta(axi, g['ruta'], C, C['serie'], numbered=False,
                      labels=False, lw=1.4, ms=14)
            axi.set_xlim(128.5, 146.5); axi.set_ylim(30, 46)
            axi.set_aspect(1 / np.cos(np.radians(38)))
            axi.set_xticks([]); axi.set_yticks([])
            for s in axi.spines.values():
                s.set_color(C['grid']); s.set_linewidth(0.8)
            axi.text(0.05, 0.94, 'orig. (8)', transform=axi.transAxes,
                     fontsize=7.5, color=C['serie_old'], va='top', fontweight='bold')
            axi.text(0.05, 0.80, 'corr. (5)', transform=axi.transAxes,
                     fontsize=7.5, color=C['serie'], va='top', fontweight='bold')

    # letras en linea de base comun, bajo el panel mas profundo
    fig.canvas.draw()
    y_letras = min(ax.get_position().y0 for ax in panels) - 0.015
    for ax, g in zip(panels, GLIFOS):
        bb = ax.get_position()
        fig.text((bb.x0 + bb.x1) / 2, y_letras, g['letra'], fontsize=54,
                 fontweight='bold', color=C['serie'], ha='center', va='top')

    # ------------------------------------------------------------- tabla
    axt = fig.add_subplot(gs[1, :], facecolor=C['surface'])
    axt.set_axis_off()
    axt.set_xlim(0, 1); axt.set_ylim(0, 1)
    cols = [('DÍA', 0.03), ('BANDAS', 0.115), ('PAÍS DEDUCIDO', 0.21),
            ('GLIFO', 0.36), ('SE LEE', 0.475), ('ORDEN ALFAB. ES', 0.56)]
    y = 0.96
    for name, x in cols:
        axt.text(x, y, name, fontsize=10.5, color=C['muted'], fontweight='bold')
    axt.plot([0.02, 0.66], [y - 0.075, y - 0.075], color=C['grid'], lw=1)
    for r, (dia, n, pais, glifo, letra, pos) in enumerate(TABLA):
        yy = y - 0.16 - r * 0.115
        axt.text(0.03, yy, dia, fontsize=11.5, color=C['ink2'])
        axt.text(0.115, yy, str(n), fontsize=11.5, color=C['ink2'])
        axt.text(0.21, yy, pais, fontsize=11.5, color=C['ink'], fontweight='bold')
        axt.text(0.36, yy, glifo, fontsize=11.5, color=C['ink2'])
        axt.text(0.475, yy, letra, fontsize=13, color=C['serie'], fontweight='bold')
        axt.text(0.56, yy, f'{pos}º', fontsize=11.5, color=C['ink2'])
    # lectura final + control EN, a la derecha de la tabla
    axr_x = 0.70
    axt.text(axr_x, 0.96, 'LECTURA', fontsize=10.5, color=C['muted'], fontweight='bold')
    axt.plot([axr_x - 0.01, 0.99], [0.885, 0.885], color=C['grid'], lw=1)
    axt.text(axr_x, 0.72, 'Orden alfabético en castellano:', fontsize=11.5, color=C['ink2'])
    axt.text(axr_x, 0.50, 'C · 4 · M · 1 · N · O · S', fontsize=26,
             fontweight='bold', color=C['serie'])
    axt.text(axr_x, 0.30, 'Control — en inglés (Australia, Brazil, China,\n'
                          'France, Japan, Mexico, Spain) saldría CAMNOSI:',
             fontsize=10.5, color=C['ink2'])
    axt.text(axr_x, 0.10, 'el idioma del cartel es parte de la clave.',
             fontsize=10.5, color=C['ink2'], style='italic')
    fig.text(0.985, 0.005,
             'Figura propia (no reproduce el cartel). Datos: ciudades natales públicas de las 40 bandas.',
             fontsize=8.5, color=C['muted'], ha='right')

    out = f'{HERE}/figura_geoglifos_{mode}.png'
    fig.savefig(out, dpi=100, facecolor=C['surface'])
    plt.close(fig)
    print('guardado', out)


if __name__ == '__main__':
    render('light')
    render('dark')
