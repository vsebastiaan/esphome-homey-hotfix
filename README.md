# ESPHome Homey hotfix

Temporary fork/worktree for fixing non-finite (`NaN`/`Infinity`) ESPHome climate values before they are passed to Homey. Based on `Doekse/esphome-homey` and `Doekse/homey-esphomedriver`.

The observed failure on Homey SHS is a JSON parse crash when a climate state contains `NaN`. This repository is intended to carry the minimal compatibility hotfix until the upstream driver handles non-finite climate values safely.
