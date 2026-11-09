"""Regression coverage for catalog publication and verification metadata."""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts import compile_catalog as compiler


def recipe(**metadata):
    data = {
        'title': 'Example Feature',
        'category': 'Lighting',
        'platform': 'F-150',
        'model_years': '2021-2026',
        'trim': 'All',
        'steps': [{
            'module': 'BCM',
            'address': '726-63-02',
            'targets': [{
                'mask': 'xxx* xxxx xx--',
                'community_hex': '1',
                'type': 'discrete',
                'bits': [{
                    'bit': 0, 'action': 1,
                    'feature_name': 'ExampleParameter', 'target_state': 'Enabled',
                }],
            }],
        }],
    }
    data.update(metadata)
    data['recipe_version'] = '1.1'
    return data


class CompileCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.recipes = self.root / 'recipes'
        self.recipes.mkdir()
        self.dist = self.root / 'dist'

    def write_recipe(self, name, data):
        path = self.recipes / name
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
        return path

    def compile(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return compiler.compile_catalog(self.recipes, self.dist, **kwargs)

    def test_verification_flags_survive_both_catalog_views(self):
        for name, metadata in (
            ('true.acwrecipe', {'validated': True}),
            ('false.acwrecipe', {'validated': False}),
            ('unknown.acwrecipe', {}),
            ('untested.acwrecipe', {'status': 'untested'}),
        ):
            self.write_recipe(name, recipe(**metadata))

        catalog = self.compile()
        self.assertEqual(catalog['summary']['schema_valid_recipes'], 4)
        self.assertEqual(catalog['summary']['validated_recipes'], 1)
        self.assertEqual(catalog['summary']['unverified_recipes'], 3)
        self.assertEqual(catalog['summary']['untested_recipes'], 1)
        for view in (catalog['recipes'], catalog['features'][0]['platforms']['F-150']):
            by_file = {entry['file']: entry for entry in view}
            self.assertIs(by_file['true.acwrecipe']['validated'], True)
            self.assertIs(by_file['false.acwrecipe']['validated'], False)
            self.assertNotIn('validated', by_file['unknown.acwrecipe'])
            self.assertEqual(by_file['untested.acwrecipe']['status'], 'untested')
        published = json.loads((self.dist / 'master_recipes.json').read_text())
        self.assertEqual(published, catalog)

    def test_compilation_is_deterministic_and_keeps_recipe_values(self):
        original = recipe(validated=False)
        original['notes'] = 'Keep the source instructions.'
        path = self.write_recipe('example.acwrecipe', original)
        original_text = path.read_text()
        before = copy.deepcopy(original)
        self.compile()
        first = (self.dist / 'master_recipes.json').read_bytes()
        self.compile()
        self.assertEqual(first, (self.dist / 'master_recipes.json').read_bytes())
        self.assertEqual(path.read_text(), original_text)
        compiled = json.loads(first)['recipes'][0]
        self.assertEqual(compiled['steps'], before['steps'])
        self.assertEqual(compiled['notes'], before['notes'])

    def test_untested_count_normalizes_case_and_whitespace_without_rewriting(self):
        self.write_recipe('example.acwrecipe', recipe(status=' UnTeStEd '))
        catalog = self.compile()
        self.assertEqual(catalog['summary']['untested_recipes'], 1)
        self.assertEqual(catalog['recipes'][0]['status'], ' UnTeStEd ')

    def test_invalid_recipe_cannot_replace_last_good_catalog(self):
        self.write_recipe('good.acwrecipe', recipe())
        self.compile()
        previous = (self.dist / 'master_recipes.json').read_bytes()
        invalid = recipe()
        invalid['steps'][0]['targets'][0]['mask'] = 'xxxx xxxx xxx*'
        self.write_recipe('invalid.acwrecipe', invalid)
        with self.assertRaises(SystemExit) as raised:
            self.compile()
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(previous, (self.dist / 'master_recipes.json').read_bytes())

    def test_read_failure_never_publishes_a_partial_catalog(self):
        self.write_recipe('good.acwrecipe', recipe())
        self.compile()
        previous = (self.dist / 'master_recipes.json').read_bytes()
        # Simulate a file becoming unreadable between validation and compilation.
        with patch.object(compiler, 'load_recipe', side_effect=OSError('file unavailable')):
            with self.assertRaisesRegex(ValueError, 'Cannot compile'):
                self.compile()
        self.assertEqual(previous, (self.dist / 'master_recipes.json').read_bytes())

    def test_strict_build_refuses_legacy_warnings(self):
        legacy = recipe()
        target = legacy['steps'][0]['targets'][0]
        target['mask'] = 'xxxx xxxx **--'
        target['community_hex'] = '00'
        target.pop('bits')
        self.write_recipe('legacy.acwrecipe', legacy)
        self.assertEqual(self.compile()['summary']['schema_valid_recipes'], 1)
        previous = (self.dist / 'master_recipes.json').read_bytes()
        with self.assertRaises(SystemExit):
            self.compile(strict=True)
        self.assertEqual(previous, (self.dist / 'master_recipes.json').read_bytes())

    def test_skipped_checks_do_not_claim_schema_validation(self):
        self.write_recipe('example.acwrecipe', recipe())
        catalog = self.compile(skip_validation=True)
        self.assertIsNone(catalog['summary']['schema_valid_recipes'])
        self.assertEqual(catalog['summary']['validated_recipes'], 0)


if __name__ == '__main__':
    unittest.main()
