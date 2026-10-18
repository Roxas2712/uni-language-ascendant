"""Run the combined release regression gate in isolated LOVE identities.

Set LOVE and LUAJIT. Requires the private, exact-hash QA inputs documented by
existing profile runners. No ROMs or generated game content are published.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = ('units', 'gba', 'european', 'ptbr', 'picker', 'asian')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-suite', choices=SUITES, default='units')
    args = parser.parse_args()
    assert os.environ.get('LOVE') and os.environ.get('LUAJIT'), 'Set LOVE and LUAJIT'
    active = set(SUITES[SUITES.index(args.from_suite):])

    def run(script, *arguments, extra=None):
        print('RELEASE_CHECK', script, *arguments, flush=True)
        subprocess.run([sys.executable, str(ROOT / 'tests' / script), *arguments],
                       cwd=ROOT, env=dict(os.environ, **(extra or {})), check=True)

    if 'units' in active:
        run('run_merged_units.py')
    if 'gba' in active:
        run('run_gba_completion.py')
        run('run_gba_completion.py', 'firered_de', 'leafgreen_de', 'ruby_de',
            'sapphire_de', 'emerald_de', '--modes', 'english,disabled')
    if 'european' in active:
        run('run_european_languages.py', *'red_es yellow_es gold_es gold_fr gold_it silver_es silver_fr crystal_es crystal_it'.split(),
            extra={'QA_SUITE': 'catalog', 'QA_GB_DRIVER': 'european_catalog_live.lua',
                   'QA_MARKER': 'EUROPEAN_CATALOG_LIVE_OK'})
    if 'ptbr' in active:
        # Rebuild the historical baseline rather than requiring saved evidence.
        run('run_merged_ptbr.py')
    if 'picker' in active:
        run('run_merged_picker.py')
    if 'asian' in active:
        for game in ('gold', 'silver', 'crystal'):
            for mode in ('final-cold', 'cold-verify', 'warm', 'extended', 'menus',
                         'credits', 'art', 'switch-request', 'switch-english'):
                run('run_asian_gen2.py', game, '--mode', mode)
        run('run_asian_gen2.py', 'crystal', '--mode', 'regional')
    print('RELEASE_MATRIX_PASSED', flush=True)


if __name__ == '__main__':
    main()
