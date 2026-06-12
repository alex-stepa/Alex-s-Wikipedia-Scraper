# main.py — MuJoCo simulace

## Účel

Spustitelný skript, který vytvoří soft-body míč pomocí MuJoCo a spustí interaktivní simulaci.

## MuJoCo XML model (`main.py:5–36`)

### Nastavení světa

```xml
<option gravity="0 0 -9.81" integrator="implicitfast"/>
```
- Gravitace podél osy -Z (MuJoCo konvence: Z = nahoru).
- `implicitfast` integrátor — lepší stabilita při tuhých systémech než explicitní Euler.

### Geometrie scény

| Element | Popis |
|---------|-------|
| `floor` | Rovina s třením (friction="0.8 0.005 0.0001") |
| 4× `box` | Průhledné stěny arény 10×10×4 m |

### Míč — composite ellipsoid

```xml
<composite type="ellipsoid" count="5 5 5" spacing="0.09" offset="0 0 2.5">
  <skin material="ball" inflate="0.01" subgrid="2" rgba="0.2 0.5 0.9 0.9"/>
  <geom size="0.04" rgba="0.1 0.3 0.7 0.5"/>
  <joint kind="main" damping="0.5"/>
  <tendon kind="main" stiffness="400" damping="2"/>
</composite>
```

- **5×5×5 uzlů** uspořádaných v elipsoidní mřížce, rozestup 9 cm.
- **skin** — vizuální obal (modrý, průhledný).
- **joint** s tlumením 0.5 — relativní pohyb mezi uzly.
- **tendon** se tuhostí 400 a tlumením 2 — pružinové spojení uzlů.
- Počáteční výška 2.5 m (offset Z).

## Inicializace a smyčka (`main.py:38–58`)

```python
model = mujoco.MjModel.from_xml_string(XML)  # sestaví model z XML
data  = mujoco.MjData(model)                 # alokuje stavové proměnné

with mujoco.viewer.launch_passive(model, data) as viewer:
    viewer.cam.distance  = 6.0   # vzdálenost kamery
    viewer.cam.elevation = -25   # úhel pohledu dolů
    viewer.cam.azimuth   = 135   # rotace kamery

    while viewer.is_running():
        mujoco.mj_step(model, data)  # jeden krok fyziky
        viewer.sync()                # překresli viewer
```

`launch_passive` — viewer neblokuje hlavní vlákno; simulace běží co nejrychleji.

## Ovládání (tištěno při startu)

| Akce | Klávesa/myš |
|------|------------|
| Rotace kamery | Levé tlačítko myši |
| Zoom | Pravé tlačítko myši |
| Pohyb | Scroll |
| Sledování tělesa | Dvojklik na těleso |
| Aplikovat sílu | Ctrl + klik |
| Pauza/spuštění | Space |
| Reset | Backspace |

## Ladění parametrů

Změna tuhosti míče: upravit `stiffness` v tendonu.
Změna odpružení: upravit `damping` v jointu/tendonu.
Větší/menší míč: změnit `count`, `spacing`, nebo `size` geomů.
