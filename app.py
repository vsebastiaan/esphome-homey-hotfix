# Homey SHS uses strict JSON parsing, while ESPHome can expose NaN/Infinity
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

from homey.app import App

homey_export = App
