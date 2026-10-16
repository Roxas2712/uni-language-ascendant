from pathlib import Path
import json, shutil
from fontTools.ttLib import TTFont
from fontTools import subset
r=Path(__file__).resolve().parents[1]
strings=json.loads((r/'tools/ui_locales.json').read_text())
text=''.join(chr(c) for c in range(32,256))+''.join(v for d in strings.values() for v in d.values())+'←→✓·éÉ'
out=r/'mod/fonts';out.mkdir(exist_ok=True)
for index,name in [(0,'jp'),(1,'kr'),(2,'sc'),(3,'tc')]:
 font=TTFont(r/'build/NotoSansCJK-Regular.ttc',fontNumber=index)
 options=subset.Options();options.name_IDs=['*'];options.name_legacy=True;options.name_languages=['*']
 sub=subset.Subsetter(options=options);sub.populate(text=text);sub.subset(font)
 for record in font['name'].names:
  if record.nameID in (1,3,4,6,16,17):
   value='AscendantMenu'+name.upper() if record.nameID!=17 else 'Regular'
   record.string=value.encode(record.getEncoding())
 font.save(out/f'ascendant-{name}.otf')
 print(name,len(font.getBestCmap()),(out/f'ascendant-{name}.otf').stat().st_size)
(out/'OFL.txt').write_text('© 2014-2021 Adobe (http://www.adobe.com/).\n\n'+(r/'build/Noto-OFL.txt').read_text())
(out/'SOURCE.txt').write_text('UI glyph subsets of Noto Sans CJK Regular, SIL Open Font License 1.1.\nSource: https://github.com/notofonts/noto-cjk/tree/main/Sans/OTC\nRenamed AscendantMenu. Original copyright and license retained in OFL.txt.\n')
