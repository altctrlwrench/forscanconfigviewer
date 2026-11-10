# AsBuiltPro UI improvement plan

**Status: proposed UI changes are unimplemented and untested against the private
application or a vehicle.** The browser observations below were manually
reproduced; they are separate from implementation or vehicle validation.

Reviewed the [live application](https://asbuilt.altctrlwrench.com/) on November 8,
2026, using its default desktop viewport and a 390 × 844 CSS-pixel viewport.
The public catalog baseline was
[`6820185`](https://github.com/altctrlwrench/forscanconfigviewer/tree/6820185c7096aa03c1a005594905efac09e50b35).
The live application is privately maintained, so the items below are an
implementation plan for its author. The public-repo patch does not change the
deployed interface.

## Fix first: one numeric value must drive all recipe steps

**Observed defect.** Open Common Mods, search for “Tire Size Calibration,” and
choose “Validate & Compare Memory Blocks.” Both steps initially show a separate
circumference input of 2455 mm and a converter output of `0997`. Change the first
input to 2785 mm. Its converter changes to `0AE1`, while the second remains at
2455 mm / `0997`.

The dialog presents both converter results as “FORScan Write Value (4-Digit
Hex),” although each step targets only part of that four-digit value. A user
working down the procedure can combine values for two different circumferences.
The supplied synthetic number tested the converter only; it establishes no
supported vehicle calibration limit.

**Recommended fix.** Put one “Effective rolling circumference (mm)” input above
the procedure and derive every affected step from the same value. Show the full
encoded value once, then show which two hex digits belong in each masked field.
Keep measured rolling circumference and a tire-dimensions estimate clearly
distinguished. Label the converter output as an encoded parameter until a
vehicle-specific before/after preview is available.

**Acceptance criteria:** changing either representation updates both step
previews; changing between Direct MM and Tire Dimensions retains one shared
parameter; clearing or entering an invalid value removes usable output; exported
plans and copied previews use the same value. Numeric encoding bounds and any
vehicle-specific supported limits must be supplied by the authoritative mapping.

[Step 1 screenshot](review-evidence/tire-input-step-1.jpg) ·
[Step 2 screenshot](review-evidence/tire-input-step-2.jpg) ·
[DOM evidence containing both values](review-evidence/tire-dialog-dom.txt)

## Fix first: make narrow-screen actions reachable

**Observed defect.** At 390 × 844, the ribbon clips to the right after Common
Mods. The recipe dialog lays its title, status badge, export controls, and close
control on one horizontal row. The title wraps into a narrow column and the
right-hand controls extend past the visible panel. The mobile dialog capture
shows this after the modification steps finished loading.

**Recommended fix.** Use a compact mobile header with an always-visible menu
button, current vehicle summary, and search. Move database, cohort, comparison,
and bit-display controls into a mode-specific panel. Stack the dialog title,
status, and actions at narrow breakpoints. Keep a labelled Close button visible
independently of horizontal content. Technical hex matrices may scroll inside
their own region.

**Acceptance criteria:** at 390 and 768 px, navigation, close, search, and primary
recipe actions remain visible and keyboard reachable; page-level horizontal
scrolling is unnecessary; interactive controls have practical touch targets
(recommend 44 × 44 px); closing a dialog restores focus to its opener. Escape
already closed the inspected dialog successfully and should keep doing so.

[Mobile catalog screenshot](review-evidence/mobile-390.jpg) ·
[Mobile dialog screenshot](review-evidence/mobile-dialog-390.jpg)

## Make theme selection visible and consistent

The inspected app already uses a dark theme and exposes an icon button named
“Light Mode” in the desktop ribbon. The requested improvement is an obvious
**Light / Dark / System** selector, available on desktop and mobile.

**Agreed default:** follow the operating system. Remember a manual Light or Dark
choice on the device; choosing System restores automatic behavior. Make the
selected preference and the currently applied appearance understandable, for
example “System — currently Dark.”

Use shared color tokens for page backgrounds, panels, text, borders, focus,
status labels, and highlighted hex/bit changes. Theme selection should preserve
vehicle context, filters, loaded backups, and open recipe inputs. Keep warning
and comparison meanings consistent across themes.

**Acceptance criteria:** first visit follows the OS; explicit selections survive
reload; an OS change updates the appearance only while System is selected;
initial rendering uses the correct theme without a visible flash; mobile and
desktop expose the same setting; all dialogs and technical tables use the
selected theme. Check text, focus, status, and changed-bit readability in both
appearances. Persistence and OS-following behavior have not been verified in
the existing private app.

## Fix next: distinguish matching from vehicle verification

**Observed behavior.** Common Mods offers Verified Native, Untested, Matches
Same Address, Relocated Address, Partial Match, and Unsupported statuses. Native
cards describe themselves as “Officially verified and tested for this vehicle
platform.” The inspected public catalog provides no explicit `validated: true`
flags or structured vehicle-test evidence. Independent evidence maintained by
the private application was outside this review.

Candidates and partial matches also expose a prominently labelled “Recommended
As-Built Values” section and a Copy action. This gives a stronger execution cue
than the candidate status supports. With no backup loaded, the tire dialog also
shows “Target Platform (F-150): MISSING” next to “Verified Native,” without
explaining what is missing.

**Recommended fix.** Show two independent facts: mapping result and verification
evidence. Suggested labels are “Native recipe,” “Candidate mapping,” “Partial
mapping,” and “Tested on [year / trim / module software]” when evidence exists.
Use “Candidate pattern” for unverified values. Explain incomplete mappings
beside affected steps. Give missing data a specific reason: “No backup loaded,”
“Address absent from backup,” or “Parameter absent from workbook.”

**Acceptance criteria:** absent verification metadata stays unknown; a name or
address match alone cannot produce a vehicle-tested label; incomplete mappings
identify every missing step; unresolved conflicts lead to an inspection or
report action before a calculated vehicle-change export is offered.

The author has already acknowledged related mapping failures in
[issue #2](https://github.com/altctrlwrench/forscanconfigviewer/issues/2).
This review did not reproduce that report's Mach-E mapping sequence.

## Simplify the main workflow

The desktop interface exposes five work modes, a master-database selector, a
module selector, four AB file groups, display controls, and global search before
the user chooses a task. Common Mods adds another vehicle selector and a second
search field. These controls are useful, but their purpose and scope compete.

Recommended task flow:

1. **Choose vehicle:** platform, exact model year, powertrain, trim, and relevant
   module/software variant; show what was inferred and what still needs a choice.
2. **Choose task:** Browse mods, Compare backups, or Advanced workbench.
3. **Inspect a recipe:** outcome, prerequisites, verification evidence, required
   modules, optional steps, and source references.
4. **Preview changes:** existing value, proposed value, changed bits, preserved
   bits, and the reason for each change.
5. **Export a plan:** selected steps, source recipe revision, vehicle context,
   before/after values, and the original backup reference.

Use one vehicle context throughout. Rename AB Grp 1–4 to editable, descriptive
labels such as Original backup and Modified backup. The compare modes can still
support extra cohorts behind Advanced workbench. Use one contextual search with
a visible scope such as “Search recipes” or “Search module mappings.”

**Acceptance criteria:** switching modes retains vehicle context and loaded
backups; selectors make different database variants understandable; an optional
step is an explicit choice; preview and export reflect the selected year/trim
branch consistently. Year/trim alternatives currently encoded only in recipe
notes require a catalog contract before the UI can reliably select them.

## Improve navigation and accessibility

The observed accessibility trees expose mode tabs and clickable recipe headings
as generic elements, and the validation window as generic content instead of a
named dialog. The two search fields rely on placeholder text for identification.
Small ribbon controls measured about 13.5–20 CSS px in height. Text contrast has
not been measured, so this review makes no contrast-compliance claim.

Use actual buttons or semantic tabs for mode changes and recipe navigation,
persistent field labels, a named modal dialog, visible focus, and explicit
loading/result announcements. Preserve the existing Escape behavior. Reserve
color for reinforcement alongside clear text labels. Increase primary text and
control sizes while keeping dense bit-level tables in the advanced view.

**Acceptance criteria:** keyboard-only users can complete recipe search and
inspection; dialog focus stays within the open dialog and returns on close;
screen-reader output names vehicle, search, status, and each recipe action;
filtered counts and loading completion are announced without repeated noise.

## Delivery order and verification

| Order | Work | Evidence required before release |
| --- | --- | --- |
| 1 | Shared numeric parameter and precise output labels | Reproduction above becomes one consistent value across steps and export |
| 2 | Mobile header and dialog layout | Screenshots and keyboard checks at 390, 768, and desktop widths |
| 3 | Verification labels and missing-data reasons | Fixtures for unknown, untested, native, partial, and conflicting data |
| 4 | Light / Dark / System theme control, defaulting to System | Reload, OS-change, readability, and mobile-access checks |
| 5 | Unified vehicle context, optional steps, and preview | Year/trim fixture branches and before/after comparisons |
| 6 | Task-based navigation and accessible controls | Keyboard, screen-reader, and ordinary user walkthroughs |

No vehicle files were uploaded, no vehicle was modified, and no application
source or server behavior was inspected. Browser observations establish the
reproductions above; proposed behavior still needs implementation and testing
in the private application.
