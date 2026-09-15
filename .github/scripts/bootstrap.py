from pathlib import Path
import json

app_py = Path("app.py")
original = app_py.read_text()
patch = '''# Homey SHS uses strict JSON parsing, while ESPHome can expose NaN/Infinity
# for climate values before the first valid measurement. Never pass non-finite
# floats to Homey's capability IPC. The runner can evaluate app.py more than
# once, so this patch must be idempotent and capture its delegate by value.
import math
from typing import Any

from homey_esphomedriver.entities.state.base import AbstractEntityStateUpdateHandler

if not getattr(
    AbstractEntityStateUpdateHandler.set_capability_value,
    "_io_esphome_nonfinite_guard",
    False,
):
    _set_capability_value = AbstractEntityStateUpdateHandler.set_capability_value

    def _safe_set_capability_value(
        self,
        capability_id: str,
        value: Any,
        _delegate=_set_capability_value,
    ) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            self.debug(
                f"Ignoring non-finite ESPHome value for {capability_id}: {value!r}"
            )
            return
        _delegate(self, capability_id, value)

    _safe_set_capability_value._io_esphome_nonfinite_guard = True
    AbstractEntityStateUpdateHandler.set_capability_value = _safe_set_capability_value

'''

if "Ignoring non-finite ESPHome value" not in original:
    app_py.write_text(patch + original)

for manifest_path in (Path(".homeycompose/app.json"), Path("app.json")):
    if not manifest_path.exists():
        continue
    data = json.loads(manifest_path.read_text())
    data["version"] = "0.4.4"
    data["source"] = "https://github.com/vsebastiaan/esphome-homey-hotfix"
    data["bugs"] = {"url": "https://github.com/vsebastiaan/esphome-homey-hotfix/issues"}
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

Path("HOTFIX.md").write_text(
    """# Homey ESPHome climate non-finite value hotfix

This tree is based on `Doekse/esphome-homey`.

## Why

ESPHome climate entities may report `NaN` before a first valid temperature or humidity measurement. Homey SHS transports app capability values through strict JSON and crashes when the app emits literal `NaN`.

## Fix

`app.py` guards the shared ESPHome state capability writer and drops all non-finite floats (`NaN`, `Infinity`, `-Infinity`) before they enter Homey IPC. Finite values are passed through unchanged. The guard is idempotent because the Homey Python runner can evaluate `app.py` more than once; its original delegate is captured by value, preventing recursive self-wrapping.

The app id remains `io.esphome`, so a development install upgrades/replaces the existing app in place. Version is bumped to `0.4.4` for this hotfix.
"""
)
