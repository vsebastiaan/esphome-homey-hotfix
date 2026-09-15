# Homey ESPHome climate non-finite value hotfix

This tree is based on `Doekse/esphome-homey`.

## Why

ESPHome climate entities may report `NaN` before a first valid temperature or humidity measurement. Homey SHS transports app capability values through strict JSON and crashes when the app emits literal `NaN`.

## Fix

`app.py` guards the shared ESPHome state capability writer and drops all non-finite floats (`NaN`, `Infinity`, `-Infinity`) before they enter Homey IPC. Finite values are passed through unchanged. The guard is idempotent because the Homey Python runner can evaluate `app.py` more than once; its original delegate is captured by value, preventing recursive self-wrapping.

The app id remains `io.esphome`, so a development install upgrades/replaces the existing app in place. Version is bumped to `0.4.4` for this hotfix.
