"""Offline publication safeguards; no external service or application database."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('publication', Path(__file__).parents[1] / 'prepare_publication.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicationTests(unittest.TestCase):
    def test_environment_excluded_template_included(self):
        for name in ['.env', '.env.local', '.env.production']:
            self.assertEqual(module.classify(Path(name))[0], 'exclude')
        self.assertEqual(module.classify(Path('.env.example'))[0], 'include')

    def test_lockfiles_preserved_runtime_lock_excluded(self):
        for name in ['package-lock.json', 'requirements.lock.txt']:
            self.assertEqual(module.classify(Path(name))[0], 'include')
        self.assertEqual(module.classify(Path('runner.lock'))[0], 'exclude')

    def test_media_not_implicitly_cleared(self):
        for name in ['safe.jpg', 'government.pdf', 'screen.png']:
            self.assertEqual(module.classify(Path(name))[0], 'hold')

    def test_secret_findings_do_not_echo_value(self):
        secret = b'local-synthetic-secret-12345'
        result = module.findings(secret, [secret])
        self.assertEqual(result, ['configured_secret_match'])
        self.assertNotIn(secret.decode(), str(result))

    def test_private_key_detection(self):
        marker = b'-----BEGIN ' + b'PRIVATE KEY-----'
        self.assertIn('private_key', module.findings(marker, []))

    def test_privacy_redaction_keeps_json_and_annotations(self):
        original = {'reviewer': 'Example Reviewer', 'evidence': r'[LOCAL_HOME]\archive.json',
                    'ground_truth_hazards': ['housekeeping'], 'ambiguous': True, 'score': 12}
        result = json.loads(module.sanitize(json.dumps(original).encode(), ['Example Reviewer']))
        self.assertEqual(result['reviewer'], 'REVIEWER_1')
        self.assertNotIn('Example User', result['evidence'])
        for key in ['ground_truth_hazards', 'ambiguous', 'score']:
            self.assertEqual(result[key], original[key])

    def test_source_code_unchanged(self):
        data = b'def risk(a, b):\n    return a * b\n'
        self.assertEqual(module.sanitize(data, []), data)

    def test_unknown_binary_held(self):
        self.assertEqual(module.classify(Path('unreviewed.dat'))[0], 'hold')

    def test_source_byte_order_mark_preserved(self):
        data = b'\xef\xbb\xbf' + b'print(1)\r\n'
        self.assertEqual(module.sanitize(data, []), data)


if __name__ == '__main__':
    unittest.main()
