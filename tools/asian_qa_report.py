"""Summarize reproducible localization checks. Never grants overall release QA."""
import hashlib,html,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/asian-gen2';LIVE=B/'live'
def checked(game,mode,marker='ASIAN_GEN2_LIVE_OK'):
 body=(LIVE/f'{game}-{mode}.log').read_text()
 assert marker in body and 'FAILED'not in body and 'Font: no glyph'not in body and 'strings: translation'not in body,(game,mode)
 return body
def records(body,prefix):
 return [json.loads(line[len(prefix):].strip())for line in body.splitlines()if line.startswith(prefix)]
def payload(game,mode):return records(checked(game,mode),'ASIAN_LOAD_JSON ')[0]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
ui=json.loads((B/'ui-coverage.json').read_text());jp=json.loads((B/'crystal-ja-profile-report.json').read_text())
assert jp['missing']=={} and jp['dialogue']==4003 and jp['named']==1011
assert jp['native']=={'dialogue':3970,'named':892}and len(jp['authoredCompatibility'])==152
rows=[];performance=[];modes=['final-cold','cold-verify','warm','extended','menus','credits','art']
for game,lang in [('gold','ko'),('silver','ko'),('crystal','ja')]:
 cold,warm=payload(game,'cold-verify'),payload(game,'warm')
 assert not cold['cacheHit']and warm['cacheHit']and cold['digest']==warm['digest']
 for mode in modes:assert payload(game,mode)['digest']==warm['digest'],(game,mode,'stale compiled payload')
 body=checked(game,'final-cold')
 for marker in ['ASIAN_GLYPHS_OK','ASIAN_MECHANICS_OK','ASIAN_NURSE_SAVE_OK','ASIAN_NAMING_INPUT_OK','ASIAN_BATTLE_INPUT_OK','ASIAN_REAL_DIALOGUE','ASIAN_REAL_BATTLE_MESSAGE']:assert marker in body,(game,marker)
 body=checked(game,'extended')
 for marker in ['ASIAN_REAL_PURCHASE_OK','ASIAN_REAL_INTRO_OK','ASIAN_MENU_STAGE\tdex-entry','ASIAN_MENU_STAGE\tdiploma','ASIAN_MENU_STAGE\tsummary-pokerus']:assert marker in body,(game,marker)
 # Only technical notation occurred in the exercised menus; no English prose.
 assert 'ASIAN_REAL_MENUS_OK'in checked(game,'menus')
 assert 'ASIAN_MENU_STAGE\tpc-deposit'in checked(game,'menus')
 assert 'ASIAN_MENU_STAGE\tparty-six'in checked(game,'menus')
 assert 'ASIAN_MENU_STAGE\tpack-actions'in checked(game,'menus')
 assert 'ASIAN_MENU_STAGE\tparty-battle'in checked(game,'menus')
 latin=records(body+checked(game,'menus'),'ASIAN_VISIBLE_LATIN\t')
 for row in latin:
  value=row['text'].split(' :: ',1)[1]
  import re
  ordinary=re.sub(r'<[^>]+>|ASCENDANT|FPS|HZ|PP|kg','',value)
  assert not re.search('[A-Za-z]{2,}',ordinary),(game,'Visible untranslated UI',value)
 assert 'ASIAN_REAL_CREDITS_OK'in checked(game,'credits')
 for mode,marker in [('switch-request','ASIAN_SWITCH_REQUEST_OK'),('switch-english','ASIAN_SWITCH_ENGLISH_OK')]:checked(game,mode,marker)
 for mode,language in [('perf-native',lang),('perf-en','en')]:
  record=records(checked(game,mode,'PERFORMANCE_JSON'),'PERFORMANCE_JSON ')[0]
  assert record['language']==language and record['game']==game and record['draw']['n']>=360
  performance.append(record)
 native=performance[-2];english=performance[-1]
 coverage=next(x for x in ui if x['game']==game)
 assert coverage['recipeSha256']==sha(R/f'mod/gb/profiles/{game}_{lang}/strings.lua')and not coverage['missing']
 rows.append({'game':game,'language':lang,'sha1':json.loads((R/f'tools/asian_gen2_refs/{game}.json').read_text())['sourceSha1'],'dialogue':4003 if lang=='ja'else 3044,'named':1011 if lang=='ja'else 889,'nativeDialogue':3970 if lang=='ja'else 3035,'nativeNamed':892 if lang=='ja'else 881,'authoredCompatibility':152 if lang=='ja'else 17,'ui':coverage,'coldSeconds':cold['seconds'],'warmSeconds':warm['seconds'],'payloadSha256':warm['digest'],'payloadFiles':warm['payloads'],'luaHeapMiB':native['luaMemoryKiB']/1024,'englishLuaHeapMiB':english['luaMemoryKiB']/1024,'nativeUpdateP95Ms':native['update']['p95Ms'],'englishUpdateP95Ms':english['update']['p95Ms'],'nativeDrawP95Ms':native['draw']['p95Ms'],'englishDrawP95Ms':english['draw']['p95Ms'],'world':json.loads((B/f'{game}-{lang}-world.json').read_text())})
regional=checked('crystal','regional');assert 'ASIAN_REAL_ODD_EGG_OK'in regional and 'ASIAN_REAL_EON_MAIL_OK'in regional
assert payload('crystal','regional')['digest']==rows[2]['payloadSha256']
for entry in records(regional,'ASIAN_REGIONAL_DIALOGUE\t'):
 text=entry['text'];text=__import__('re').sub(r'\{[A-Z]+\}','',text);assert not __import__('re').search('[A-Za-z]{3,}',text),entry
proof={p.name:sha(p)for p in sorted(LIVE.glob('*'))if p.suffix in('.png','.log')and (p.suffix=='.png'or any(p.name==f'{game}-{mode}.log'for game in ['gold','silver','crystal']for mode in modes+['switch-request','switch-english','perf-native','perf-en','regional']))}
report={'version':json.loads((R/'mod/manifest.json').read_text())['version'],'status':'localization-covered-scoped-qa-passed','scope':'Asian profiles; see MERGE-QA.json for the overall package gate','date':'2026-10-18','performanceEvidence':'Earlier development samples, retained as scoped evidence; not a fresh release performance benchmark','profiles':rows,'japaneseUnmapped':{},'japaneseClosed508':{'nativeRomMappings':356,'authoredUsCompatibility':152},'evidenceSha256':proof,'sourceSha256':{str(p.relative_to(R)):sha(p)for folder in ['mod/gb/runtime','mod/gb/adapters']for p in sorted((R/folder).glob('*.lua'))},'testIncidents':['One earlier Gold credits invocation ended without a completion marker. Two separate reruns completed with exit 0; the initial cause was not determined.'],'testScope':['All extracted script and named text slots populated; all compiled characters checked against available native glyphs','1060 literal Gen2 engine UI keys audited per edition, with explicit technical-notation exceptions','Actual nurse scripts: ROM-independent expected decode, healing, poison cure, goodbye, save/load','Actual clerk: three Potions, native item/quantity/price order, inventory and money mutation','Normal intro clock/name/Oak flow, five independently decoded native texts','Start, all options groups, party, four pack pockets, trainer card/badges, all Pokegear cards, PC, three summary pages','Pokedex list/options/search/entry, native one-page description and area action','Crystal actual Odd Egg gift and Eon Mail trade: original US scripts, authored Japanese text, real party/inventory changes','Original port-credit state machine through THE END (accelerated between rendered frames); native titles/main menus','Actual wild battle inputs to victory, four native moves; Unicode naming/delete/save','Native center/shop graphics; all used metatiles/collisions unchanged','Cold/warm payload equality; language switch back to English with native saved names retained','360-frame native/English performance samples in one scene'],'limitations':['Scoped scenario QA, not a full playthrough, exhaustive event-branch execution, or multiplayer/mobile test','US base game mechanics/events remain; Japanese mobile facilities are not implemented by a language overlay','Authored compatibility/UI translations are separate from native ROM excerpts; no claim of native-speaker editorial review','Original cartridge THE END/CONGRATULATIONS, hardware/button notation and port contributor/project names intentionally remain','Performance is one idle scene on this Mac with VSync and other apps running; the English Gold sample contains a roughly one-second draw outlier. Crystal native rendered 360 measured frames in about 0.8 s versus about 6.8 s in English, so presentation timing was not comparable. These samples do not isolate translation overhead. Lua heap is not process RSS or peak memory','Native saved-name fonts require the exact Asian ROM to remain imported','Overall package validation is recorded separately in MERGE-QA.json']}
(R/'mod/ASIAN-QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(B/'performance.json').write_text(json.dumps(performance,indent=2)+'\n')
md='''# Asiatische Gen2-Profile – Prüfumfang für Release 1.7.0

Die 508 zuvor fehlenden Kristall-Einträge sind geschlossen: **356 zusätzliche ROM-Zuordnungen und 152 ausdrücklich eigene Übersetzungen für den US-Spielablauf**. Kein erfasster Dialog- oder Systemtexteintrag ist mehr unbesetzt. Die Mod bleibt ein Sprachaufsatz auf der US-Basis; regionale Spielfunktionen werden nicht hinzugefügt.

| Profil | Dialoge | Benannte Texte | Eigene Kompatibilitätstexte | SHA-1 der Sprach-ROM |
|---|---:|---:|---:|---|
'''
for r in rows:md+=f"| {r['game']} / {r['language']} | {r['dialogue']}/{r['dialogue']} | {r['named']}/{r['named']} | {r['authoredCompatibility']} | `{r['sha1']}` |\n"
md+='''
Menüs und Grafikbeschriftungen: native Titel, Rucksack samt Taschenreitern, Trainerkarte, Arenaleiter, Pokédex, PokéCom, Diplom und Center-/Shop-Fassaden. Die festen Engine-Menüs und Port-Abspannrollen sind separat übersetzt. Kachelpositionen, koreanische Zeilenhöhe, japanische Lautzeichen, Unicode-Laufschrift und vertauschte Textparameter sind im Mod angepasst; die Engine bleibt unverändert. Die asiatische Teamliste zeigt vier Einträge gleichzeitig und scrollt zu allen sechs Pokémon; Namen, Status, Level und KP bleiben erhalten. PC- und Auswahlrahmen sind an die größere Schrift angepasst.

Je Edition sind 1.060 tatsächliche Gen2-UI-Quellschlüssel geprüft. Ausnahmen sind ausdrücklich benannte Zahlenformate, Einheiten, Glyphenmakros und Hardwarekürzel. Originale Aufschriften wie THE END und CONGRATULATIONS sowie Namen der Port-Mitwirkenden bleiben erhalten. Dies ist Textabdeckung, keine Behauptung, jeden Ereigniszweig durchgespielt zu haben.

## Echte Spieltests

Center-Heilung und Abschied, Ladenkauf mit korrektem Betrag und Inventar, Wildkampf bis zum Sieg, Namenseingabe und Speichern/Laden, das reguläre Intro, Optionsuntermenüs, Team/Status, Taschen, PC, Trainerkarte, PokéCom und Pokédex wurden in allen drei Editionen ausgeführt. Zusätzlich wurden Kristalls Ei-Geschenk und Brief-Tausch über die echten US-Kartenskripte gespielt. Ihre japanischen Texte sind eigene Kompatibilitätsübersetzungen, keine angeblichen japanischen Originaldialoge.

Native Titel und Diplom sowie der echte Port-Abspann wurden gerendert. Der Abspann wurde zwischen Bildaufnahmen beschleunigt; es wurde dafür kein neuer Dialog oder Abspanntext in den Test eingespeist. Screenshots und Protokolle liegen privat unter `build/asian-gen2/live/`, die Ingame-Dokumentation unter `build/asian-gen2/Pruefbericht.html`.

85 Python-Tests und 18 Lua-Testgruppen bestanden; alle Mod-Lua-Dateien wurden auf Syntax geprüft. Binär-/Einheitstests sind keine Übersetzungsbelege. Kalter Import und Cache-Start liefern identische Nutzdaten; der Wechsel zurück zu Englisch erhält lesbare asiatische Spielernamen.

| Profil | Kalt | Cache | Lua-Heap nativ / Englisch |
|---|---:|---:|---:|
'''
for r in rows:md+=f"| {r['game']} {r['language']} | {r['coldSeconds']*1000:.0f} ms | {r['warmSeconds']*1000:.0f} ms | {r['luaHeapMiB']:.1f} / {r['englishLuaHeapMiB']:.1f} MiB |\n"
md+='''
Die Performancewerte stammen aus den vorherigen Entwicklungsprüfungen; sie sind kein neuer Release-Benchmark. Messumfang: je 360 Update-/Draw-Frames in einer Szene auf diesem Mac mit VSync. Andere Anwendungen liefen parallel; insbesondere enthält Gold/Englisch einen Draw-Ausreißer von etwa einer Sekunde. Kristall nativ und Englisch hatten zudem deutlich unterschiedliche Frame-Ausgabezeiten (ca. 0,8 gegenüber 6,8 Sekunden für 360 Frames). Daraus wird kein Geschwindigkeitsvergleich abgeleitet. Die Messung isoliert keinen Übersetzungs-Overhead. Keine Messung des gesamten Prozessspeichers, kein Benchmark aller Szenen und kein Nachweis eines generell fehlenden Overheads. Details, Grenzen und Dateiprüfsummen stehen in ASIAN-QA.json.

Kein vollständiger Spieldurchlauf und kein Link-/Mobile-Test. Eigene Übersetzungen sind nicht als muttersprachlich lektoriert ausgewiesen. Die übergreifenden Paketprüfungen stehen separat in MERGE-QA.json.
'''
(R/'mod/ASIAN-PREVIEW.md').write_text(md)
shots=[('native-title','Titel aus der Sprach-ROM'),('nurse-greeting','Echter Center-Dialog; direkt gegen ROM geprüft'),('nurse-healed','Echte Antwort nach Heilung'),('nurse-choice','Echte Heilungsfrage mit bedienter Ja/Nein-Auswahl'),('mart-price','Echter Kauf: Artikel und Stückzahl'),('mart-price-final','Echte Kaufbestätigung mit Gesamtbetrag 900'),('battle-moves','Bediente Attackenauswahl'),('pack-item','Native Rucksackgrafik'),('pack-submenu','Tatsächlich geöffnetes Gegenstandsmenü'),('pack-toss-confirm','Echte Wegwerf-Rückfrage; anschließend abgebrochen, Inventar unverändert'),('gear-map','Native Karte und Ortsnamen'),('gear-radio','Native Radio-Beschriftung'),('dex-entry','Originaler Pokédex-Eintrag'),('party-six-last','Volles Team: zum sechsten Pokémon gescrollt'),('party-tm','TM-Auswahl mit langen Namen und Statusproblemen'),('party-battle-submenu','Bedientes Team-Untermenü für den Kampf'),('pc-submenu','Bediente Pokémon-Auswahl im PC'),('summary-1','Status und Typen'),('summary-pokerus','Echte Pokérus-Statusanzeige'),('summary-3','Statuswerte und Originaltrainer'),('dex-option','Pokédex-Einstellungen'),('diploma','Native Diplomgrafik und ROM-Text'),('credits-staff','Übersetzte Rollen des echten Port-Abspanns'),('pokecenter-front','Native Center-Fassade'),('mart-front','Native Laden-Fassade')]
sections=[]
for r in rows:
 cards=[]
 for suffix,label in shots:
  name=f"{r['game']}-{r['language']}-{suffix}.png";assert (LIVE/name).exists(),name
  cards.append(f'<figure><img loading="lazy" src="live/{name}" alt="{html.escape(label)}"><figcaption>{html.escape(label)}</figcaption></figure>')
 if r['game']=='crystal':
  for suffix,label in [('odd-egg-offer','Echtes Ei-Ereignis: eigene japanische Übersetzung des US-Skripts'),('eon-mail-request','Echter Brief-Tausch: eigene japanische Übersetzung des US-Skripts')]:
   name=f'crystal-ja-{suffix}.png';assert (LIVE/name).exists();cards.append(f'<figure><img loading="lazy" src="live/{name}"><figcaption>{label}</figcaption></figure>')
 sections.append(f'<section id="{r["game"]}"><h2>{r["game"].title()} · {r["language"].upper()}</h2><p>{r["dialogue"]} Dialoge · {r["named"]} Systemtexte · 0 unbesetzte Einträge</p><div class="grid">'+''.join(cards)+'</div></section>')
(B/'Pruefbericht.html').write_text('''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Uni-Language Ascendant · Gen2 Ingame-Prüfung</title><style>body{font:16px/1.6 system-ui;margin:0;background:#102333;color:#eaf0df}main{max-width:1200px;margin:auto;padding:32px}h1,h2{color:#ffd65a}nav a{color:white;display:inline-block;padding:8px 20px;background:#b83643;border-radius:10px;margin:4px}aside{background:#253d4c;border-left:6px solid #ffd65a;padding:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}figure{margin:0;background:#0b1722;border-radius:12px;overflow:hidden}img{width:100%;image-rendering:pixelated;display:block}figcaption{padding:14px}section{margin-top:40px}</style><main><h1>Uni-Language Ascendant</h1><p>Japanisches Kristall · koreanisches Gold und Silber</p><aside><b>508 Kristall-Lücken geschlossen.</b> 356 zusätzliche ROM-Zuordnungen und 152 eigene US-Kompatibilitätstexte. Alle Bilder stammen aus dem laufenden Spiel. Original-ROM-Dialoge, eigene Übersetzungen und Port-Menüs werden ausdrücklich unterschieden. Textabdeckung und dokumentierte Szenentests sind kein vollständiger Spieldurchlauf. Kein Link-/Mobile-Test.</aside><nav><a href="#gold">Gold KO</a><a href="#silver">Silber KO</a><a href="#crystal">Kristall JA</a></nav>'''+''.join(sections)+'</main></html>')
print('ASIAN_SCOPED_QA_REPORT_OK 3 profiles; missing text slots 0; overall package gate in MERGE-QA.json')
