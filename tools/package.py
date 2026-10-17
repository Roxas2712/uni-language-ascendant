"""Create an installable mod archive using an explicit runtime-only allowlist."""
from pathlib import Path
import hashlib, json, re, zipfile

root=Path(__file__).resolve().parents[1]
files=['manifest.json','main.lua','startup.lua','startup_view.lua','locales.lua','intro.lua','preferences.lua','Weitere-Sprachen.html','adapters.lua','options_schema.lua','rom_requirements.lua','translate.lua','extract.lua','assets.lua','world.lua','compiler.lua','cache_codec.lua','catalog.lua','overlay.lua','README.md','ROM-Liste.html','Performance.html','LICENSE.MD','VENDOR.md','vendor/index.lua']
files.extend(['latin_glyphs.lua','authored.lua','compat.lua','ptbr_names.lua','ptbr_moves.lua','ptbr_types.lua','ptbr_abilities.lua','ptbr_ability_descriptions.lua','ptbr_move_descriptions.lua','ptbr_gender.lua','ptbr_graphics.lua','ptbr_world_graphics.lua','ptbr_title_graphics.lua','ptbr_asset_text.lua','ptbr_credits.lua','ptbr_summary_graphics.lua','ptbr_pixel_labels.lua','ptbr_pokenav.lua','ptbr_pokenav_trainers.lua','ptbr_side_assets.lua','ptbr_scene_paths.lua','ptbr_scene_text.lua','ptbr_scene_authored.lua', 'ptbr_scene_bindings.lua','ptbr_easy_chat_ui.lua','ptbr_easy_chat.lua','ptbr_easy_chat_words.lua','profiles/sapphire_ptbr.lua'])
files.extend('profiles/'+game+'_ptbr_authored.lua' for game in ['emerald','ruby','sapphire'])
files.extend('profiles/'+game+'_ptbr/'+name+'.lua' for game in ['firered','leafgreen'] for name in ['profile','assets','world','authored'])
files.append('PT-BR.html')
files.extend(['ptbr_items.lua','ptbr_item_descriptions.lua','ptbr_classes.lua','ptbr_text_layout.lua'])
for game in ['firered','leafgreen','ruby','sapphire','emerald','emerald_fr','emerald_it','emerald_es','emerald_ptbr','ruby_ptbr']:
    files.extend([f'profiles/{game}.lua',f'profiles/{game}_assets.lua',f'profiles/{game}_world.lua'])
index=(root/'mod/vendor/index.lua').read_text()
files.extend('vendor/'+name.replace('.','/')+'.lua' for name in re.findall(r'\["([a-zA-Z0-9_.]+)"\] = true',index))
files.extend(str(p.relative_to(root/'mod')) for p in sorted((root/'mod/gb').rglob('*.lua')))
files.extend(str(p.relative_to(root/'mod')) for p in sorted((root/'mod/fonts').iterdir()) if p.suffix in ('.otf','.txt'))
files.extend('intro/'+p for p in ['IntroScene.lua','VoxelBall.lua','SOURCE.txt','ASSET-SHA256.json','assets/ascendant-start.png','assets/ascendant-chime.wav','assets/pikachu-atlas.png','assets/eevee-atlas.png','assets/mew-atlas.png'])
assert len(files)==len(set(files))
version=json.loads((root/'mod/manifest.json').read_text())['version']
dest=root/'dist';dest.mkdir(exist_ok=True)
out=dest/f'uni-language-ascendant-{version}.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for rel in files:
        data=(root/'mod'/rel).read_bytes()
        info=zipfile.ZipInfo('german_rom_source/'+rel,date_time=(2026,10,15,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        z.writestr(info,data)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)
    assert not any('baseroms/' in p or p.endswith(('.gba','.gb','.gbc','.sav')) for p in z.namelist())
digest=hashlib.sha256(out.read_bytes()).hexdigest()
(dest/'SHA256SUMS.txt').write_text(digest+'  '+out.name+'\n')
print(out, out.stat().st_size, 'bytes', digest)
