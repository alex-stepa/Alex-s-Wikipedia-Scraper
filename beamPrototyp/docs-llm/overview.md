# Přehled projektu beamPrototyp

## Co projekt dělá

Simuluje chování měkkého tělesa (soft body) — kulového objektu tvořeného sítí uzlů propojených pružinami (beamy) s vnitřním tlakem. Těleso se deformuje, odráží od podlahy, a lze ho uchopit myší.

## Dvě implementace

### 1. MuJoCo (`main.py`)
Využívá fyzikální engine MuJoCo od DeepMind. Model tělesa je definovaný v XML jako `composite` typ `ellipsoid` — 5×5×5 uzlů s tendony a klouby. MuJoCo řeší fyziku automaticky pomocí `implicitfast` integrátoru.

**Výhody:** Realistická fyzika, interaktivní viewer, rychlé spuštění.
**Nevýhody:** Méně kontroly nad přesnou implementací fyziky.

### 2. Vlastní Cython engine (`physics.pyx`)
Ruční implementace tří fyzikálních jevů:
- **Beam síly** — Hookeův zákon + viskózní tlumení na každém beamu.
- **Tlak** — izotropní vnitřní tlak přes povrchové trojúhelníky (divergenční věta).
- **Kolize** — jednoduché AABB kolize s podlahou a stěnami.

**Výhody:** Plná kontrola, možnost experimentovat s fyzikálními parametry.
**Nevýhody:** Nutno kompilovat, ručně nastavovat parametry stability.

## Architektura dat

```
Sphere mesh
    │
    ├── uzly (pos, vel)      — N × 3 float64 arrays
    └── topologie (faces)    ──► beamy (beams, rests)
                                    │
                                    ▼
                               step() smyčka
                               ├── beam síly
                               ├── tlak
                               ├── integrace
                               └── kolize
```

## Technologický stack

- **Python 3.12 / 3.14**
- **MuJoCo** (Google DeepMind) — fyzikální engine + viewer
- **Cython** — C-level optimalizace Python kódu
- **NumPy** — vektorové operace, datové struktury

## Stav projektu

Prototyp / proof-of-concept. Kód je minimální a přímočarý — žádná konfigurace, žádné testy, žádné CLI argumenty.
