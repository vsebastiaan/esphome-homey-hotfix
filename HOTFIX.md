# Homey ESPHome climate non-finite value hotfix

This tree is based on `Doekse/esphome-homey`.

## Why

ESPHome climate entities may report `NaN` before a first valid temperature or humidity measurement. Homey SHS transports app capability values through strict JSON and crashes when the app emits literal `NaN`.

## Temporary fix

`app.py` guards the shared ESPHome state capability writer and drops all non-finite floats (`NaN`, `Infinity`, `-Infinity`) before they enter Homey IPC. Finite values are passed through unchanged.

The app id remains `io.esphome`, so a development install upgrades/replaces the existing app in place. Version is bumped to `0.4.3` for this hotfix.
