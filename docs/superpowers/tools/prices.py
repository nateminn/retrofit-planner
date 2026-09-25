"""Energy prices for the tools, read from js/heat-model.js (RP_HEAT.prices).

The site's prices live in one place, the model file. Tools import them from here instead of
keeping their own copies, so a price change is made once. prices_check.py makes sure every
page's own copy agrees with the model too.
"""
import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
_P = json.loads(subprocess.run(
    ['node', '-e', "global.window={};require('./js/heat-model.js');console.log(JSON.stringify(window.RP_HEAT.prices));"],
    capture_output=True, text=True, cwd=ROOT, check=True).stdout)
GAS, ELEC, OIL, LPG, HPT = _P['gas'], _P['electricity'], _P['oil'], _P['lpg'], _P['hpTariff']
