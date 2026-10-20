#!/usr/bin/env python3
"""
Compile AsBuiltPro Recipe Catalog
Scans recipes/**/*.yaml, validates structure, filters for validated items,
and produces dist/master_recipes.json.
"""

import os
import sys
import json
import glob
from collections import defaultdict
import yaml

def compile_catalog(recipes_dir="recipes", dist_dir="dist"):
    os.makedirs(dist_dir, exist_ok=True)
    
    recipe_files = glob.glob(os.path.join(recipes_dir, "**", "*.acwrecipe"), recursive=True) + glob.glob(os.path.join(recipes_dir, "**", "*.yaml"), recursive=True)
    recipe_files = sorted(list(set(recipe_files)))
    print(f"Found {len(recipe_files)} recipe files in {recipes_dir}/")
    
    validated_recipes = []
    unvalidated_recipes = []
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
            
        title = data.get('title', 'Unknown')
        platform = data.get('platform', 'Unknown')
        category = data.get('category', 'General')
        is_validated = data.get('validated', False)
        
        entry = {
            'file': os.path.relpath(yf, recipes_dir).replace('\\', '/'),
            'title': title,
            'raw_community_title': data.get('raw_community_title', ''),
            'category': category,
            'platform': platform,
            'model_years': data.get('model_years', ''),
            'trim': data.get('trim', 'All'),
            'validated': is_validated,
            'verified_by': data.get('verified_by', ''),
            'forscan_menu': data.get('forscan_menu'),
            'prerequisites': data.get('prerequisites'),
            'post_procedure': data.get('post_procedure'),
            'warnings': data.get('warnings'),
            'steps': data.get('steps', [])
        }
        
        # Clean None fields
        clean_entry = {k: v for k, v in entry.items() if v is not None}
        
        if is_validated:
            validated_recipes.append(clean_entry)
            
            # Group into canonical feature map for As Built Pro
            cf = canonical_features[title]
            cf['title'] = title
            cf['category'] = category
            
            plat_key = platform
            if plat_key not in cf['platforms']:
                cf['platforms'][plat_key] = []
                
            cf['platforms'][plat_key].append({
                'model_years': data.get('model_years', ''),
                'trim': data.get('trim', 'All'),
                'steps': data.get('steps', []),
                'source_file': clean_entry['file'],
                'forscan_menu': data.get('forscan_menu'),
                'prerequisites': data.get('prerequisites'),
                'post_procedure': data.get('post_procedure'),
                'warnings': data.get('warnings')
            })
        else:
            unvalidated_recipes.append(clean_entry)
            
    # Structure final release payload
    catalog = {
        'version': '1.0.0',
        'generated_at': None,
        'summary': {
            'total_files': len(recipe_files),
            'validated_recipes': len(validated_recipes),
            'pending_recipes': len(unvalidated_recipes),
            'unique_canonical_features': len(canonical_features),
            'supported_platforms': sorted(list(set(r['platform'] for r in validated_recipes)))
        },
        'features': [canonical_features[k] for k in sorted(canonical_features.keys())],
        'recipes': validated_recipes
    }
    
    # Write master JSON
    json_path = os.path.join(dist_dir, "master_recipes.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2)
        
    print(f"Compiled {len(validated_recipes)} validated recipes ({len(canonical_features)} unique features).")
    print(f"Output saved to: {json_path} ({os.path.getsize(json_path):,} bytes)")

if __name__ == '__main__':
    r_dir = sys.argv[1] if len(sys.argv) > 1 else "recipes"
    d_dir = sys.argv[2] if len(sys.argv) > 2 else "dist"
    compile_catalog(r_dir, d_dir)
