# As Built Pro & Community Recipes 🚀

Welcome to the public community repository for **As Built Pro**. This repository serves as the public hub for reporting bugs, suggesting features, and maintaining the open-source **Automotive As-Built Recipe Catalog** for Ford vehicles.

---

## 🛠️ The App
The core application is hosted privately to ensure the security of the processing engine and proprietary data mappings. You can access the live tool here:
👉 **[https://asbuilt.altctrlwrench.com/](https://asbuilt.altctrlwrench.com/)**

### Key Features:
* **As-Built Analysis:** Upload your `.abt` or `.ab` files for instant human-readable decoding.
* **Deep Diffing:** Compare your vehicle's current configuration against the community-standard master spreadsheets.
* **One-Click Modifications (Recipes):** Execute validated bitwise modifications safely on your vehicle without guessing hex codes.

---

## 📖 Community As-Built Recipes

This repository now hosts the open-source **[Recipe Catalog](recipes/)** used by As Built Pro! 

Each recipe defines the exact CAN module registers, bitmasks, and offset math needed to enable or disable vehicle features (such as Bambi Mode, Auto Relock, Global Windows, Turn Signal Outage Detection, and Cluster Temperatures).

* **Browse by Platform:** Check the [`recipes/`](recipes/) folder for your vehicle (`f150`, `super_duty`, `bronco`, `ranger_6g`, `explorer`, `mustang`).
* **Recipe Specification & Authoring Guide:** See the **[Recipes Authoring Guide](recipes/README.md)** for full details on the YAML schema and examples.
* **Compiled Catalog:** Every recipe or tooling push to `main` runs structural validation and compiles the catalog into [`dist/master_recipes.json`](dist/master_recipes.json) via GitHub Actions. Existing recipes with review warnings remain included. A schema pass does not establish vehicle compatibility or a successful vehicle test.

### Contributing a Recipe:
Have a modification working on your truck that isn't listed yet?
1. Create a `.acwrecipe` file under `recipes/<platform>/<feature_name>.acwrecipe`.
2. Follow the [Recipe Schema Guide](recipes/README.md) and set `validated: false`.
3. Open a Pull Request! The compiler preserves `validated: false`; set `validated: true` only after a maintainer accepts supporting vehicle-test evidence. Missing verification metadata means unknown, rather than verified. Accepted recipes remain available for discovery regardless of that flag.

### Development checks

Use Python 3.11 or newer in a virtual environment, then run:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate_recipes.py recipes
python scripts/compile_catalog.py
```

For a stricter review, run `python scripts/validate_recipes.py recipes --strict`
or `python scripts/compile_catalog.py --strict`. Strict mode fails on existing
review warnings as well as structural errors; the current catalog needs source
review before it can pass this mode. The default mode preserves existing recipe
values and reports those warnings explicitly.

Catalog summaries distinguish `schema_valid_recipes` from `validated_recipes`
(explicit `validated: true`), `unverified_recipes`, and `untested_recipes`
(explicit `status: untested`). Untested recipes are a subset of unverified ones.
Missing verification flags are preserved as missing; compilation never invents
vehicle-test results.

The [catalog review](docs/catalog-review.md) records unresolved recipe issues.

---

## 🐞 How to Provide Feedback & Issues

We are currently in Beta. Your feedback is essential for refining the parsing logic and ensuring accuracy across different Ford modules.

### 1. Report a Bug
If the tool crashes, misinterprets an address, or displays incorrect data:
* **[Open a New Issue](../../issues/new)**.
* Include the Module name (e.g., APIM, IPC) and the specific Address/HEX string that caused the issue.
* *Please do not post your full VIN in public issues.*

### 2. Request a Feature
Have an idea for a better dashboard or a specific comparison tool?
* Open an issue with the label `enhancement`.

---

## 🔒 Privacy & Safety
* **Data Privacy:** This tool processes all vehicle files in-memory. Your uploaded `.abt` and `.ab` files are never saved to our servers or stored in any database.
* **Source Code:** The core engine is maintained in a private repository to protect the specialized parsing logic and prevent unauthorized redistribution.

---

## ⚠️ Disclaimer
This tool is a community-led project and is not affiliated with Ford Motor Company. Use the information provided at your own risk when modifying vehicle software. Always back up your factory As-Built configuration before making any changes.
