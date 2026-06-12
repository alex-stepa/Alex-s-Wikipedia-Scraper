# physics.pyx — Vlastní Cython fyzikální engine

## Účel

Cython modul implementující soft-body fyziku od základu: generování sítě, beam/spring síly, tlakové síly a detekci kolizí. Navržen pro výkon — kritické části jsou staticky typovány.

## Funkce

### `build_sphere(num_lat, num_lon, R, cx, cy, cz)` — řádky 8–49

Generuje kulovou síť (mesh) parametricky.

**Parametry:**
- `num_lat` — počet zeměpisných šířkových pásů
- `num_lon` — počet podélníků (segmentů po obvodu)
- `R` — poloměr koule
- `cx, cy, cz` — střed koule

**Vrací:** `(pts: ndarray[N,3], faces: list[tuple])`

**Topologie:**
- Severní pól: index 0 (`cy - R`)
- Vnitřní uzly: řady `lat × num_lon` uzlů
- Jižní pól: index `N-1` (`cy + R`)
- Stěny: trojúhelníky (čepičky na pólech, čtyřúhelníky rozdělené na 2 trojúhelníky uprostřed)

---

### `build_beams(pos, faces)` — řádky 52–67

Ze seznamu trojúhelníkových stěn sestaví seznam unikátních hran (beamů) a jejich klidové délky.

**Parametry:**
- `pos` — pozice uzlů `ndarray[N,3]`
- `faces` — seznam trojúhelníků `list[tuple(int,int,int)]`

**Vrací:** `(beams: ndarray[M,2], rests: ndarray[M])`

**Logika:** Pro každý trojúhelník přidá 3 hrany i diagonály do množiny (deduplication přes `min/max` pořadí). Klidová délka = euklidovská vzdálenost v klidové poloze.

---

### `step(...)` — řádky 70–222

Hlavní fyzikální smyčka. Provede `substeps` pod-kroků s časovým krokem `dt/substeps`.

**Fáze každého pod-kroku:**

#### 1. Gravitace (řádek 106)
```
f[:, 1] += gravity   # Y osa = vertikála
```

#### 2. Beam síly (řádky 109–135)
Hookeův zákon + viskózní tlumení:
```
stretch = L - L0
dv      = dot(vel_diff, normal)
force   = stiff × stretch + damp × dv
```
Síla je ořezána na **±6000 N** — ochrana před numerickou explozí.
Síla působí podél normály beamu, opačně na oba uzly.

#### 3. Tlakové síly (řádky 138–183)

**Výpočet objemu** (divergenční věta, skalární trojný součin):
```
vol = |Σ (p0·(p1×p2))| / 6
vol = max(vol, rest_vol × 0.15)   # zabraňuje kolapsu
```

**Tlak** (Boyle — izotermická komprese):
```
P = pressure × rest_vol / vol
P = min(P, pressure × 5.0)
```

**Aplikace na stěny:**
Pro každý trojúhelník: výpočet normály, ověření orientace (dot test), přidání `P × area/3` každému uzlu trojúhelníku.

#### 4. Integrace pohybu (řádky 186–194)
Explicitní Euler (symplektický — nejdřív rychlost, pak pozice):
```
vel += f × sub_dt
pos += vel × sub_dt
```
Uzel `drag_idx` je přeskočen (ovládán ručně).

#### 5. Drag (řádky 197–203)
Ovládaný uzel se přitahuje k cílové pozici:
```
pos[drag_idx] += (drag_target - pos[drag_idx]) × 0.3
vel[drag_idx]  = 0
```

#### 6. Kolize (řádky 206–221)
- **Podlaha** (`pos[i,1] > floor_y`): odraz Y s koef. `-0.4`, tření XZ `0.78`.
- **Stěny X** (`pos[i,0] < -400` nebo `> 400`): odraz X s koef. `-0.5`.

## Výkonnostní poznámky

- Všechny vnitřní smyčky (`for i in range(N)`, `for i in range(M)`) jsou v C díky `cdef`.
- Hlavní bottleneck: smyčka přes `faces` pro tlak — O(F) na každý pod-krok.
- Pro velké sítě (N > 1000) zvažuj vektorizaci tlakové části přes NumPy.

## Typické hodnoty parametrů

| Parametr | Typická hodnota | Efekt při zvýšení |
|----------|-----------------|-------------------|
| `stiff` | 200–2000 | Tužší těleso |
| `damp` | 0.5–5 | Méně oscilací |
| `pressure` | 50–500 | Nafukovací balón |
| `substeps` | 4–20 | Lepší stabilita, pomalejší |
| `dt` | 1/60 | Kratší krok = stabilnější |
