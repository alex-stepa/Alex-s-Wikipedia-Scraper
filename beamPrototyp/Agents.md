# Agents.md — Průvodce pro AI agenty

## Účel projektu

`beamPrototyp` je fyzikální simulační prototyp měkkého tělesa. Slouží jako základ pro experimentování s beam/spring sítěmi a tlakovými silami. Nejde o produkční aplikaci — jde o výzkumný/vzdělávací kód.

## Kde co najdeš

| Co hledáš | Kde |
|-----------|-----|
| MuJoCo XML model koule | `main.py:5–36` |
| Vstupní bod simulace | `main.py:38–58` |
| Generování kulové sítě | `physics.pyx:8–49` (funkce `build_sphere`) |
| Sestavení beam sítě | `physics.pyx:52–67` (funkce `build_beams`) |
| Hlavní fyzikální smyčka | `physics.pyx:70–222` (funkce `step`) |
| Beam (spring) síly | `physics.pyx:109–135` |
| Výpočet tlaku | `physics.pyx:138–183` |
| Integrace pohybu | `physics.pyx:186–194` |
| Kolize s podlahou/stěnami | `physics.pyx:206–221` |

## Klíčové datové struktury

```
pos       : ndarray[N, 3]  — pozice uzlů (x, y, z) v metrech
vel       : ndarray[N, 3]  — rychlosti uzlů
beams     : ndarray[M, 2]  — indexy párů uzlů tvořících beam
rests     : ndarray[M]     — klidové délky beamů
faces     : list of tuples — trojúhelníkové stěny povrchové sítě
rest_vol  : float          — referenční objem při klidovém stavu
```

## Fyzikální parametry `step()`

| Parametr | Typ | Popis |
|----------|-----|-------|
| `substeps` | int | Počet pod-kroků na snímek (zvyšuje stabilitu) |
| `dt` | float | Časový krok snímku v sekundách |
| `stiff` | float | Tuhosť beamů (N/m) |
| `damp` | float | Tlumení beamů (Ns/m) |
| `pressure` | float | Vnitřní tlak (Pa) |
| `gravity` | float | Gravitace (záporné = dolů, osa Y) |
| `floor_y` | float | Y-souřadnice podlahy |
| `drag_idx` | int | Index uzlu ovládaného myší (-1 = žádný) |
| `drag_target` | ndarray[3] | Cílová pozice pro drag |

## Typické úkoly pro agenta

### Přidat nový tvar tělesa
1. Přidej funkci `build_<shape>` do `physics.pyx` podle vzoru `build_sphere`.
2. Funkce vrací `(pts: ndarray[N,3], faces: list)`.
3. Zavolej `build_beams(pts, faces)` pro vygenerování beam sítě.
4. Předpočítej `rest_vol` pomocí stejného vzorce jako v `step()` (divergenční věta).

### Změnit fyzikální vlastnosti
- Tuhost/tlumení → parametry `stiff`, `damp` ve volání `step()`.
- Větší stabilita → zvyš `substeps`, zmenš `dt`.
- Odraz od podlahy → koeficient `-0.4` na `physics.pyx:211`.
- Tření → koeficient `0.78` na `physics.pyx:212–213`.

### Přepsat na čistý Python (bez Cython)
- Odstraň `cimport numpy`, `ctypedef`, všechny `cdef` deklarace.
- `np.ndarray[F64, ndim=2]` → `np.ndarray`.
- Očekávej 10–50× zpomalení na velkých sítích.

### Integrovat `physics.pyx` do MuJoCo projektu
- Nejde o přímé propojení — jsou to dva nezávislé přístupy.
- MuJoCo (`main.py`) řeší fyziku interně; `physics.pyx` je alternativní engine.

## Co NEDĚLAT

- Neměň osu nahoru mezi moduly bez úpravy kolizní logiky (Y vs Z).
- Neodstraňuj ořez sily ±6000 N bez náhrady — simulace exploduje.
- Nepočítej `rest_vol` uvnitř časové smyčky — je to konstantní reference.
