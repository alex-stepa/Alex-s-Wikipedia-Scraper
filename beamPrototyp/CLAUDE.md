# beamPrototyp — CLAUDE.md

## Co je tento projekt

Prototyp fyzikální simulace měkkého tělesa (soft-body). Obsahuje dvě oddělené implementace:

1. **MuJoCo pipeline** (`main.py`) — rychlé spuštění pomocí MuJoCo composite ellipsoid s pasivním viewerem.
2. **Vlastní Cython engine** (`physics.pyx`) — ruční implementace beam/spring sítě s tlakovou simulací a detekcí kolizí.

## Struktura

```
beamPrototyp/
├── main.py          # MuJoCo simulace (spustitelný entry-point)
├── physics.pyx      # Cython modul: mesh, síly, integrace
├── docs-llm/        # LLM-friendly dokumentace
│   ├── overview.md
│   ├── main.md
│   └── physics.md
└── CLAUDE.md        # tento soubor
```

## Závislosti

- Python 3.12+ (venv312) nebo 3.14 (venv)
- `mujoco` — pro `main.py`
- `numpy`, `Cython` — pro `physics.pyx`

## Jak spustit

```bash
# MuJoCo demo
source .venv312/bin/activate
python main.py

# Cython modul zkompilovat
cythonize -i physics.pyx
```

## Konvence

- `physics.pyx` používá staticky typované Cython proměnné (`cdef`) pro výkon — nekonvertuj na čistý Python bez důvodu.
- Fyzikální jednotky: pozice v metrech, čas v sekundách, síly v Newtonech.
- Osa Y je nahoru v `physics.pyx`; osa Z je nahoru v MuJoCo (`main.py`) — dej pozor při překladu mezi moduly.

## Důležité invarianty

- `rest_vol` v `step()` musí být předpočítán před simulací; nikdy ho nepočítej uvnitř časové smyčky.
- Síla paprsku je ořezána na ±6000 N (`physics.pyx:128–129`) — ochrana před explozí simulace.
- Tlak je omezen na `5× pressure` — zabraňuje nekontrolovanému nafukování.
