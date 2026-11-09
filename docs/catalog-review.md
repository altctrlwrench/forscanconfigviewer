# Catalog findings and patch scope

Baseline: public repository revision
[`6820185c7096aa03c1a005594905efac09e50b35`](https://github.com/altctrlwrench/forscanconfigviewer/tree/6820185c7096aa03c1a005594905efac09e50b35),
reviewed November 8, 2026. The linked
[community thread](https://www.f150gen14.com/forum/threads/an-attempt-at-standardizing-mods-recipes-for-forscan-207-so-far-looking-for-testers.55323/)
describes the goal of preserving unrelated bits while sharing modifications
across platforms.

## Addressed in this patch

1. **Malformed input passed validation or crashed the validator.** Examples
   included missing addresses, BCM at `742-19-02`, a partial module name `B`,
   checksum-position masks, `community_hex: ZZ`, and malformed nested lists.
   Validation now checks types, required fields, address syntax, registered
   module aliases, masks, integer bit actions, and verification metadata, with
   readable per-file errors. Duplicate YAML keys fail rather than silently
   replacing earlier instructions.
2. **Compilation lost contributor verification flags.** A source recipe with
   `validated: false` previously lost the flag and was included in the
   `validated_recipes` count. Explicit flags now survive both catalog views.
   Counts distinguish structurally accepted recipes from explicit
   vehicle-verification assertions. Existing missing flags remain unknown.
3. **Ambiguous legacy targets were invisible.** Compatibility mode now reports
   36 warnings on the baseline catalog: 21 non-atomic masks (17 with multiple
   active nibbles and four with none), two legacy hex values, and 13 individual
   hex/bit disagreements across 12 targets. `--strict` rejects these warnings.
4. **A compilation read failure could silently omit a recipe.** Read/parse
   failures now abort, and output replacement occurs only after the complete
   catalog has serialized successfully. A failed build preserves the prior
   output. Regression tests run in the catalog workflow.

The output retains all 211 recipes across 111 canonical features. At this
revision the source contains zero explicit `validated: true` assertions, four
explicit `status: untested` entries, and 207 recipes without a recorded status.
Zero explicit assertions means that the public metadata cannot establish a
tested count; it does not establish that nobody has tested these modifications.

## Recipe issues requiring source verification

The following findings remain in the catalog and are concrete review candidates.
The patch adds diagnostics without choosing replacement vehicle values.

### High priority: mutually exclusive trims are unconditional

[Ranger Glare-Free Matrix High Beams](../recipes/ranger_6g/glare_free_matrix_high_beams_adaptive_driving_beam_2024_plus.acwrecipe)
declares `trim: All` and includes two HCM `734-01-04` steps. Notes identify a
Raptor value `A0D1` and a Lariat value `A54E`. Both steps are present without
machine-readable eligibility. A sequential consumer can apply incompatible
trim variants.

**Recommended resolution:** verify source applicability, then split by trim or
define mutually exclusive variants that every consumer understands. Preserve
each verified value in its applicable branch. This needs agreement with the
private app's recipe-selection behavior before changing the catalog shape.

### High priority: model-year alternatives are unconditional

[F-150 Auto Relock](../recipes/f150/auto_relock_on_unopened_door_enable_2021_2026.acwrecipe)
contains two `726-58-02` steps whose notes distinguish 2021–2023 and 2024–2026.
The root spans 2021–2026, and eligibility exists only in prose. Its APIM target
also specifies hex `3` alongside bit 3 set to one, which that hex value cannot
satisfy.

**Recommended resolution:** select one verified year branch using structured
metadata or separate recipes, then resolve the APIM representation against the
correct workbook/module version. Similar engineering names alone are
insufficient evidence to choose a value.

### High priority: Traffic Jam Assist instructions disagree

[F-150 Traffic Jam Assist](../recipes/f150/traffic_jam_assist_enable_disable_bluecruise_2021_2026.acwrecipe)
promises disabling Highway Assist while setting `ModuleFeatureCfg_HwyAssist`
to an enabled state. Its second target's hex `8` also disagrees with bit 1 set
to one. The conflict is observable; the correct replacement is unresolved.

**Recommended resolution:** obtain authoritative workbook or working-vehicle
evidence, then align the title, intended outcome, feature state, and bit actions.
The new validator emits a hex/bit diagnostic for this target.

### Review the legacy format explicitly

[Ranger Trail Turn Assist](../recipes/ranger_6g/trail_turn_assist_enable_2024_plus.acwrecipe)
contains a discrete `community_hex: x` placeholder without bit actions. The
[Ranger seatbelt recipe](../recipes/ranger_6g/remove_all_seatbelt_warnings_and_chimes_including_ok_button_2024_plus.acwrecipe)
contains four masks with no active positions. Several numerical parameters span
multiple nibbles, including tire circumference and timeouts; these need defined
width, units, ordering, and shared input semantics rather than mechanical
conversion into unrelated one-nibble operations.

**Recommended resolution:** resolve placeholders from sources and document a
numeric-field contract before migrating continuous targets. The default build
continues to report these entries; strict mode provides an explicit review gate.

## Validation and limits

Local validation passed all **28 regression tests** on Python 3.14.8 with
PyYAML 6.0.3. The rebuilt catalog's recipe records and feature mappings match
the baseline exactly; only the summary counts changed for the existing data.
The default build passed with 36 warnings. The configured GitHub Actions runtime
is Python 3.11; that hosted run has not been executed for this local patch.

Run from the repository root after installing `requirements.txt`:

```sh
python -m unittest discover -s tests -v
python scripts/validate_recipes.py recipes
python scripts/compile_catalog.py
python scripts/validate_recipes.py recipes --strict
```

The final command currently exits nonzero because the 36 review warnings need
source disposition. A default build passing alongside a strict failure is the
intended compatibility behavior. This is not a passing vehicle-compatibility
test. Hosted CI, private application integration, and vehicle testing remain
outside this local validation.
