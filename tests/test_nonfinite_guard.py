"""Regression coverage for the repeatable Homey ESPHome NaN guard."""

from __future__ import annotations

import math
import json
import os
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "app.py"
BOOTSTRAP_PATH = APP_PATH.parent / ".github" / "scripts" / "bootstrap.py"


class NonFiniteGuardTest(unittest.TestCase):
    def test_bootstrap_applies_the_guard_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            (temporary_path / "app.py").write_text(
                "from homey.app import App\n\nhomey_export = App\n"
            )
            compose = temporary_path / ".homeycompose"
            compose.mkdir()
            (compose / "app.json").write_text(
                json.dumps({"id": "io.esphome", "version": "0.4.3"})
            )

            previous_directory = Path.cwd()
            try:
                os.chdir(temporary_path)
                runpy.run_path(str(BOOTSTRAP_PATH))
                once = (temporary_path / "app.py").read_text()
                runpy.run_path(str(BOOTSTRAP_PATH))
                twice = (temporary_path / "app.py").read_text()
            finally:
                os.chdir(previous_directory)

            self.assertEqual(twice, once)
            self.assertEqual(
                json.loads((compose / "app.json").read_text())["version"], "0.4.4"
            )

    def test_repeated_app_evaluation_is_idempotent(self) -> None:
        forwarded: list[tuple[str, object]] = []
        debug_messages: list[str] = []

        class Handler:
            def set_capability_value(self, capability_id: str, value: object) -> None:
                forwarded.append((capability_id, value))

            def debug(self, message: str) -> None:
                debug_messages.append(message)

        modules = {
            "homey": types.ModuleType("homey"),
            "homey.app": types.ModuleType("homey.app"),
            "homey_esphomedriver": types.ModuleType("homey_esphomedriver"),
            "homey_esphomedriver.entities": types.ModuleType(
                "homey_esphomedriver.entities"
            ),
            "homey_esphomedriver.entities.state": types.ModuleType(
                "homey_esphomedriver.entities.state"
            ),
            "homey_esphomedriver.entities.state.base": types.ModuleType(
                "homey_esphomedriver.entities.state.base"
            ),
        }
        modules["homey.app"].App = type("App", (), {})
        modules[
            "homey_esphomedriver.entities.state.base"
        ].AbstractEntityStateUpdateHandler = Handler

        previous = {name: sys.modules.get(name) for name in modules}
        sys.modules.update(modules)
        namespace = {"__name__": "app.app", "__file__": str(APP_PATH)}
        try:
            source = compile(APP_PATH.read_text(), str(APP_PATH), "exec")
            for _ in range(3):
                exec(source, namespace, namespace)
        finally:
            for name, module in previous.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

        handler = Handler()
        handler.set_capability_value("measure_temperature", 21.5)
        handler.set_capability_value("measure_temperature", math.nan)
        handler.set_capability_value("measure_temperature", math.inf)
        handler.set_capability_value("measure_temperature", -math.inf)

        self.assertEqual(forwarded, [("measure_temperature", 21.5)])
        self.assertEqual(len(debug_messages), 3)
        self.assertTrue(
            getattr(Handler.set_capability_value, "_io_esphome_nonfinite_guard", False)
        )


if __name__ == "__main__":
    unittest.main()
