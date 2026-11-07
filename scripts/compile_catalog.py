#!/usr/bin/env python3
"""
Compile AsBuiltPro Recipe Catalog (v1.1)
Scans recipes/**/*.acwrecipe, validates v1.1 structure,
and produces a lean, pure dist/master_recipes.json for AsBuiltPro runtime.
"""

import os
import sys
import json
import glob
from collections import defaultdict
import yaml

try:
    from validate_recipes import validate_catalog
except ImportError:
    from scripts.validate_recipes import validate_catalog

def compile_catalog(recipes_dir="recipes", dist_dir="dist", skip_validation=False):
    if not skip_validation:
        print(f"Running v1.1 recipe schema validation on '{recipes_dir}'...")
        if not validate_catalog(recipes_dir):
            print("Catalog compilation aborted due to schema validation failures.", file=sys.stderr)
            sys.exit(1)
            
    os.makedirs(dist_dir, exist_ok=True)
    
    recipe_files = glob.glob(os.path.join(recipes_dir, "**", "*.acwrecipe"), recursive=True) + \
                   glob.glob(os.path.join(recipes_dir, "**", "*.yaml"), recursive=True)
    recipe_files = sorted(list(set(recipe_files)))
    print(f"\nCompiling {len(recipe_files)} recipe files from {recipes_dir}/...")
    
    validated_recipes = []
    canonical_features = defaultdict(lambda: {
        'title': '',
        'category': '',
        'platforms': {}
    })
    
    for yf in recipe_files:
        try:
            with open(yf, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error parsing {yf}: {e}", file=sys.stderr)
            continue
            
        if not isinstance(data, dict):
            continue
            
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
            'source_sheet': data.get('source_sheet', ''),
            'notes': data.get('notes'),
            'steps': data.get('steps', []),
            'recipe_version': data.get('recipe_version', '1.1')
        }
        
        # Omit None fields
        clean_recipe = {k: v for k, v in clean_recipe.items() if v is not None}
        validated_recipes.append(clean_recipe)
        
        # Group into canonical feature map for AsBuiltPro UI
        cf = canonical_features[title]
        cf['title'] = title
        cf['category'] = category
        
        if platform not in cf['platforms']:
            cf['platforms'][platform] = []
            
        cf['platforms'][platform].append(clean_recipe)
        
    catalog = {
        'version': '1.1.0',
        'generated_at': None,
        'summary': {
            'total_files': len(recipe_files),
            'validated_recipes': len(validated_recipes),
            'unique_canonical_features': len(canonical_features),
            'supported_platforms': sorted(list(set(r['platform'] for r in validated_recipes)))
        },
        'features': [canonical_features[k] for k in sorted(canonical_features.keys())],
        'recipes': validated_recipes
    }
    
    json_path = os.path.join(dist_dir, "master_recipes.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2)
        
    print(f"Successfully compiled {len(validated_recipes)} recipes across {len(canonical_features)} unique canonical features.")
    print(f"Output saved to: {json_path} ({os.path.getsize(json_path):,} bytes)")

if __name__ == '__main__':
    r_dir = sys.argv[1] if len(sys.argv) > 1 else "recipes"
    d_dir = sys.argv[2] if len(sys.argv) > 2 else "dist"
    compile_catalog(r_dir, d_dir)
