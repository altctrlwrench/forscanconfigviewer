# AsBuiltPro Community Recipes 🛠️

Welcome to the **AsBuiltPro Recipe Catalog**. This directory hosts open-source, machine-executable automotive configuration recipes for Ford vehicles (F-150, Super Duty, Bronco, Ranger, Explorer, Mustang, and more).

Each recipe defines the exact CAN module registers, bitmasks, and offset logic required to enable or disable features using FORScan.

---

## 📁 Directory Structure

Recipes are organized by **vehicle platform**:

```text
recipes/
├── f150/              # 14th Gen (2021-2026) F-150 & Lightning
├── super_duty/        # (2023-2026) Super Duty
├── bronco/            # (2021+) 6G Bronco
├── ranger_6g/         # (2024+) 6G Ranger
├── explorer/          # (2020-2026) Explorer
└── mustang/           # (2024+) S650 Mustang
```

---

## 📜 Recipe Schema Specification

Every recipe is stored as an individual `.yaml` file. Here is the reference template:

```yaml
# ==============================================================================
# 1. Feature Identity & Governance
# ==============================================================================
title: "Bambi Mode (High Beams with Fog Lights)"             # Standardized curated title
raw_community_title: "Fogs on when high beams are on (aka Bambi Mode) (2021-2026)" # Exact forum/sheet string
category: "Lighting"                                        # Lighting, Locks and Security, Chimes and Horn, etc.

# Governance
validated: true                                             # true = verified by AsBuiltPro; false = unverified community PR
verified_by: "Kyle / AsBuiltPro"
source_sheet: "2021-2026 F150.xlsx"

# Vehicle Compatibility
platform: "F-150"                                           # F-150, Super Duty, Bronco, Ranger (6G), Explorer, Mustang
model_years: "2021-2026"
trim: "All"                                                 # "All", or specific: "Raptor", "Lightning", "Tremor"

# Optional Operational Notes
forscan_menu: "Using Front Fog With High Beam (Allowed)"     # Plain-English GUI menu equivalent (if supported)
prerequisites: "Sync 4 version 22012 or higher"             # Firmware or hardware requirement (optional)
post_procedure: "Cycle ignition after writing"              # e.g. "PCM Relearn", "Reset APIM" (optional)
warnings: "Check local regulations regarding auxiliary forward lighting" # Known side-effects (optional)

# ==============================================================================
# 2. Execution Steps
# ==============================================================================
steps:
  - module: "BCM"                                           # CAN Module acronym (BCM, IPC, APIM, DDM, PDM, etc.)
    address: "726-39-02"                                    # Target CAN address
    mask: "xxx0-xxxx-xx--"                                  # FORScan visual display mask
    nibble: 3                                               # 0-indexed character position (the 4th character)
    recommended_hex: "0"                                    # Community suggested hex value
    hex_offset: "-1"                                        # Offset hint (e.g. "+8", "+2", "-1", optional)
    community_instruction: "If 1 change to 0"               # Text guidance from forum/sheet
    feature_name: "FrontFog_WithHighBeams_Cfg (FFWHBC)"     # Exact workbook subfeature name
    target_state: "FFWHBC ALLOW"                            # Exact workbook target state
    bit: 3                                                  # Target bit index (0 to 3)
    action: 0                                               # 0 = Clear/Disable, 1 = Set/Enable
```

---

## ⚙️ Modification Types

1. **Discrete Bitwise Flag (Default):**
   * Operates on isolated bits (`bit: 0`, `action: 1`) using bitwise AND/OR logic. Never overwrites adjacent factory features.
2. **Multi-Nibble Atomic Enum (`type: byte_enum`):**
   * For animations, themes, and visual design variants (e.g. 75th Anniversary Splash Screen `24`) where 2 or more nibbles represent a single unified code.
3. **Continuous Parameter (`type: continuous`):**
   * For numerical calibrations and timers (e.g. Tire Circumference in `mm`, Power Point Timeout in `seconds`).

---

## 🚀 How to Contribute a New Recipe

1. **Fork this repository** and create a feature branch (`git checkout -b recipe/my-new-mod`).
2. Create a new `.yaml` file inside the appropriate platform directory:
   `recipes/<platform>/<short_name>.yaml`
3. Fill in the fields following the schema above.
   * If you are a community contributor submitting an untested or community-tested mod, set **`validated: false`**.
4. Submit a **Pull Request**.
5. Once reviewed and verified on physical hardware or As-Built option matrices, an admin will toggle **`validated: true`** and merge.

---

## 🤖 Automated CI & Master Catalog Compilation

Upon merging to `main`, a GitHub Action automatically:
1. Validates the YAML formatting.
2. Filters for all recipes where `validated: true`.
3. Compiles the master release payload into **`dist/master_recipes.json`**.
4. As Built Pro fetches this master JSON file directly for instant in-app execution.
