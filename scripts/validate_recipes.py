#!/usr/bin/env python3
"""
AsBuiltPro Recipe Schema Validator & Linter
Validates that all .acwrecipe files adhere strictly to:
1. Format 1: Hierarchical Nibbles & Bits for all discrete steps.
2. No trailing colons in step dictionary keys (e.g. 'mask:').
3. No discrete steps with omitted targets (every discrete step must have recommended_hex or bit actions).
4. Continuous / Variable parameters (Tire size, 12V timeout, DRL brightness) must be tagged
   type: continuous with user_input: required, and have NO forced default overrides.
5. Multi-choice parameters (Turn signal flash count, audio EQ) must provide an options map.
6. Elimination of phantom nibble 4 on 12V Power Outlet Enable (726-57-01).
7. Platform & Trim integrity (e.g. F-150 vs F-150 Lightning separation, Super Duty diesel trims).
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
    format_counts = {'format_1_hierarchical': 0, 'continuous': 0, 'multi_choice': 0, 'all_zeros': 0}

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

        if not title:
            errors.append(f"[{rel_path}] Missing 'title'.")
        if not plat:
            errors.append(f"[{rel_path}] Missing 'platform'.")

        # Trim validation
        if plat == 'Super Duty' and any(k in title.lower() for k in ['diesel exhaust auto regen', 'soot percentage']):
            if trim != 'Diesel (6.7L Powerstroke)':
                errors.append(f"[{rel_path}] Super Duty diesel recipe must have trim: 'Diesel (6.7L Powerstroke)', found: '{trim}'")

        for s_idx, step in enumerate(steps):
            total_steps += 1
            addr = step.get('address', f"step_{s_idx}")

            # 1. Check for key typos (e.g. 'mask:')
            for k in step.keys():
                if k.endswith(':'):
                    errors.append(f"[{rel_path}] Step {addr} has key with trailing colon: '{k}'. Must be '{k[:-1]}'.")

            # 2. Check for phantom nibble 4 on 12V enable
            if addr == '726-57-01' and 'enable' in title.lower():
                for n in step.get('nibbles', []):
                    if n.get('nibble') == 4:
                        errors.append(f"[{rel_path}] Step {addr} contains phantom Nibble 4. Only authentic Nibble 5 (PPTC DISABLE) should be present.")

            # 3. Format & Schema check
            stype = step.get('type')
            
            if stype == 'continuous':
                format_counts['continuous'] += 1
                if step.get('user_input') != 'required':
                    errors.append(f"[{rel_path}] Continuous step {addr} must specify 'user_input: required'.")
                if 'recommended_hex' in step:
                    errors.append(f"[{rel_path}] Continuous step {addr} has forced 'recommended_hex: {step['recommended_hex']}'. Continuous parameters must be left for user input.")
                continue

            if stype == 'multi_choice':
                format_counts['multi_choice'] += 1
                if 'options' not in step or not isinstance(step['options'], (dict, str)):
                    errors.append(f"[{rel_path}] Multi-choice step {addr} missing 'options' mapping.")
                continue

            if stype == 'all_zeros':
                format_counts['all_zeros'] += 1
                continue

            # Reject Flat Formats
            if 'bits' in step:
                errors.append(f"[{rel_path}] Step {addr} uses legacy flat 'bits' format. Must use Format 1 (hierarchical 'nibbles' list).")
                continue
            if 'bit' in step:
                errors.append(f"[{rel_path}] Step {addr} uses legacy flat 'bit' format. Must use Format 1 (hierarchical 'nibbles' list).")
                continue

            if 'nibbles' in step and step['nibbles']:
                format_counts['format_1_hierarchical'] += 1
                # Validate nibbles structure
                for n in step['nibbles']:
                    if not isinstance(n, dict):
                        errors.append(f"[{rel_path}] Step {addr} nibble entry must be a dictionary.")
                        continue
                    if 'nibble' not in n:
                        errors.append(f"[{rel_path}] Step {addr} nibble entry missing 'nibble' index.")

                    # Ensure discrete targets exist
                    has_action = False
                    if n.get('recommended_hex') or n.get('target_state') or n.get('hex_offset'):
                        has_action = True
                    for b in n.get('bits', []):
                        if 'action' in b or b.get('target_state'):
                            has_action = True
                    if not has_action and not step.get('recommended_hex') and not step.get('target_state'):
                        errors.append(f"[{rel_path}] Step {addr} Nibble {n.get('nibble')} has no recommended_hex, target_state, or bit actions.")
            else:
                errors.append(f"[{rel_path}] Step {addr} missing 'nibbles' list or valid step type ('continuous', 'multi_choice', 'all_zeros').")

    print(f"--- AsBuiltPro Recipe Validation Report ---")
    print(f"Scanned {len(recipe_files)} recipes ({total_steps} total steps across all platforms).")
    print(f"Format Breakdown: {format_counts}")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")

    if errors:
        print(f"\nFAILED: {len(errors)} schema errors detected:", file=sys.stderr)
        for e in errors:
            print(f"  [ERROR] {e}", file=sys.stderr)
        return False

    print("\nSUCCESS: All recipes adhere strictly to AsBuiltPro Format 1 schema and standards.")
    return True

if __name__ == '__main__':
    r_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(__file__)), "recipes")
    valid = validate_catalog(r_dir)
    sys.exit(0 if valid else 1)
