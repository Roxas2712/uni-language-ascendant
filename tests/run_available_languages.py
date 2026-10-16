"""Check missing imports using the dedicated Emerald QA identity, restoring inputs."""
import os
import subprocess
import tempfile
from pathlib import Path
import run_emerald_languages as qa

imports = qa.prepare()
moved = []
with tempfile.TemporaryDirectory(prefix='ula-import-filter-') as directory:
    hold = Path(directory)
    try:
        for source in (imports, qa.ENGINE/'mods/german_rom_source/baseroms'):
            for language in ('de', 'fr', 'it', 'es'):
                path = source/f'emerald_{language}.gba'
                if path.exists():
                    dest = hold/str(len(moved))
                    path.rename(dest)
                    moved.append((path, dest))
        for label, available in [('english-only', 'en'), ('spanish-only', 'en,es')]:
            if label == 'spanish-only':
                source, dest = next(row for row in moved if row[0] == imports/'emerald_es.gba')
                dest.rename(source)
            (imports/'.uni-language-profile').write_text(
                'ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\n'
                'preferences/ui-language.txt=de\npreferences/emerald.txt=fr\n')
            (qa.QA/'options.lua').write_text(
                'return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker=true}}}\n')
            log = qa.ROOT/f'build/available-languages-{label}.log'
            env = dict(os.environ, POKEPORT_IDENTITY=qa.IDENTITY, POKEPORT_VERSION='emerald',
                       POKEPORT_DRIVER=str(qa.ROOT/'tests/available_languages_live.lua'),
                       QA_AVAILABLE_LANGUAGES=available, QA_EXPECTED_LANGUAGE='en')
            with log.open('w') as output:
                result = subprocess.run([qa.LOVE, str(qa.ENGINE)], env=env, stdout=output,
                                        stderr=subprocess.STDOUT, timeout=90)
            lines = log.read_text().splitlines()
            for line in lines:
                if 'AVAILABLE_LANGUAGES_' in line or 'entry failed' in line:
                    print(line, flush=True)
            assert result.returncode == 0 and any(line.startswith('AVAILABLE_LANGUAGES_OK') for line in lines), log
    finally:
        for source, dest in moved:
            if dest.exists():
                assert not source.exists(), source
                dest.rename(source)
