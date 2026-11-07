# AsBuiltPro Recipe Specification & Authoring Guide (v1.1) 📖

This guide documents the official **AsBuiltPro Recipe Specification (v1.1)** used to define, validate, and compile automated As-Built CAN modifications for Ford vehicles.

---

## 📌 Overview

Every recipe in this catalog is stored as an individual `.acwrecipe` YAML file under `recipes/<platform>/`. 

Each `.acwrecipe` file defines:
1. **Target Vehicle Architecture:** The platform, model years, and trim/powertrain compatibility.
2. **Deterministic Step Sequence:** The exact CAN modules and addresses required for the modification.
3. **Atomic Single-Nibble Targets:** The exact visual mask, target hex or bitwise toggles, and feature names mapped from Ford engineering definitions.

When pushed to GitHub, GitHub Actions runs automated validation and compiles all recipes into [`dist/master_recipes.json`](../dist/master_recipes.json), which directly powers the [AsBuiltPro Web App](https://asbuilt.altctrlwrench.com/).

---

## 📐 Schema Specification (v1.1)

### Root Metadata

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `title` | `string` | **Yes** | Standardized canonical feature title (e.g. `Double Horn Honk on Keyless Exit Disable`). |
| `raw_community_title` | `string` | No | Original spreadsheet or forum title, including emojis or platform tags. |
| `category` | `string` | **Yes** | Functional category (e.g. `Lighting`, `Chimes and Horn`, `Doors and Locks`, `Mirrors`, `Convenience and Comfort`, `Cameras and Driver Assist`, `Cluster and Displays`, `Towing and Powertrain`, `Climate Control`). |
| `platform` | `string` | **Yes** | Target vehicle platform (`F-150`, `F-150 Lightning`, `Super Duty`, `Bronco`, `Ranger 6G`, `Explorer`, `Mustang`). |
| `model_years` | `string` | **Yes** | Applicable year span (e.g. `2021-2026`, `2024+`). |
| `trim` | `string` | **Yes** | Target equipment trim or powertrain (defaults to `All`, or e.g. `Diesel (6.7L Powerstroke)` for Super Duty diesel features). |
| `source_sheet` | `string` | No | Source spreadsheet name (e.g. `2021-2026 F150.xlsx`). |
| `notes` | `string` | No | Contextual instructions, FORScan menu alternatives, and source forum references. |
| `steps` | `list` | **Yes** | List of CAN module address modifications. |
| `recipe_version` | `string` | **Yes** | **Must be `'1.1'` on the final line of the recipe.** |

---

### Step Object (`steps[]`)

Each step targets a specific physical ECU module and 7-character register address:

```yaml
steps:
  - module: BCM
    address: 726-63-02
    targets:
      - mask: xxx* xxxx xx--
        community_hex: '0'
        type: discrete
        bits:
          - bit: 0
            action: 0
            feature: LostPKExteriorNotificationEnable_Cfg (LPKENEC)
```

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `module` | `string` | **Yes** | Physical ECU acronym (`BCM`, `APIM`, `IPC`, `DDM`, `PDM`, `IPMA`, `PSCM`, `SODL`, `SODR`, etc.). |
| `address` | `string` | **Yes** | CAN register address matching `XXX-XX-XX` format (e.g. `726-63-02`). Checksum nibbles (`--`) are omitted from the address. |
| `targets` | `list` | **Yes** | One or more atomic single-nibble targets within this address. |

---

### Target Object (`targets[]`)

#### 1. Discrete Targets (`type: discrete`)
Used when a modification toggles specific binary bits or writes an enumerated hex value:

```yaml
targets:
  - mask: xxx* xxxx xx--
    community_hex: '0'
    type: discrete
    bits:
      - bit: 0
        action: 0
        feature: LostPKExteriorNotificationEnable_Cfg (LPKENEC)
```

* **`mask`**: Single-nibble visual position indicator (`*` marks the active nibble, `x` marks untouched nibbles, `--` marks the checksum). Exactly one `*` per target.
* **`community_hex`**: Recommended hex character (`'0'`–`'F'`).
* **`bits`**: Atomic bit manipulation list:
  * **`bit`**: 0-indexed bit within the target nibble (`0`, `1`, `2`, or `3`). Bit 0 is least significant ($2^0$), bit 3 is most significant ($2^3$).
  * **`action`**: `0` (clear bit / disable) or `1` (set bit / enable).
  * **`feature`**: Exact engineering parameter name from the official module mapping.

#### 2. Continuous Targets (`type: continuous`)
Used for user-configurable numerical parameters such as tire circumference, timeout durations, or PWM brightness levels:

```yaml
targets:
  - mask: *xxx xxxx xx--
    type: continuous
    user_input: required
```

* **`user_input: required`**: Signals to the AsBuiltPro UI that the user must specify their desired value.
* **No forced `community_hex`**: Continuous parameters must never hardcode a default value.

---

## 📝 Complete Example: Multi-Module Recipe

Below is a complete, validated v1.1 recipe for **Lincoln-Style Autofold Mirrors** requiring coordinated changes across DDM (Driver Door Module) and PDM (Passenger Door Module):

```yaml
title: Lincoln-Style Autofold Mirrors
raw_community_title: Lincoln-Style Autofold Mirrors
category: Mirrors
platform: Super Duty
model_years: 2023-2026
trim: All
source_sheet: 2023 Super Duty.xlsx
notes: '[Category: Mirrors] [Years: 2023-2026] [Original Title: Lincoln-Style Autofold
  Mirrors]

  Mirrors unfold only when driver door is closed and ignition turned on.'
steps:
- module: DDM
  address: 740-03-01
  targets:
  - mask: *xxx xxxx xx--
    community_hex: '8'
    type: discrete
    bits:
    - bit: 3
      action: 1
      feature: AutoFoldProfile_Cfg (AFPC)
- module: DDM
  address: 740-12-01
  targets:
  - mask: *xxx xxxx xx--
    community_hex: 'F'
    type: discrete
    bits:
    - bit: 2
      action: 1
      feature: LincolnAutoFold_Cfg (LAFC)
- module: PDM
  address: 741-03-01
  targets:
  - mask: *xxx xxxx xx--
    community_hex: '8'
    type: discrete
    bits:
    - bit: 3
      action: 1
      feature: AutoFoldProfile_Cfg (AFPC)
- module: PDM
  address: 741-12-01
  targets:
  - mask: *xxx xxxx xx--
    community_hex: 'F'
    type: discrete
    bits:
    - bit: 2
      action: 1
      feature: LincolnAutoFold_Cfg (LAFC)
recipe_version: '1.1'
```

---

## 🛠️ Validation & Compilation Tooling

Before committing any recipe, run the validator to verify that it meets all v1.1 standards:

### 1. Validate Schema
```powershell
# From the forscanconfigviewer directory:
python scripts/validate_recipes.py recipes
```

The validator checks:
* Valid YAML syntax with no unquoted special characters.
* Required metadata (`title`, `platform`, `model_years`, `category`, `steps`).
* `recipe_version: '1.1'` on the final line.
* Single-nibble visual masks (`xxx* xxxx xx--`).
* Proper bit indices (`0`–`3`) and actions (`0` or `1`).
* Continuous parameters have `user_input: required` with no hardcoded hex.
* Super Duty diesel trim requirements.

### 2. Compile Master Catalog
```powershell
python scripts/compile_catalog.py
```
This runs the validator and compiles all recipes into `dist/master_recipes.json`.

---

## 🌐 Online Web Tool Integration ([AsBuiltPro](https://asbuilt.altctrlwrench.com/))

`dist/master_recipes.json` compiles recipes in a 1:1 schema match with `.acwrecipe` files (omitting redundant raw YAML text). To export a recipe directly from the web browser:

```javascript
import jsyaml from 'js-yaml';

// Pure 1-line export:
function exportAcwRecipe(recipe) {
  const { file, ...pureRecipe } = recipe;
  return jsyaml.dump(pureRecipe, { indent: 2, lineWidth: -1 });
}
```
