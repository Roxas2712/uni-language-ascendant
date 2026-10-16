"""Development input checklist; intentionally separate from supported ROM profiles."""
from pathlib import Path
import re,json,html,hashlib
from urllib.parse import quote
R=Path(__file__).resolve().parents[1]
entries=[];sources=[]
for gen,system in [(1,'Game Boy'),(2,'Game Boy Color'),(3,'Game Boy Advance')]:
 p=R/'build/language-references'/f'{system}.dat';data=p.read_text()
 url='https://github.com/libretro/libretro-database/blob/master/metadat/no-intro/'+quote('Nintendo - '+system+'.dat')
 sources.append(dict(system=system,url=url,version=re.search(r'\bversion "([^"]+)"',data)[1],sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 for block in re.findall(r'game \(\n(.*?)\n\)',data,re.S):
  name=re.search(r'^\s*name "([^"]+)"',block)[1]
  rom=re.search(r'rom \( name "([^"]+)" size (\d+) crc \w+ md5 (\w+) sha1 (\w+)',block)
  if rom:entries.append(dict(name=name,file=rom[1],size=int(rom[2]),md5=rom[3].lower(),sha1=rom[4].lower(),generation=gen,reference=url))
games=['red','blue','yellow','gold','silver','crystal','firered','leafgreen','ruby','sapphire','emerald']
labels=['Rot','Blau','Gelb','Gold','Silber','Kristall','Feuerrot','Blattgrün','Rubin','Saphir','Smaragd']
names={
 'fr':['Version Rouge','Version Bleue','Version Jaune - Edition Speciale Pikachu','Version Or','Version Argent','Version Cristal','Version Rouge Feu','Version Vert Feuille','Version Rubis','Version Saphir','Version Emeraude'],
 'it':['Versione Rossa','Versione Blu','Versione Gialla - Speciale Edizione Pikachu','Versione Oro','Versione Argento','Versione Cristallo','Versione Rosso Fuoco','Versione Verde Foglia','Versione Rubino','Versione Zaffiro','Versione Smeraldo'],
 'es':['Edicion Roja','Edicion Azul','Edicion Amarilla - Edicion Especial Pikachu','Edicion Oro','Edicion Plata','Edicion Cristal','Edicion Rojo Fuego','Edicion Verde Hoja','Edicion Rubi','Edicion Zafiro','Edicion Esmeralda'],
 'ja':['- Aka','- Ao','- Pikachu','Kin','Gin','- Crystal Version','- FireRed','- LeafGreen','- Ruby','- Sapphire','- Emerald']}
region={'fr':'France','it':'Italy','es':'Spain','ja':'Japan','ko':'Korea'}
langlabel={'fr':'Französisch','it':'Italienisch','es':'Spanisch','ja':'Japanisch','ko':'Koreanisch','de':'Deutsch'}
rows=[]
def choose(prefix):
 found=[e for e in entries if (e['name']==prefix or e['name'].startswith(prefix+' (')) and not any(t in e['name'] for t in ['(Rev','(Proto','(Debug','(Pirate','(Unl','(Pokemon Box','(Switch'])]
 assert len(found)==1,(prefix,[x['name'] for x in found]);return dict(found[0])
for lang,items in names.items():
 for game,label,stem in zip(games,labels,items):
  prefix=('Pocket Monsters '+stem if lang=='ja' else 'Pokemon - '+stem)+' ('+region[lang]+')'
  e=choose(prefix);e.update(language=lang,game=game,edition=label,revision=0,status='Profil fehlt – noch nicht unterstützt/getestet');rows.append(e)
for game,stem,label in [('gold','Geum','Gold'),('silver','Eun','Silber')]:
 e=choose('Pocket Monsters '+stem+' (Korea)');e.update(language='ko',game=game,edition=label,revision=0,status='Profil fehlt – noch nicht unterstützt/getestet');rows.append(e)
e=choose('Pocket Monsters - Midori (Japan)');e.update(language='ja',game='green',edition='Grün (zusätzliche Edition)',revision=0,status='Optional für vollständiges japanisches Gen1; separate Edition/Zuordnung nötig');rows.append(e)
assert len(rows)==47 and len({x['sha1'] for x in rows})==47
rows=[x for x in rows if not (x['game']=='emerald' and x['language'] in ('fr','it','es'))]
known=json.loads((R/'tools/rom_requirements.json').read_text())
for game in ['firered','sapphire']:
 c=next(x for x in known if x['game']==game);src=c['sources'][0];e=next(dict(x) for x in entries if x['sha1']==src['sha1'])
 e.update(language='de',game=game,edition=c['name'],revision=1 if game=='sapphire' else 0,status='Profil getestet; passende eigene ROM noch benötigt');rows.insert(0,e)
report=dict(status='Development inputs, not an importer allowlist',checked='2026-10-16',sources=sources,roms=rows)
(R/'tools/language_needs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
esc=html.escape
body='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Weitere Spielsprachen · Uni-Language Ascendant</title><style>body{background:#f4f2e6;color:#182b3c;font:16px/1.55 system-ui;max-width:1200px;margin:40px auto;padding:0 22px}h1{color:#ba303c}a{color:#086e72}aside{border:2px solid #182b3c;border-radius:12px;padding:20px;background:#ffdf70}table{width:100%;border-collapse:collapse}th,td{padding:14px 9px;text-align:left;border-bottom:1px solid #bbc5bd;vertical-align:top}small{display:block;color:#51656c}code{font-size:12px;overflow-wrap:anywhere}input{padding:12px;font:inherit;border:2px solid #182b3c;border-radius:8px;width:350px;max-width:85%}@media(max-width:700px){table,tbody,tr,td,th{display:block}thead{display:none}td,th{border:0}tr{border-bottom:2px solid #aaa}}</style>
<h1>Welche weiteren ROMs brauchen wir?</h1>
<aside><b>Aktuell spielbar und geprüft: Englisch und Deutsch für elf Editionen; zusätzlich Französisch, Italienisch und Spanisch für Emerald.</b><br>Die neun Menüsprachen sind davon unabhängig. Die folgenden fremdsprachigen ROMs sind Entwicklungsgrundlagen für neue Profile, noch keine unterstützten Imports. Ein passender Hash allein bedeutet noch keine Spielkompatibilität.</aside>
<p><b>Am besten zuerst:</b> Weitere Editionen auf Französisch, Italienisch und Spanisch. Die drei Emerald-ROMs liegen bereits vor und sind freigegeben. Japanisch folgt als eigener Zeichensatz-/Layout-Schritt. Dafür steht pro Sprache eine genaue Revision unten. Bereits vorhandene andere Revisionen bitte ebenfalls nennen; nicht mehrere Revisionen derselben Edition beschaffen.</p>
<p>Für die bisherigen elf Editionen: 30 weitere FR/IT/ES-ROMs, 11 japanische ROMs und 2 koreanische ROMs (Gold/Silber). Japanisches Grün ist als zusätzliche zwölfte Edition separat aufgeführt. Dazu fehlen für die bestehenden deutschen Profile noch die passende eigene Feuerrot-ROM und ein korrekter Saphir-1.1-Dump.</p>
<p>Japanische Gen1-Ausgaben unterscheiden sich auch in Inhalt und Datenlayout; insbesondere Grün und Blau sind keine austauschbaren Sprachdateien. Die Zuordnung zu den US-Basen muss separat umgesetzt und getestet werden.</p>
<p>Der geprüfte Original-ROM-Katalog enthält keine regulären chinesischen Gen1–3-Ausgaben. Chinesisch ist deshalb derzeit ausschließlich eine Menüsprache. Eine Fanübersetzung wäre ein eigenes Profil mit festgelegter Basis-ROM, Patch-Version und separaten Tests. Für Koreanisch umfasst diese Liste ausschließlich die Originalausgaben Gold/Silber.</p>
<p><b>Revisionen:</b> Für neue Profile wählen wir hier gezielt Revision 0 (1.0), keine VC-/Switch-Abwandlungen, Debug-Versionen oder bereits gepatchten Dateien. Saphir Deutsch benötigt wegen des vorhandenen Profils ausdrücklich Revision 1 (1.1). Dateinamen sind nur eine Orientierung; entscheidend ist die SHA-1 der vollständigen Datei.</p>
<label>Filtern <input id="filter" placeholder="z. B. Smaragd, Französisch, Japanisch"></label>
<table><thead><tr><th>Edition / Sprache</th><th>Exakte Datei / Revision</th><th>SHA-1 / Größe</th></tr></thead><tbody>'''
for e in rows:
 body+='<tr><th>'+esc(e['edition'])+'<small>Gen '+str(e['generation'])+' · '+langlabel[e['language']]+'</small></th><td>'+esc(e['file'])+'<small>Revision '+str(e['revision'])+' / 1.'+str(e['revision'])+'</small><small>'+esc(e['status'])+'</small></td><td><code>'+e['sha1']+'</code><small>'+str(e['size'])+' Bytes</small></td></tr>'
body+='</tbody></table><h2>Prüfen</h2><p>macOS/Linux: <code>shasum -a 1 "/Pfad/zur/Datei.gba"</code><br>Windows: <code>Get-FileHash "C:\\Pfad\\Datei.gba" -Algorithm SHA1</code></p><h2>Quellen</h2><p>Reine Dateinamen-/Prüfsummen-Metadaten aus Libretro / No-Intro; keine ROM-Downloads. Abgeglichen am 16.10.2026.</p><ul>'
for source in sources:body+='<li><a href="'+esc(source['url'])+'">Nintendo – '+source['system']+'</a> · Katalog '+source['version']+'</li>'
body+='''</ul><p><a href="ROM-Liste.html">Bereits unterstützte ROMs</a></p><script>document.querySelector('#filter').addEventListener('input',e=>{let q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script></html>'''
(R/'mod/Weitere-Sprachen.html').write_text(body)
print('LANGUAGE_NEEDS_OK',len(rows),'exact inputs; 44 future / 2 existing German profiles')
for e in rows:
 if e['game']=='emerald':print(e['language'],e['file'],e['sha1'])
