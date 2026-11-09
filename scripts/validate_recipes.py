#!/usr/bin/env python3
"""
AsBuiltPro Recipe Schema Validator & Linter (v1.1).
Rejects malformed metadata, module addresses, targets, and bit actions.
Reports legacy non-atomic masks, legacy hex values, and conflicting target
representations for review. --strict also rejects those warnings.
Structural validation does not establish vehicle compatibility or testing.
"""

import argparse
import sys
import os
import glob
import re
import yaml

STANDARD_MODULE_PREFIXES = {
    '6F0': ['BCMC'],
    '6F6': ['LDCMA'],
    '6F7': ['LDCMB'],
    '706': ['IPMA'],
    '720': ['IPC'],
    '724': ['SCCM', 'TRM'],
    '726': ['BCM', 'BDYCM', 'BODYCM', 'BDYCM-BCM'],
    '727': ['ACM'],
    '730': ['PSCM'],
    '733': ['HVAC', 'DATC'],
    '734': ['HCM'],
    '736': ['DSP'],
    '737': ['RCM'],
    '740': ['DDM'],
    '741': ['PDM'],
    '744': ['DSM'],
    '754': ['TCU'],
    '760': ['ABS'],
    '761': ['CCM'],
    '764': ['CCM'],
    '765': ['CMR', 'IPMB'],
    '783': ['DSP', 'VDM'],  # DSP on CD6 Explorer/Aviator, VDM on F-150/Lightning
    '791': ['TRM'],
    '797': ['GSM', 'GWM'],
    '7B7': ['BCMB'],
    '7D0': ['APIM'],
    '7E0': ['PCM'],
    '7E4': ['BECM'],
    '7E6': ['SOBDM'],
    '7E7': ['SOBDMC'],
    '7E8': ['SOBDMB']
}

class RecipeLoader(yaml.SafeLoader):
    """Safe YAML loading without silent overwrites of duplicate mapping keys."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    "found an unhashable mapping key", key_node.start_mark
                ) from exc
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    f"found duplicate key {key!r}", key_node.start_mark
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def find_recipe_files(recipes_dir):
    """Use the same deterministic source set for validation and compilation."""
    return sorted(set(
        glob.glob(os.path.join(recipes_dir, "**", "*.acwrecipe"), recursive=True)
        + glob.glob(os.path.join(recipes_dir, "**", "*.yaml"), recursive=True)
    ))


def load_recipe(path):
    with open(path, "r", encoding="utf-8") as recipe_file:
        return yaml.load(recipe_file, Loader=RecipeLoader)


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_catalog(recipes_dir="recipes", strict=False):
    """Return structural validity; strict mode additionally rejects review warnings."""
    recipe_files = find_recipe_files(recipes_dir)
    
    if not recipe_files:
        print(f"Error: No recipe files found in '{recipes_dir}'.", file=sys.stderr)
        return False

    errors = []
    warnings = []
    total_steps = 0
    total_targets = 0
    format_counts = {'discrete_targets': 0, 'continuous_targets': 0}

    for rf in recipe_files:
        rel_path = os.path.relpath(rf, recipes_dir).replace('\\', '/')
        try:
            data = load_recipe(rf)
        except (OSError, UnicodeError, yaml.YAMLError) as e:
            errors.append(f"[{rel_path}] YAML parse error: {e}")
            continue

        if not isinstance(data, dict):
            errors.append(f"[{rel_path}] Root must be a dictionary.")
            continue

        title = data.get('title', '')
        plat = data.get('platform', '')
        trim = data.get('trim', 'All')
        steps = data.get('steps', [])
        version = data.get('recipe_version', '')

        for field in ('title', 'platform', 'model_years', 'category'):
            if not _nonempty_string(data.get(field)):
                errors.append(f"[{rel_path}] '{field}' must be a nonempty string.")
        if not _nonempty_string(trim):
            errors.append(f"[{rel_path}] 'trim' must be a nonempty string when present.")
        if 'source_sheet' in data and not isinstance(data['source_sheet'], str):
            errors.append(f"[{rel_path}] 'source_sheet' must be a string when present.")
        if 'validated' in data and type(data['validated']) is not bool:
            errors.append(f"[{rel_path}] 'validated' must be a boolean when present.")
        status = data.get('status')
        if 'status' in data and not _nonempty_string(status):
            errors.append(f"[{rel_path}] 'status' must be a nonempty string when present.")
        if data.get('validated') is True and isinstance(status, str) and status.strip().lower() in ('untested', 'experimental'):
            errors.append(f"[{rel_path}] 'validated: true' conflicts with status '{status}'.")
        if version != '1.1':
            errors.append(f"[{rel_path}] Expected recipe_version: '1.1', found: '{version}'.")

        if not isinstance(steps, list) or not steps:
            errors.append(f"[{rel_path}] 'steps' must be a nonempty list.")
            continue

        # Trim validation
        if plat == 'Super Duty' and isinstance(title, str) and any(k in title.lower() for k in ['diesel exhaust auto regen', 'soot percentage', 'dpf']):
            if trim != 'Diesel (6.7L Powerstroke)':
                errors.append(f"[{rel_path}] Super Duty diesel recipe must have trim: 'Diesel (6.7L Powerstroke)', found: '{trim}'")

        written_bits = {}
        for s_idx, step in enumerate(steps):
            total_steps += 1
            if not isinstance(step, dict):
                errors.append(f"[{rel_path}] Step {s_idx} must be a mapping.")
                continue
            mod = step.get('module')
            addr = step.get('address')

            if not _nonempty_string(mod):
                errors.append(f"[{rel_path}] Step {s_idx} 'module' must be a nonempty string.")
            if not isinstance(addr, str) or not re.fullmatch(r'[0-9A-Fa-f]{3}-[0-9A-Fa-f]{2,3}-[0-9A-Fa-f]{2}', addr):
                errors.append(f"[{rel_path}] Step {s_idx} invalid address {addr!r}; expected XXX-XX-XX or an extended XXX-XXX-XX block.")
            else:
                addr_upper = addr.upper()
                prefix = addr_upper.split('-')[0]
                if prefix not in STANDARD_MODULE_PREFIXES:
                    errors.append(f"[{rel_path}] Step {addr} has unregistered CAN prefix '{prefix}'; verify the module mapping before adding it to STANDARD_MODULE_PREFIXES.")
                elif _nonempty_string(mod):
                    expected = STANDARD_MODULE_PREFIXES[prefix]
                    if mod.upper().strip() not in expected:
                        errors.append(f"[{rel_path}] Module/CAN address mismatch at {addr}: Module is declared as '{mod}', but Ford CAN prefix '{prefix}' belongs to {expected}.")

            # Check for key typos (e.g. trailing colons)
            for k in step.keys():
                if isinstance(k, str) and k.endswith(':'):
                    errors.append(f"[{rel_path}] Step {addr} has key with trailing colon: '{k}'. Must be '{k[:-1]}'.")

            targets = step.get('targets', [])
            if not isinstance(targets, list) or len(targets) == 0:
                errors.append(f"[{rel_path}] Step {addr} missing or empty 'targets' list.")
                continue

            for t_idx, target in enumerate(targets):
                total_targets += 1
                location = f"[{rel_path}] Step {addr} target {t_idx}"
                if not isinstance(target, dict):
                    errors.append(f"{location} must be a mapping.")
                    continue
                mask = target.get('mask')
                t_type = target.get('type')

                normalized_mask = ' '.join(mask.split()) if isinstance(mask, str) else ''
                valid_mask = bool(re.fullmatch(r'(?:[xX*]{4} ){1,2}[xX*]{2}--', normalized_mask))
                if not valid_mask:
                    errors.append(f"{location} invalid mask {mask!r}; use 8 or 12 positions, x/* data positions, and a final -- checksum.")
                elif normalized_mask.count('*') != 1:
                    warnings.append(f"{location} [legacy-mask] mask {mask!r} has {normalized_mask.count('*')} active nibbles; atomic targets require exactly one. Review the source before changing its meaning.")
                if t_type not in ('discrete', 'continuous'):
                    errors.append(f"[{rel_path}] Step {addr} target {t_idx} invalid type: '{t_type}'. Must be 'discrete' or 'continuous'.")

                bits = target.get('bits', [])
                if not isinstance(bits, list):
                    errors.append(f"{location} 'bits' must be a list when present.")
                    bits = []

                bit_actions = {}
                for b_idx, b in enumerate(bits):
                    if not isinstance(b, dict):
                        errors.append(f"{location} bit entry {b_idx} must be a mapping.")
                        continue
                    bit, action = b.get('bit'), b.get('action')
                    valid_bit = type(bit) is int and bit in (0, 1, 2, 3)
                    valid_action = type(action) is int and action in (0, 1)
                    if not valid_bit:
                        errors.append(f"{location} bit index must be an integer 0, 1, 2, or 3; found {bit!r}.")
                    if not valid_action:
                        errors.append(f"{location} bit action must be integer 0 or 1; found {action!r}.")
                    if not any(_nonempty_string(b.get(k)) for k in ('feature_name', 'feature')):
                        errors.append(f"{location} bit {bit!r} missing nonempty 'feature_name' (or 'feature').")
                    if not any(_nonempty_string(b.get(k)) for k in ('target_state', 'state')):
                        errors.append(f"{location} bit {bit!r} missing nonempty 'target_state' (or 'state').")
                    if valid_bit and valid_action:
                        if bit in bit_actions:
                            if bit_actions[bit] != action:
                                errors.append(f"{location} has contradictory actions for bit {bit}.")
                            else:
                                warnings.append(f"{location} [duplicate-bit] repeats action {action} for bit {bit}.")
                        bit_actions[bit] = action

                if t_type == 'continuous':
                    format_counts['continuous_targets'] += 1
                    if target.get('user_input') != 'required':
                        errors.append(f"[{rel_path}] Continuous target {addr} must specify 'user_input: required'.")
                    if 'community_hex' in target:
                        errors.append(f"[{rel_path}] Continuous target {addr} has forced 'community_hex: {target['community_hex']}'. Continuous parameters must be left for user input.")
                elif t_type == 'discrete':
                    format_counts['discrete_targets'] += 1
                    chex = target.get('community_hex')
                    if not bits and 'community_hex' not in target:
                        errors.append(f"[{rel_path}] Discrete target {addr} must specify either 'bits' or 'community_hex'.")
                    single_hex = isinstance(chex, str) and bool(re.fullmatch(r'[0-9A-Fa-f]', chex))
                    if 'community_hex' in target and not single_hex:
                        if isinstance(chex, str) and (chex.lower() == 'x' or re.fullmatch(r'[0-9A-Fa-f]{2,}', chex)):
                            warnings.append(f"{location} [legacy-hex] community_hex {chex!r} is a legacy placeholder or multi-nibble value; review before converting to a single hex character.")
                        else:
                            errors.append(f"{location} community_hex {chex!r} must be a hex character '0' through 'F'.")
                    if valid_mask and normalized_mask.count('*') == 1:
                        for bit, action in bit_actions.items():
                            if single_hex and (int(chex, 16) >> bit) & 1 != action:
                                warnings.append(f"{location} [hex-bits] community_hex {chex!r} contradicts bit {bit} action {action}; confirm the authoritative target state.")
                            key = (str(addr).upper(), normalized_mask.replace(' ', '').index('*'), bit)
                            if key in written_bits and written_bits[key] != action:
                                warnings.append(f"{location} [overlapping-bit] conflicts with an earlier target at nibble {key[1]}, bit {bit}.")
                            written_bits[key] = action

    print(f"--- AsBuiltPro Recipe Validation Report (v1.1) ---")
    print(f"Scanned {len(recipe_files)} recipes ({total_steps} total module steps, {total_targets} targets).")
    print(f"Target Breakdown: {format_counts}")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")

    if errors:
        print(f"\nFAILED: {len(errors)} schema errors detected:", file=sys.stderr)
        for e in errors[:15]:
            print(f"  [ERROR] {e}", file=sys.stderr)
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors.", file=sys.stderr)
        return False

    if strict and warnings:
        print(f"\nFAILED: Strict mode rejects {len(warnings)} review warnings.", file=sys.stderr)
        return False

    print("\nSUCCESS: Recipe structural validation passed" + (f" with {len(warnings)} review warnings." if warnings else "."))
    print("Schema validation does not establish vehicle compatibility or vehicle-tested status.")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipes_dir', nargs='?', default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "recipes"))
    parser.add_argument('--strict', action='store_true', help='Fail on review warnings as well as structural errors.')
    args = parser.parse_args()
    valid = validate_catalog(args.recipes_dir, strict=args.strict)
    sys.exit(0 if valid else 1)
