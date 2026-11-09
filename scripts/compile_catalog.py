#!/usr/bin/env python3
"""
Compile AsBuiltPro Recipe Catalog (v1.1)
Scans recipes/**/*.acwrecipe, validates v1.1 structure,
and produces a lean, pure dist/master_recipes.json for AsBuiltPro runtime.
"""

import argparse
import json
import os
import sys
import tempfile
from collections import defaultdict
import yaml

try:
    from validate_recipes import find_recipe_files, load_recipe, validate_catalog
except ImportError:
    from scripts.validate_recipes import find_recipe_files, load_recipe, validate_catalog


def compile_catalog(recipes_dir="recipes", dist_dir="dist", skip_validation=False, strict=False):
    if not skip_validation:
        print(f"Running v1.1 recipe schema validation on '{recipes_dir}'...")
        if not validate_catalog(recipes_dir, strict=strict):
            print("Catalog compilation aborted due to schema validation failures.", file=sys.stderr)
            sys.exit(1)

    recipe_files = find_recipe_files(recipes_dir)
    print(f"\nCompiling {len(recipe_files)} recipe files from {recipes_dir}/...")

    recipes = []
    canonical_features = defaultdict(lambda: {
        'title': '',
        'category': '',
        'platforms': {}
    })
    
    for yf in recipe_files:
        try:
            data = load_recipe(yf)
        except (OSError, yaml.YAMLError) as e:
            raise ValueError(f"Cannot compile {yf}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(f"Cannot compile {yf}: root must be a dictionary.")
            
        rel_path = os.path.relpath(yf, recipes_dir).replace('\\', '/')
        title = data.get('title', 'Unknown')
        platform = data.get('platform', 'Unknown')
        category = data.get('category', 'General')
        
        # 1:1 recipe object matching the pure .acwrecipe schema
        clean_recipe = {
            'file': rel_path,
            'title': title,
            'raw_community_title': data.get('raw_community_title', ''),
            'category': category,
            'platform': platform,
            'model_years': str(data.get('model_years', '')),
            'trim': data.get('trim', 'All'),
            'validated': data.get('validated'),
            'status': data.get('status'),
            'source_sheet': data.get('source_sheet', ''),
            'notes': data.get('notes'),
            'steps': data.get('steps', []),
            'recipe_version': data.get('recipe_version', '1.1')
        }
        
        # Omit None fields
        clean_recipe = {k: v for k, v in clean_recipe.items() if v is not None}
        recipes.append(clean_recipe)
        
        # Group into canonical feature map for AsBuiltPro UI
        cf = canonical_features[title]
        cf['title'] = title
        cf['category'] = category
        
        if platform not in cf['platforms']:
            cf['platforms'][platform] = []
            
        cf['platforms'][platform].append(clean_recipe)
        
    # Passing a structural check is not evidence of a working vehicle test.
    # Missing verification metadata stays unknown; never promote it to True.
    vehicle_validated = sum(r.get('validated') is True for r in recipes)
    catalog = {
        'version': '1.1.0',
        'generated_at': None,
        'summary': {
            'total_files': len(recipe_files),
            'schema_valid_recipes': len(recipes) if not skip_validation else None,
            'validated_recipes': vehicle_validated,
            'unverified_recipes': len(recipes) - vehicle_validated,
            'untested_recipes': sum(r.get('status', '').strip().lower() == 'untested' for r in recipes),
            'unique_canonical_features': len(canonical_features),
            'supported_platforms': sorted(set(r['platform'] for r in recipes))
        },
        'features': [canonical_features[k] for k in sorted(canonical_features.keys())],
        'recipes': recipes
    }
    
    # Serialize before opening the output, then replace it atomically. A failed
    # build must leave the previous complete catalog available to consumers.
    serialized = json.dumps(catalog, indent=2)
    os.makedirs(dist_dir, exist_ok=True)
    json_path = os.path.join(dist_dir, "master_recipes.json")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=dist_dir,
                                         prefix='.master_recipes-', suffix='.tmp',
                                         delete=False) as f:
            temporary_path = f.name
            f.write(serialized)
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, json_path)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)

    print(f"Successfully compiled {len(recipes)} recipes across {len(canonical_features)} unique canonical features.")
    print(f"Output saved to: {json_path} ({os.path.getsize(json_path):,} bytes)")
    return catalog

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipes_dir', nargs='?', default='recipes')
    parser.add_argument('dist_dir', nargs='?', default='dist')
    parser.add_argument('--strict', action='store_true', help='Fail on recipe review warnings too.')
    args = parser.parse_args()
    try:
        compile_catalog(args.recipes_dir, args.dist_dir, strict=args.strict)
    except (OSError, ValueError, TypeError) as e:
        print(f"Catalog compilation failed: {e}", file=sys.stderr)
        sys.exit(1)
