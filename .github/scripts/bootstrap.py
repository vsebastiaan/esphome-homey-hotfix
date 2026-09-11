from pathlib import Path
import json

app_py = Path("app.py")
original = app_py.read_text()
patch = '''# Temporary safety shim: Homey SHS uses strict JSON parsing, while ESPHome can
# expose NaN/Infinity for climate values before the first valid measurement.
# Never pass non-finite floats to Homey's capability IPC.
import math
from typing import Any

from homey_esphomedriver.entities.state.base import AbstractEntityStateUpdateHandler

_original_set_capability_value = AbstractEntityStateUpdateHandler.set_capability_value


def _safe_set_capability_value(self, capability_id: str, value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        self.debug(f"Ignoring non-finite ESPHome value for {capability_id}: {value!r}")
        return
    _original_set_capability_value(self, capability_id, value)


AbstractEntityStateUpdateHandler.set_capability_value = _safe_set_capability_value

'''

if "Ignoring non-finite ESPHome value" not in original:
    app_py.write_text(patch + original)

for manifest_path in (Path(".homeycompose/app.json"), Path("app.json")):
    if not manifest_path.exists():
        continue
    data = json.loads(manifest_path.read_text())
    data["version"] = "0.4.3"
    data["source"] = "https://github.com/vsebastiaan/esphome-homey-hotfix"
    data["bugs"] = {"url": "https://github.com/vsebastiaan/esphome-homey-hotfix/issues"}
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

Path("HOTFIX.md").write_text(
    """# Homey ESPHome climate non-finite value hotfix

This tree is based on `Doekse/esphome-homey`.

## Why

ESPHome climate entities may report `NaN` before a first valid temperature or humidity measurement. Homey SHS transports app capability values through strict JSON and crashes when the app emits literal `NaN`.

## Temporary fix

`app.py` guards the shared ESPHome state capability writer and drops all non-finite floats (`NaN`, `Infinity`, `-Infinity`) before they enter Homey IPC. Finite values are passed through unchanged.

The app id remains `io.esphome`, so a development install upgrades/replaces the existing app in place. Version is bumped to `0.4.3` for this hotfix.
"""
)
