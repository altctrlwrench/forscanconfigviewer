# 🛠️ FORScan Community Recipe Guide (`.acwrecipe` v1.1)

Welcome! This is the official guide for creating and sharing Ford As-Built modifications using the **FORScan Community Recipe** format (`.acwrecipe`).

An **`.acwrecipe`** is a simple, human-readable text file (written in YAML) that describes a FORScan modification—what vehicle it fits, which module addresses to change, and which specific bits to flip. 

### 🌍 An Open Standard for Any Tool
This format is 100% open-source and intentionally designed so **any developer or community tool** can use it. When you submit a recipe to `recipes/<platform>/`, GitHub Actions automatically validates it and compiles all recipes into [`dist/master_recipes.json`](../dist/master_recipes.json). Tools like the [AsBuiltPro Web App](https://asbuilt.altctrlwrench.com/)—or any custom script, mobile app, or viewer the community builds—can read these files directly!

---

## 💡 Best Way to Start: Copy an Existing Recipe!

You don't have to write a recipe from scratch! The easiest way to get started is to head over to **[AsBuiltPro](https://asbuilt.altctrlwrench.com/)** (or browse the `recipes/` folders here on GitHub), find a similar mod—or the same mod on another vehicle platform—and download/copy its `.acwrecipe` file as your starting point.

* **Keep titles consistent:** If you are adapting a mod that already exists on another platform (like *Double Horn Honk on Keyless Exit Disable* or *Lincoln-Style Autofold Mirrors*), **keep the `title` 100% identical**. This allows tools to link the exact same feature across different vehicles.
* **Stick to existing categories:** Try to use one of our standard categories whenever possible, though creating a variation is okay if there is a genuinely good reason.

---

## 🚀 Quick Start: Copy-Paste Template

You can also copy this template, save it as `your-mod-name.acwrecipe` inside the matching `recipes/<platform>/` folder, and fill in your values:

```yaml
title: Double Horn Honk on Keyless Exit Disable
category: Chimes and Horn
platform: F-150
model_years: 2021-2026
trim: All
validated: false
notes: Disables the double horn honk when exiting a running vehicle with the key fob.

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
            feature_name: LostPKExteriorNotificationEnable_Cfg (LPKENEC)
            target_state: LPKENEC DISABLED

recipe_version: '1.1'
```

---

## 🧩 How a Recipe Works (Plain English)

Every `.acwrecipe` file has three main parts:

### 1. Vehicle & Mod Info (Top of the file)
Describes what the mod is called and which vehicles it works on (`platform`, `model_years`, `category`, `trim`).

### 2. Steps (`steps`)
Lists each module (`BCM`, `APIM`, `DDM`, etc.) and register address (`726-63-02`) you need to touch. If a mod requires changes in both the Driver and Passenger Door Modules (`DDM` and `PDM`), each address gets its own step.

### 3. Targets (`targets`) — *Why Bits Matter More Than `community_hex`*
In FORScan spreadsheets, a line looks like `xxx* xxxx xx--`. Each character position is called a **nibble** (1 hex character = 4 binary bits).
* **`mask`**: Shows which character position is changing using a single `*`. Use `x` for untouched characters and `--` at the end for the 2-digit checksum. *(Rule: Only put **one `*`** per target! If you need to change two characters on the same line, create two separate targets under that step.)*
* **`community_hex`**: The common "write this character" value often shared on forums (e.g., `'8'`). Always wrap this in single quotes!

> ⚠️ **Use `community_hex` with Caution! (The `0 → 8` vs. `7 → F` Trap)**
> A single hex character controls **4 separate vehicle settings** at the same time. Forum posts often say *"Change this character to `8`"*, which only works if your truck started with a `0` (`0 + 8 = 8`).
>
> However, another truck with different factory options might start with a **`7`** in that exact same spot! If that owner blindly types in an `8`, they will turn on the new mod (+8) **but accidentally wipe out three of their existing factory features (-7)**. Because their truck started at `7`, their actual target character needs to be **`F`** (`7 + 8 = 15`, which is `F` in hex).
>
> **This is why the `bits` section below is so important:** by specifying *which exact bit* (`0`, `1`, `2`, or `3`) to turn on (`1`) or off (`0`), tools reading this recipe can calculate the right hex character automatically based on each user's actual factory As-Built data!

> 💡 **Quick Bit Math Cheat Sheet (1 Hex Character = 4 Bits)**
> | Bit Index | Binary Value | Position in Nibble |
> | :--- | :--- | :--- |
> | `bit: 3` | Adds / Subtracts `8` | Leftmost / Most Significant Bit ($2^3$) |
> | `bit: 2` | Adds / Subtracts `4` | Second from left ($2^2$) |
> | `bit: 1` | Adds / Subtracts `2` | Second from right ($2^1$) |
> | `bit: 0` | Adds / Subtracts `1` | Rightmost / Least Significant Bit ($2^0$) |

---

## 📋 Field Reference

### 1. Root Metadata (Top-Level Fields)

| Field | Required? | What to put here |
| :--- | :---: | :--- |
| **`title`** | **Yes** | Clean, descriptive name for the mod. **Keep this identical** to existing recipes if the mod already exists on another platform. |
| **`category`** | **Yes** | Try to use an existing category: `Lighting`, `Chimes and Horn`, `Doors and Locks`, `Mirrors`, `Convenience and Comfort`, `Cameras and Driver Assist`, `Cluster and Displays`, `Towing and Powertrain`, or `Climate Control`. *(Variations are allowed if there is a good reason).* |
| **`platform`** | **Yes** | Target vehicle: `F-150`, `F-150 Lightning`, `Super Duty`, `Bronco`, `Ranger 6G`, `Explorer`, or `Mustang`. |
| **`model_years`** | **Yes** | Applicable model years (e.g., `2021-2026` or `2024+`). |
| **`steps`** | **Yes** | The list of module and address changes (see below). |
| **`recipe_version`** | **Yes** | Must always be `'1.1'` (in quotes). Keep this as the very last line of the file. |
| **`trim`** | No | Defaults to `All`. Specify if restricted (e.g., `Diesel (6.7L Powerstroke)` for Super Duty diesel mods). |
| **`notes`** | No | Helpful tips, FORScan plain-English menu alternatives, or forum credits. |
| **`raw_community_title`** | No | Original title from the spreadsheet or forum (emojis/tags allowed). |
| **`source_sheet`** | No | Name of the spreadsheet it came from (e.g., `2021-2026 F150.xlsx`). |
| **`validated`** | No | Set to `false` for new submissions. Maintainers set this to `true` once confirmed on a real vehicle. |
| **`status`** | No | Optional review status (e.g., `untested` or `experimental`). *Note: Cannot be combined with `validated: true`.* |

---

### 2. Step Object (`steps:`)

Each item under `steps:` points to one module address:

| Field | Required? | Description |
| :--- | :---: | :--- |
| **`module`** | **Yes** | Official module acronym (`BCM`, `APIM`, `IPC`, `DDM`, `PDM`, `IPMA`, `PSCM`, `SODL`, `SODR`, etc.). |
| **`address`** | **Yes** | 7-character register address (e.g., `726-63-02`) or extended block (`7E0-162-02`). Must match a known prefix for that module. |
| **`targets`** | **Yes** | List of single-character (`*`) modifications at this address. |

---

### 3. Target Object (`targets:`)

There are two types of targets depending on what the mod does:

#### Option A: Discrete Targets (`type: discrete`) — *Most Common*
Used when turning a specific feature ON/OFF or picking a preset option.

> 📌 **IMPORTANT: Copy `feature_name` and `target_state` Directly from the Livnitup Sheets!**
> Do not reword or summarize these two fields! Copy and paste the exact text directly from the **Livnitup As-Built spreadsheets** (including underscores, abbreviations in parentheses, and capitalization).
>
> **Why?** Community tools use `feature_name` and `target_state` to automatically search and cross-reference mods across spreadsheets for other Ford platforms and model years. Even a small typo will break cross-platform matching!

```yaml
targets:
  - mask: xxx* xxxx xx--
    community_hex: '0'
    type: discrete
    bits:
      - bit: 0
        action: 0
        feature_name: LostPKExteriorNotificationEnable_Cfg (LPKENEC)
        aliases:
          - LostPKExteriorNotificationEnable_Cfg
        target_state: LPKENEC DISABLED
```
* **`mask`**: Position of the change (`*` = active character, `x` = ignore, `--` = checksum). Must be 8 or 12 data characters plus `--`.
* **`community_hex`**: Single hex character (`'0'` through `'F'`) in quotes. *(Remember: this is just a common reference example; the `bits` below do the real work!)*
* **`bits`**: List of bit changes inside that character:
  * **`bit`**: `0`, `1`, `2`, or `3`.
  * **`action`**: `0` (turn off / clear) or `1` (turn on / set).
  * **`feature_name`**: **Exact copy-paste** of the parameter name from the Livnitup sheet.
  * **`target_state`**: **Exact copy-paste** of the target state from the Livnitup sheet (e.g., `LPKENEC DISABLED`, `AFPC ENABLED`).
  * **`aliases` / `state_aliases`** *(Optional)*: Exact alternate names if another platform's Livnitup sheet spells the same feature or state slightly differently.

#### Option B: Continuous Targets (`type: continuous`)
Used for custom numbers entered by the user—like tire size, timeout seconds, or brightness percentages.

```yaml
targets:
  - mask: '*xxx xxxx xx--'
    type: continuous
    user_input: required
```
* **`user_input: required`**: Signals to apps/tools (such as AsBuiltPro) that the user must input their own custom value.
* **Do not include `community_hex`**: Continuous values depend on the user's setup and must never hardcode a default hex value.

---

## 📝 Complete Example: Multi-Module Recipe

Here is a full working recipe for **Lincoln-Style Autofold Mirrors**, which updates two addresses in the Driver Door Module (`DDM`) and two in the Passenger Door Module (`PDM`):

```yaml
title: Lincoln-Style Autofold Mirrors
raw_community_title: Lincoln-Style Autofold Mirrors
category: Mirrors
platform: Super Duty
model_years: 2023-2026
trim: All
source_sheet: 2023 Super Duty.xlsx
notes: '[Category: Mirrors] [Years: 2023-2026] Mirrors unfold only when driver door is closed and ignition turned on.'
steps:
  - module: DDM
    address: 740-03-01
    targets:
      - mask: '*xxx xxxx xx--'
        community_hex: '8'
        type: discrete
        bits:
          - bit: 3
            action: 1
            feature_name: AutoFoldProfile_Cfg (AFPC)
            target_state: AFPC ENABLED
  - module: DDM
    address: 740-12-01
    targets:
      - mask: '*xxx xxxx xx--'
        community_hex: 'F'
        type: discrete
        bits:
          - bit: 2
            action: 1
            feature_name: LincolnAutoFold_Cfg (LAFC)
            target_state: LAFC ENABLED
  - module: PDM
    address: 741-03-01
    targets:
      - mask: '*xxx xxxx xx--'
        community_hex: '8'
        type: discrete
        bits:
          - bit: 3
            action: 1
            feature_name: AutoFoldProfile_Cfg (AFPC)
            target_state: AFPC ENABLED
  - module: PDM
    address: 741-12-01
    targets:
      - mask: '*xxx xxxx xx--'
        community_hex: 'F'
        type: discrete
        bits:
          - bit: 2
            action: 1
            feature_name: LincolnAutoFold_Cfg (LAFC)
            target_state: LAFC ENABLED
recipe_version: '1.1'
```
*(Tip: In YAML, if your `mask` starts with `*`, wrap the whole mask in single quotes like `'*xxx xxxx xx--'` so YAML doesn't confuse `*` with a special alias character!)*

---

## ✅ Testing Your Recipe Locally (Optional for Contributors)

When you open a Pull Request on GitHub, our automated checks will test your recipe for you. If you have Python installed and want to test it on your computer first:

### 1. Run the Validator
From the repository root folder, run:
```bash
python scripts/validate_recipes.py recipes
```
**What the validator checks:**
* Valid YAML with no duplicate keys or merge overrides (`<<`).
* All required fields are filled out and `recipe_version: '1.1'` is present.
* Module names and address prefixes match known Ford ECUs.
* Masks are 8 or 12 data characters ending in `--` (you cannot modify checksums).
* `bit` is an integer (`0`–`3`) and `action` is an integer (`0` or `1`).
* Continuous targets have `user_input: required` and no hardcoded `community_hex`.

> **Strict Mode:** Some older legacy recipes in our catalog span multiple characters and show up as review warnings. If you want to check that your new recipe passes with **zero** warnings, run:
> ```bash
> python scripts/validate_recipes.py recipes --strict
> ```

### 2. Compile the Master Catalog
To test building the final `dist/master_recipes.json` catalog file:
```bash
python scripts/compile_catalog.py
```
*(If a build fails, the script safely keeps the last working catalog rather than saving a broken file.)*

---

## 🌐 Developer Note: Using & Exporting Recipes in Your Own Tools

Because the FORScan Community Recipe format is open-source, any web app, CLI, or tool can ingest [`dist/master_recipes.json`](../dist/master_recipes.json), which mirrors the `.acwrecipe` schema 1:1.

To export a recipe object from a JavaScript app (like [AsBuiltPro](https://asbuilt.altctrlwrench.com/)) back into a standalone `.acwrecipe` YAML file:

```javascript
import jsyaml from 'js-yaml';

function exportAcwRecipe(recipe) {
  const { file, ...pureRecipe } = recipe;
  return jsyaml.dump(pureRecipe, { indent: 2, lineWidth: -1 });
}
```
