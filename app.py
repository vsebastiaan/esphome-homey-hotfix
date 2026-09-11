# Temporary safety shim: Homey SHS uses strict JSON parsing, while ESPHome can
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

from homey.app import App

homey_export = App
