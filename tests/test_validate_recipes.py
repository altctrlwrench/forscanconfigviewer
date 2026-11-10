"""Regression coverage for the public recipe validation boundary."""

import contextlib
import copy
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from scripts.validate_recipes import find_recipe_files, load_recipe, validate_catalog


VALID_RECIPE = {
    'title': 'Example feature',
    'category': 'Lighting',
    'platform': 'F-150',
    'model_years': '2021-2026',
    'steps': [{
        'module': 'BCM',
        'address': '726-63-02',
        'targets': [{
            'mask': 'xxx* xxxx xx--',
            'type': 'discrete',
            'community_hex': '0',
            'bits': [{
                'bit': 0,
                'action': 0,
                'feature_name': 'ExampleFeature',
                'target_state': 'Disabled',
            }],
        }],
    }],
    'recipe_version': '1.1',
}


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.recipe = copy.deepcopy(VALID_RECIPE)

    def validate(self, strict=False):
        (self.root / 'example.acwrecipe').write_text(
            yaml.safe_dump(self.recipe, sort_keys=False), encoding='utf-8'
        )
        return self.capture(self.root, strict)

    @staticmethod
    def capture(root, strict=False):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            passed = validate_catalog(root, strict=strict)
        return passed, output.getvalue(), errors.getvalue()

    def target(self):
        return self.recipe['steps'][0]['targets'][0]

    def test_valid_recipe_and_legacy_bit_field_names(self):
        passed, output, errors = self.validate(strict=True)
        self.assertTrue(passed, errors)
        self.assertNotIn('[WARN]', output)
        bit = self.target()['bits'][0]
        bit['feature'] = bit.pop('feature_name')
        bit['state'] = bit.pop('target_state')
        self.assertTrue(self.validate(strict=True)[0])

    def test_required_metadata_rejects_missing_blank_and_wrong_types(self):
        for field in ('title', 'platform', 'category', 'model_years'):
            for value in (None, '', '  ', 2024, [], {}):
                with self.subTest(field=field, value=value):
                    self.recipe = copy.deepcopy(VALID_RECIPE)
                    self.recipe[field] = value
                    passed, _, errors = self.validate()
                    self.assertFalse(passed)
                    self.assertIn(f"'{field}' must be a nonempty string", errors)

    def test_version_and_optional_metadata_types(self):
        for field, value in (
            ('recipe_version', 1.1), ('trim', None), ('source_sheet', []),
            ('validated', 'false'), ('validated', 1), ('status', None),
            ('status', '  '),
        ):
            with self.subTest(field=field, value=value):
                self.recipe = copy.deepcopy(VALID_RECIPE)
                self.recipe[field] = value
                self.assertFalse(self.validate()[0])
        self.recipe = copy.deepcopy(VALID_RECIPE)
        self.recipe.update(validated=False, status='untested')
        self.assertTrue(self.validate(strict=True)[0])

    def test_conflicting_verification_metadata_fails(self):
        for status in ('untested', ' Experimental '):
            with self.subTest(status=status):
                self.recipe.update(validated=True, status=status)
                passed, _, errors = self.validate()
                self.assertFalse(passed)
                self.assertIn('conflicts with status', errors)

    def test_malformed_nested_shapes_report_errors_without_crashing(self):
        cases = (
            ('steps', None), ('steps', 'bad'), ('steps', []), ('steps', ['bad']),
            ('targets', {}), ('targets', []), ('targets', [None]),
            ('bits', None), ('bits', 'bad'), ('bits', [None]),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.recipe = copy.deepcopy(VALID_RECIPE)
                owner = self.recipe if field == 'steps' else (
                    self.recipe['steps'][0] if field == 'targets' else self.target()
                )
                owner[field] = value
                passed, _, errors = self.validate()
                self.assertFalse(passed)
                self.assertIn('FAILED:', errors)

    def test_invalid_yaml_and_duplicate_keys_fail_cleanly(self):
        texts = (
            'title: [',
            yaml.safe_dump(VALID_RECIPE) + '\ntitle: Replacement\n',
            yaml.safe_dump(VALID_RECIPE).replace('action: 0', 'action: 0\n      action: 1'),
            '? [invalid, key]\n: value\n',
            '[]\n',
        )
        for text in texts:
            with self.subTest(text=text):
                (self.root / 'bad.acwrecipe').write_text(text, encoding='utf-8')
                passed, _, errors = self.capture(self.root)
                self.assertFalse(passed)
                self.assertIn('FAILED:', errors)

    def test_missing_wrong_and_unknown_module_addresses_fail(self):
        for module, address in (
            ('BCM', None), ('BCM', 'garbage'), ('BCM', '726-1-01'),
            ('BCM', '742-19-02'), ('BCM', '740-01-01'), ('B', '726-01-01'),
            ('CM', '726-01-01'), (None, '726-01-01'),
        ):
            with self.subTest(module=module, address=address):
                self.recipe = copy.deepcopy(VALID_RECIPE)
                self.recipe['steps'][0].update(module=module, address=address)
                self.assertFalse(self.validate()[0])

    def test_exact_module_aliases_and_extended_block_addresses_pass(self):
        for module, address in (
            ('BDYCM', '726-01-01'), (' bcm ', '726-01-01'),
            ('PCM', '7e0-162-02'),
        ):
            with self.subTest(module=module, address=address):
                self.recipe['steps'][0].update(module=module, address=address)
                self.assertTrue(self.validate(strict=True)[0])

    def test_malformed_masks_and_checksum_edits_fail(self):
        for mask in (None, '', 'garbage', 'xxxx xxxx xxx*', 'xxxx xxxx xx-*',
                     'xxx! xxxx xx--', '*xxx xxxx xxxx', '*xxx xxx--', 123):
            with self.subTest(mask=mask):
                self.target()['mask'] = mask
                passed, _, errors = self.validate()
                self.assertFalse(passed)
                self.assertIn('invalid mask', errors)

    def test_short_rows_and_uppercase_untouched_positions_pass(self):
        for mask in ('*xxx xx--', 'XXX* XXXX XX--'):
            with self.subTest(mask=mask):
                self.target()['mask'] = mask
                self.assertTrue(self.validate(strict=True)[0])

    def test_legacy_masks_are_warnings_or_strict_failures(self):
        for mask in ('**** xxxx xx--', 'xxxx xxxx xx--'):
            with self.subTest(mask=mask):
                self.target()['mask'] = mask
                passed, output, errors = self.validate()
                self.assertTrue(passed, errors)
                self.assertEqual(1, output.count('[legacy-mask]'))
                passed, _, errors = self.validate(strict=True)
                self.assertFalse(passed)
                self.assertIn('Strict mode rejects 1 review warnings', errors)

    def test_invalid_community_hex_fails(self):
        for value in ('ZZ', '', None, 0, True):
            with self.subTest(value=value):
                self.target()['community_hex'] = value
                self.assertFalse(self.validate()[0])

    def test_legacy_hex_values_warn_without_rewriting_the_source(self):
        for value in ('x', '00'):
            with self.subTest(value=value):
                self.target()['community_hex'] = value
                passed, output, errors = self.validate()
                self.assertTrue(passed, errors)
                self.assertEqual(1, output.count('[legacy-hex]'))
                self.assertEqual(value, load_recipe(self.root / 'example.acwrecipe')['steps'][0]['targets'][0]['community_hex'])
                self.assertFalse(self.validate(strict=True)[0])

    def test_bits_require_actual_integers_and_nonempty_feature_state(self):
        for field, value in (
            ('bit', True), ('bit', 0.0), ('bit', 4), ('bit', None),
            ('action', False), ('action', 0.0), ('action', 2),
            ('feature_name', ''), ('target_state', None),
        ):
            with self.subTest(field=field, value=value):
                self.recipe = copy.deepcopy(VALID_RECIPE)
                self.target()['bits'][0][field] = value
                self.assertFalse(self.validate()[0])

    def test_hex_bit_disagreement_warns_and_strict_rejects(self):
        self.target()['community_hex'] = '1'
        passed, output, errors = self.validate()
        self.assertTrue(passed, errors)
        self.assertEqual(1, output.count('[hex-bits]'))
        self.assertFalse(self.validate(strict=True)[0])

    def test_contradictory_duplicate_bit_fails_and_identical_duplicate_warns(self):
        bit = copy.deepcopy(self.target()['bits'][0])
        self.target()['bits'].append(bit)
        passed, output, errors = self.validate()
        self.assertTrue(passed, errors)
        self.assertEqual(1, output.count('[duplicate-bit]'))
        bit['action'] = 1
        passed, _, errors = self.validate()
        self.assertFalse(passed)
        self.assertIn('contradictory actions for bit 0', errors)

    def test_conflicting_bits_across_targets_warn(self):
        target = copy.deepcopy(self.target())
        target['community_hex'] = '1'
        target['bits'][0]['action'] = 1
        self.recipe['steps'][0]['targets'].append(target)
        passed, output, errors = self.validate()
        self.assertTrue(passed, errors)
        self.assertEqual(1, output.count('[overlapping-bit]'))
        self.assertFalse(self.validate(strict=True)[0])

    def test_continuous_values_require_input_and_reject_forced_hex(self):
        self.recipe['steps'][0]['targets'] = [{
            'mask': '*xxx xxxx xx--', 'type': 'continuous', 'user_input': 'required',
        }]
        self.assertTrue(self.validate(strict=True)[0])
        self.target()['community_hex'] = '0'
        self.assertFalse(self.validate()[0])
        self.target().pop('community_hex')
        self.target().pop('user_input')
        self.assertFalse(self.validate()[0])

    def test_empty_catalog_fails_and_discovery_is_deterministic(self):
        self.assertFalse(self.capture(self.root)[0])
        (self.root / 'b.yaml').write_text('title: b', encoding='utf-8')
        (self.root / 'a.acwrecipe').write_text('title: a', encoding='utf-8')
        (self.root / 'README.md').write_text('ignored', encoding='utf-8')
        self.assertEqual(['a.acwrecipe', 'b.yaml'], [Path(p).name for p in find_recipe_files(self.root)])

    def test_strict_cli_returns_failure_for_review_warnings(self):
        self.target()['mask'] = '**** xxxx xx--'
        self.validate()
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'validate_recipes.py'
        result = subprocess.run(
            [sys.executable, str(script), str(self.root), '--strict'],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn('Strict mode rejects 1 review warnings', result.stderr)

    def test_current_catalog_remains_structurally_valid(self):
        recipes = Path(__file__).resolve().parents[1] / 'recipes'
        passed, output, errors = self.capture(recipes)
        self.assertTrue(passed, errors)
        self.assertIn('Schema validation does not establish vehicle compatibility', output)


if __name__ == '__main__':
    unittest.main()
