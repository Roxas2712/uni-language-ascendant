from pathlib import Path
import subprocess,os
root=Path(__file__).resolve().parents[1]
p=Path.home()/'Library/Application Support/LOVE/german-rom-mod-gb-qa/options.lua'
original=p.read_bytes() if p.exists() else None
try:
 p.write_text('return {mods={german_rom_source=false}}')
 subprocess.run(['python3',str(root/'tests/run_gb_smoke.py')],env=dict(os.environ,QA_DRIVER='gb_disabled.lua'),check=True)
finally:
 if original is None:p.unlink(missing_ok=True)
 else:p.write_bytes(original)
