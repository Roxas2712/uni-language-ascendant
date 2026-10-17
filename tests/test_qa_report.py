"""Reject stale or partial gameplay evidence before publishing the report."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_ptbr_report as report


class GameplayEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('tests', 'mod/profiles', 'qa'):
            (self.root / directory).mkdir(parents=True)
        files = {
            'mod/main.lua': 'return true',
            'mod/catalog.lua': "return {{game='ruby',language='pt-BR',profile='profiles/ruby.lua'}}",
            'mod/profiles/ruby.lua': 'return {}',
            'mod/profiles/emerald.lua': 'return {}',
            'tests/driver.lua': "return assert(loadfile(root..'/ptbr_nurse_live.lua'))()",
            'tests/ptbr_nurse_live.lua': 'return function() end',
        }
        for name, contents in files.items():
            (self.root / name).write_text(contents)
        self.patch = patch.multiple(report, ROOT=self.root, QA=self.root / 'qa')
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.clear_caches()
        self.addCleanup(self.clear_caches)
        self.log = self.root / 'qa/check.log'
        self.log.write_text('LANGUAGE_LIVE_OK\n')
        self.evidence = {
            'game': 'ruby', 'language': 'pt-BR', 'passed': True,
            'driver': 'driver.lua',
            'driver_sha256': self.digest('tests/driver.lua'),
            'helpers_sha256': {'ptbr_nurse_live.lua': self.digest('tests/ptbr_nurse_live.lua')},
            'runtime_sha256': report.runtime_hashes(),
            'log_sha256': self.digest('qa/check.log'),
        }
        self.save()

    @staticmethod
    def clear_caches():
        report.runtime_hashes.cache_clear()
        report.selected_profiles.cache_clear()

    def digest(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def save(self):
        (self.root / 'qa/check.evidence.json').write_text(json.dumps(self.evidence))

    def test_current_run_is_accepted(self):
        self.assertIsNotNone(report.proof('check'))

    def test_changed_dialogue_helper_requires_new_run(self):
        (self.root / 'tests/ptbr_nurse_live.lua').write_text('return function() assert(false) end')
        self.assertIsNone(report.proof('check'))

    def test_changed_driver_requires_new_run(self):
        (self.root / 'tests/driver.lua').write_text('return false')
        self.assertIsNone(report.proof('check'))

    def test_unloaded_other_game_profile_does_not_invalidate_run(self):
        (self.root / 'mod/profiles/emerald.lua').write_text('return {new=true}')
        self.clear_caches()
        self.assertIsNotNone(report.proof('check'))

    def test_selected_profile_change_requires_new_run(self):
        (self.root / 'mod/profiles/ruby.lua').write_text('return {new=true}')
        self.clear_caches()
        self.assertIsNone(report.proof('check'))

    def test_modified_log_is_rejected(self):
        self.log.write_text('LANGUAGE_LIVE_OK\nmodified\n')
        self.assertIsNone(report.proof('check'))

    def test_runtime_failure_cannot_be_hidden_by_success_marker(self):
        self.log.write_text('LANGUAGE_LIVE_OK\nhot-path pcall failed\n')
        self.evidence['log_sha256'] = self.digest('qa/check.log')
        self.save()
        self.assertIsNone(report.proof('check'))

    def test_focused_sample_is_not_full_scenario_evidence(self):
        self.evidence['test_options'] = {'QA_FRONTIER_SAMPLE': '1'}
        self.save()
        self.assertIsNone(report.proof('check'))


if __name__ == '__main__':
    unittest.main()
