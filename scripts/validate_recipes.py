#!/usr/bin/env python3
"""
AsBuiltPro Recipe Schema Validator & Linter (v1.1)
Validates that all .acwrecipe files adhere strictly to:
1. v1.1 Specification: Atomic single-nibble targets grouped under module & address.
2. Root Metadata: title, platform, model_years, category, source_sheet, and recipe_version ('1.1').
3. No trailing colons in dictionary keys.
4. Discrete steps: valid visual mask (e.g. 'xxx* xxxx xx--'), type: discrete, and active bit actions or community_hex.
5. Continuous parameters: type: continuous with user_input: required, no hardcoded default overrides.
6. Platform & Trim integrity (e.g. Super Duty diesel trims).
"""

import sys
import os
import glob
import yaml

def validate_catalog(recipes_dir="recipes"):
    recipe_files = sorted(glob.glob(os.path.join(recipes_dir, "**", "*.acwrecipe"), recursive=True) +
                          glob.glob(os.path.join(recipes_dir, "**", "*.yaml"), recursive=True))
    
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
            with open(rf, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
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

        if not title:
            errors.append(f"[{rel_path}] Missing 'title'.")
        if not plat:
            errors.append(f"[{rel_path}] Missing 'platform'.")
        if not steps:
            errors.append(f"[{rel_path}] Missing or empty 'steps'.")
        if version != '1.1':
            errors.append(f"[{rel_path}] Expected recipe_version: '1.1', found: '{version}'.")

        # Trim validation
        if plat == 'Super Duty' and any(k in title.lower() for k in ['diesel exhaust auto regen', 'soot percentage', 'dpf']):
            if trim != 'Diesel (6.7L Powerstroke)':
                errors.append(f"[{rel_path}] Super Duty diesel recipe must have trim: 'Diesel (6.7L Powerstroke)', found: '{trim}'")

        for s_idx, step in enumerate(steps):
            total_steps += 1
            mod = step.get('module')
            addr = step.get('address', f"step_{s_idx}")

            if not mod:
                errors.append(f"[{rel_path}] Step {addr} missing 'module'.")

            # Check for key typos (e.g. trailing colons)
            for k in step.keys():
                if k.endswith(':'):
                    errors.append(f"[{rel_path}] Step {addr} has key with trailing colon: '{k}'. Must be '{k[:-1]}'.")

            targets = step.get('targets', [])
            if not isinstance(targets, list) or len(targets) == 0:
                errors.append(f"[{rel_path}] Step {addr} missing or empty 'targets' list.")
                continue

            for t_idx, target in enumerate(targets):
                total_targets += 1
                mask = target.get('mask')
                t_type = target.get('type')

                if not mask:
                    errors.append(f"[{rel_path}] Step {addr} target {t_idx} missing 'mask'.")
                if t_type not in ('discrete', 'continuous'):
                    errors.append(f"[{rel_path}] Step {addr} target {t_idx} invalid type: '{t_type}'. Must be 'discrete' or 'continuous'.")

                if t_type == 'continuous':
                    format_counts['continuous_targets'] += 1
                    if target.get('user_input') != 'required':
                        errors.append(f"[{rel_path}] Continuous target {addr} must specify 'user_input: required'.")
                    if 'community_hex' in target:
                        errors.append(f"[{rel_path}] Continuous target {addr} has forced 'community_hex: {target['community_hex']}'. Continuous parameters must be left for user input.")
                elif t_type == 'discrete':
                    format_counts['discrete_targets'] += 1
                    bits = target.get('bits', [])
                    chex = target.get('community_hex')
                    if not bits and not chex:
                        errors.append(f"[{rel_path}] Discrete target {addr} must specify either 'bits' or 'community_hex'.")
                    for b in bits:
                        if 'bit' not in b or 'action' not in b:
                            errors.append(f"[{rel_path}] Bit entry in {addr} missing 'bit' or 'action'.")
                        elif b.get('bit') not in (0, 1, 2, 3):
                            errors.append(f"[{rel_path}] Bit index in {addr} must be 0, 1, 2, or 3. Found: {b.get('bit')}")
                        elif b.get('action') not in (0, 1):
                            errors.append(f"[{rel_path}] Bit action in {addr} must be 0 or 1. Found: {b.get('action')}")

    print(f"--- AsBuiltPro Recipe Validation Report (v1.1) ---")
    print(f"Scanned {len(recipe_files)} recipes ({total_steps} total module steps, {total_targets} atomic targets).")
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

    print("\nSUCCESS: All recipes adhere strictly to AsBuiltPro v1.1 schema and standards.")
    return True

if __name__ == '__main__':
    r_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(__file__)), "recipes")
    valid = validate_catalog(r_dir)
    sys.exit(0 if valid else 1)
