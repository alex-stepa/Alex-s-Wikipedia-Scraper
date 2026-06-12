import mujoco
import mujoco.viewer
import numpy as np

XML = """
<mujoco model="softball">
  <option gravity="0 0 -9.81" integrator="implicitfast"/>

  <visual>
    <global offwidth="1280" offheight="720"/>
  </visual>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.1 0.1 0.15" rgb2="0.2 0.2 0.3" width="512" height="512"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.3 0.3 0.35" rgb2="0.2 0.2 0.25" width="512" height="512"/>
    <material name="grid" texture="grid" texrepeat="4 4" reflectance="0.1"/>
  </asset>

  <worldbody>
    <geom name="floor" type="plane" size="5 5 0.1" material="grid" condim="3" friction="0.8 0.005 0.0001"/>

    <geom type="box" pos=" 5 0 2" size="0.1 5 2" rgba="0.4 0.4 0.5 0.3"/>
    <geom type="box" pos="-5 0 2" size="0.1 5 2" rgba="0.4 0.4 0.5 0.3"/>
    <geom type="box" pos="0  5 2" size="5 0.1 2" rgba="0.4 0.4 0.5 0.3"/>
    <geom type="box" pos="0 -5 2" size="5 0.1 2" rgba="0.4 0.4 0.5 0.3"/>

    <flexcomp name="cube" type="box" count="5 5 5"
              spacing="0.09 0.09 0.09" pos="0 0 2.5" dim="3"
              rgba="0.9 0.4 0.2 0.9" mass="1">
      <contact condim="3" selfcollide="narrow" internal="true" friction="0.5"/>
    </flexcomp>
  </worldbody>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(XML)
data = mujoco.MjData(model)

print("Soft body ball - MuJoCo")
print("Ovladani v okne:")
print("  Leve tlacitko mysi  = rotace kamery")
print("  Prave tlacitko mysi = zoom")
print("  Scroll              = pohyb")
print("  Dvojklik na teleso  = sledovani")
print("  Ctrl+klik           = sila na teleso")
print("  [Space]             = pauza")
print("  [Backspace]         = reset")

try:
    ctx = mujoco.viewer.launch_passive(model, data)
except RuntimeError as e:
    if "mjpython" in str(e):
        print("\nChyba: na macOS spust skript pomoci:")
        print("  mjpython main.py\n")
    raise

with ctx as viewer:
    viewer.cam.distance = 6.0
    viewer.cam.elevation = -25
    viewer.cam.azimuth = 135

    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
