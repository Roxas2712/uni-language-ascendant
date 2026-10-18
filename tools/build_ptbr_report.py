"""Build the PT-BR report from genuine captures and hashed QA logs.
--require-final refuses to package a report with missing required runs.
Synthetic unit/font fixtures are never translation evidence.
"""
import argparse,base64,hashlib,html,json,re
from functools import lru_cache
from statistics import median
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'build/ptbr-qa'
GB=['red','blue','yellow','gold','silver','crystal']
GBA=['ruby','sapphire','emerald','firered','leafgreen']
GAMES=GB+GBA
NAMES=dict(zip(GAMES,['Rot','Blau','Gelb','Gold','Silber','Kristall','Rubin','Saphir','Emerald','Feuerrot','Blattgrün']))
@lru_cache(maxsize=1)
def runtime_hashes():
 return {p.relative_to(ROOT/'mod').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'mod').rglob('*.lua')}
@lru_cache(maxsize=None)
def selected_profiles(game,language):
 paths=set()
 for line in (ROOT/'mod/catalog.lua').read_text().splitlines():
  fields=dict(re.findall(r"(\w+)='([^']*)'",line))
  if fields.get('game')==game and fields.get('language')==language:
   paths.update(fields[k] for k in ('profile','assets','world','authored') if k in fields)
   if fields.get('root'):paths.update(p.relative_to(ROOT/'mod').as_posix() for p in (ROOT/'mod'/fields['root']).rglob('*.lua'))
 return paths
def stem(game,language,label):return ('' if game=='emerald' else game+'-')+language+'-'+label
def helper_dependencies(driver,seen=None):
 seen=set() if seen is None else seen
 for value in re.findall(r'''["']([^"']+\.lua)["']''',(ROOT/'tests'/driver).read_text()):
  name=Path(value).name
  if name.startswith(('ptbr_','frlg_','rs_ptbr_')) and (ROOT/'tests'/name).is_file() and name not in seen:
   seen.add(name);helper_dependencies(name,seen)
 return seen
def proof(name):
 path=QA/(name+'.log');ev=QA/(name+'.evidence.json')
 if not path.exists() or not ev.exists():return None
 row=json.loads(ev.read_text())
 if row['log_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():return None
 driver=ROOT/'tests'/row.get('driver','missing-driver')
 if not driver.is_file() or row.get('driver_sha256')!=hashlib.sha256(driver.read_bytes()).hexdigest():return None
 for helper in helper_dependencies(driver.name):
  if row.get('helpers_sha256',{}).get(helper)!=hashlib.sha256((ROOT/'tests'/helper).read_bytes()).hexdigest():return None
 if not row['passed']:return None
 if any(term in path.read_text().lower() for term in ('draw failed:', 'update failed:', 'runtime error:', 'stack traceback:', 'hot-path pcall failed')):return None
 if any(row.get('test_options',{}).get(k) for k in ('QA_CONTEST_ONLY','QA_NAV_ONLY','QA_SIDE_DECOR_ONLY','QA_FRONTIER_SAMPLE')):return None
 # Retain the complete recorded fingerprint, and refuse obsolete required
 # runs. Gen1/2 never execute the separate Gen3 overlay/profile modules.
 stale=[]
 for rel,digest in runtime_hashes().items():
  # Other editions' recipes are never loaded by this run. Keep their hashes
  # in the evidence, but require only the selected profile plus shared code.
  if (rel.startswith('profiles/') or rel.startswith('gb/profiles/')) and rel not in selected_profiles(row['game'],row['language']):continue
  if row['game'] in GB and not (rel.startswith('gb/') or rel.startswith('intro/') or rel in ('main.lua','compiler.lua','cache_codec.lua','adapters.lua','catalog.lua','startup.lua','startup_view.lua','preferences.lua','locales.lua','intro.lua','rom_requirements.lua','options_schema.lua')):continue
  if row['game'] in GBA and rel.startswith('gb/'):continue
  if row.get('runtime_sha256',{}).get(rel)!=digest:stale.append(rel)
 if stale:return None
 return row

def picture(name,caption):
 path=QA/name;assert path.exists(),name
 return '<figure><img loading="lazy" alt="'+html.escape(caption)+'" src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'

def build(require_final):
 manifest=json.loads((ROOT/'mod/manifest.json').read_text())
 sources=json.loads((ROOT/'tools/ptbr_sources.json').read_text())
 requirements=json.loads((ROOT/'tools/rom_requirements.json').read_text())
 environment_path=QA/'performance-environment.json'
 environment=json.loads(environment_path.read_text()) if environment_path.exists() else {}
 checks=[];missing=[];perf=[]
 for game in GAMES:
  modes=['live']
  if game in GBA:modes+=['vocabulary','uitour','endings','easy-chat','hatch']+(['reference','gender'] if game in ('firered','leafgreen') else ['side-menus','minigames','braille'])
  if game=='emerald':modes+=['dialogues','frontier','panels']
  for mode in modes:
   name=stem(game,'pt-BR','final-'+mode);ev=proof(name)
   if not ev:missing.append(name);continue
   checks.append({**ev,'game':game,'mode':mode,'log':name+'.log'})
  for lang in ('en','pt-BR'):
   for label in ('perf-a','perf-b'):
    name=stem(game,lang,label);ev=proof(name)
    if not ev:missing.append(name);continue
    rows=[json.loads(s.split(' ',1)[1]) for s in (QA/(name+'.log')).read_text().splitlines() if s.startswith('PERFORMANCE_JSON ')]
    assert len(rows)==1 and rows[0]['draw']['n']==360,name
    perf.append(dict(rows[0],log=name+'.log',log_sha256=ev['log_sha256']))
 for lang,mode,label in [('en','menu','final-menu')]+[(lang,'smoke','final-regression') for lang in ('en','de','fr','it','es')]:
  name=stem('emerald',lang,label);ev=proof(name)
  if not ev:missing.append(name)
  else:checks.append({**ev,'game':'emerald','mode':mode,'log':name+'.log'})
 if require_final:assert not missing,'Pending: '+', '.join(missing)
 report={'format':2,'version':manifest['version'],'status':'verified-scope' if not missing else 'verification-in-progress','known_baseline_failures':[{'game':'emerald','language':'en','case':'norman-rematch-one-mon','result':'Base engine remains locked after rejecting the rematch; translated mode includes a scoped compatibility fix.','log':'en-upstream-norman-lock.log'}],'environment':environment,'full_story_playthrough':False,'missing_checks':missing,'checks':checks,'performance':perf,'sources':sources,'evidence_policy':'Native screens and NPC interaction. Fixtures prepare save/map/party state only; no injected display messages. Unit tests are not translation evidence.','performance_limits':'Two EN and two PT-BR runs per edition in the same stationary overworld scene; 180 warm-up and 360 measured frames. This is not a battle or dialog stress benchmark. Vsync and background load affect timing. Lua heap is not process RAM; no forced collection.'}
 optimization_html=''
 optimization_path=ROOT/'docs'/('Optimization-'+manifest['version']+'.json')
 if optimization_path.exists():
  optimization=json.loads(optimization_path.read_text());report['optimization']=optimization
  cells=''
  for version,values in optimization['medians'].items():
   cells+='<tr><td>'+html.escape(version)+'</td><td>'+f"{values['modLoadSeconds']:.2f} s"+'</td><td>'+f"{values['luaMemoryKiB']/1024:.1f} MiB"+'</td><td>'+f"{values['peakProcessRSSBytes']/1024**2:.1f} MiB"+'</td><td>'+f"{values['observedFPS']:.2f}"+'</td></tr>'
  optimization_html='<section id="optimization"><h2>1.5.1: schneller laden, weniger Speicher</h2><p>Verlustfreier Binärcache, weniger überschreibende Zwischeneinträge und komprimierte Gen3-Rohgrafiken. Grafikdaten werden bei der ersten Verwendung entpackt und anschließend wiederverwendet. Der erste Start nach dem Update baut den Cache einmal neu auf; Imports und persönliche Einstellungen bleiben erhalten.</p><p>Vorher-/Nachher-Vergleich in Emerald PT-BR: zwei warme Läufe je Version, abwechselnd 1.5.0 / 1.5.1 / 1.5.1 / 1.5.0, dieselbe ruhende Oldale-Szene. Medianwerte:</p><div class="scroll"><table><tr><th>Version</th><th>Mod laden</th><th>Lua-Heap</th><th>Max. Prozess-RAM</th><th>FPS</th></tr>'+cells+'</table></div><p>Alle 25 veröffentlichten Sprachprofile wurden vollständig auf unveränderte Cache-Inhalte geprüft: elf deutsche und elf portugiesische Editionen sowie Emerald FR/IT/ES. Endgültige Textwerte sind identisch; bei unterschiedlicher Kachelanordnung wurden die dargestellten Pixel verglichen.</p><small>Lua-Heap ohne erzwungene Speicherbereinigung; Prozess-RAM ist das Betriebssystem-Maximum einschließlich Startphase. VSync und andere Anwendungen beeinflussen die Messung. Die Speicherersparnis hängt von bereits besuchten Bildschirmen ab. Kein vollständiger Story- oder Worst-Case-Benchmark.</small></section>'
 verified_captures={}
 for path in QA.glob('*final-*.evidence.json'):
  evidence=proof(path.name.removesuffix('.evidence.json'))
  if evidence:
   for name,digest in evidence.get('captures_sha256',{}).items():
    verified_captures.setdefault(name,{}).setdefault(digest,[]).append(path.name)
 document_captures={}
 def render(name,caption):
  digest=hashlib.sha256((QA/name).read_bytes()).hexdigest()
  evidence=verified_captures.get(name,{}).get(digest,[])
  if require_final:assert evidence,'Document capture has no current gameplay proof: '+name
  document_captures[name]={'sha256':digest,'evidence':evidence}
  return picture(name,caption)
 cards=[]
 scope_labels={'live':'Heilung, Feld-Dialoge, Kampf, Speichern','vocabulary':'Vollständige Namenslisten und Textbreiten','uitour':'Native Menüs und Grafikbeschriftungen','endings':'Diplom und Abspann','easy-chat':'Wortwahl und gespeicherte Wort-IDs','hatch':'Schlüpfen und Spitznamenabfrage','reference':'Hilfe und Ruhmeschecker','gender':'Spieleransprache','side-menus':'Beeren, Dekorationen und Nebenmenüs','minigames':'Vollständiger Wettbewerb, Casino und Beerenmixer','braille':'Echte Braille-Tafel-Interaktionen','dialogues':'Zusätzliche Feld- und Pensionsdialoge','frontier':'47 Kampfzonen-Dialogfälle','panels':'363 Herkunftsangaben und Attackenbeschreibungen'}
 for game in GAMES:
  prefix='' if game=='emerald' else game+'-'
  shots=render(prefix+'pt-BR-healing.png',NAMES[game]+': echter Heilungsdialog durch NPC-Interaktion.')+render(prefix+'pt-BR-mart.png',NAMES[game]+': Ladenfront im Spiel.')
  moveShot=(game+'-pt-BR-move-menu.png') if game in GB else (game+'-pt-BR-summary-3.png') if game in ('firered','leafgreen') else (game+'-pt-BR-ui-summary-2.png')
  if (QA/moveShot).exists():shots+=render(moveShot,NAMES[game]+': Attackennamen im nativen Spielmenü; Party als dokumentierte Testvorbereitung.')
  if game in ('red','ruby','emerald') and (QA/(prefix+'en-healing.png')).exists():shots+=render(prefix+'en-healing.png','Englische Vergleichsszene derselben Edition.')
  req=next(r for r in requirements if r['game']==game);source=next(r for r in req['sources'] if r['language']=='pt-BR')
  cards.append('<section class="game" data-game="'+game+'"><h2>'+NAMES[game]+'</h2><p>'+str(sum(c['game']==game and c['language']=='pt-BR' for c in checks))+' aktuelle PT-BR-Prüfgruppen bestanden. Attackennamen: '+str(165 if game in GB[:3] else 251 if game in GB else 354)+'.</p><details><summary>Geprüfte Abläufe</summary><p>'+('Heilung und Dialogwahl, Außenbeschriftungen, Pokédex, echter Kampf, Diplom und Abspann.' if game in GB else '; '.join(scope_labels[c['mode']] for c in checks if c['game']==game and c['language']=='pt-BR'))+'</p></details><div class="shots">'+shots+'</div><details><summary>Benötigte ROM-Identitäten</summary><p>US-Basis: '+html.escape(req['base']['name']+' · '+req['base']['version'])+'<code>'+req['base']['sha1']+'</code></p><p>PT-BR-Quelle:<code>'+source['sha1']+'</code></p></details></section>')
 deeper=[('ruby-pt-BR-minigame-contest-move-1.png','Rubin: natives Wettbewerbsmenü mit übersetzter Attacke, Beschreibung und Grafikbeschriftungen.'),('sapphire-pt-BR-minigame-contest-comment.png','Saphir: echter Kommentar während einer vollständigen Wettbewerbsrunde.'),('emerald-pt-BR-easy-chat-profile.png','Emerald: natives Wortmenü.'),('ruby-pt-BR-hatch-nickname.png','Rubin: originale Schlüpfsequenz und Spitznamenabfrage.'),('firered-pt-BR-reference-fame-4-1-gender-1.png','Feuerrot: Ruhmeschecker mit weiblicher Spieleransprache.'),('firered-pt-BR-reference-help-4-2.png','Feuerrot: natives Hilfemenü.')]
 deeper += [('emerald-pt-BR-memo-frontier.png','Emerald: vollständiger Fundort im nativen Pokémon-Bericht; zusätzlich 363 Herkunfts-/Wesen-Kombinationen auf die tatsächlichen Textgrenzen geprüft.'),('ruby-pt-BR-ui-bag.png','Rubin: echte Itemliste und Beschreibung im Beutel.'),('ruby-pt-BR-ui-location-mapsec_granite_cave.png','Rubin: Ortsname im nativen Pokémon-Bericht; Fundort als Test-Spielstand vorbereitet.')]
 deep=''.join(render(n,c) for n,c in deeper if (QA/n).exists())
 rows=''.join('<tr><td>'+html.escape(NAMES[r['game']]+' / '+r['language']+' / '+r['log'].split('-perf-')[-1].split('.')[0])+'</td><td>'+f'{r["draw"]["p50Ms"]:.2f} / {r["draw"]["p95Ms"]:.2f}'+'</td><td>'+f'{r["update"]["p50Ms"]:.3f}'+'</td><td>'+f'{r["modLoadSeconds"]:.3f}'+'</td><td>'+('ja' if r['cacheHit'] else 'nein')+'</td><td>'+f'{r["luaMemoryKiB"]/1024:.1f}'+'</td></tr>' for r in perf)
 summary_rows=''
 for game in GAMES:
  grouped={lang:[r for r in perf if r['game']==game and r['language']==lang] for lang in ('en','pt-BR')}
  if any(len(rows)!=2 for rows in grouped.values()):continue
  metrics=[]
  for metric in (lambda r:360/r['elapsedSeconds'],lambda r:r['update']['p95Ms'],lambda r:r['modLoadSeconds'],lambda r:r['luaMemoryKiB']/1024):
   metrics.append(' / '.join(f'{median(metric(r) for r in grouped[lang]):.2f}' for lang in ('en','pt-BR')))
  summary_rows+='<tr><td>'+NAMES[game]+'</td>'+''.join('<td>'+v+'</td>' for v in metrics)+'</tr>'
 links=''.join('<li>'+NAMES[s['game']]+': '+('eigene Saphir-Ergänzungen mit derselben Rubin-Textquelle' if not s.get('source') else '<a href="'+html.escape(s['source'],quote=True)+'">Übersetzungsprojekt / Patchquelle</a>')+'</li>' for s in sources['games'])
 options='<option value="all">Alle Editionen</option>'+''.join('<option value="'+g+'">'+NAMES[g]+'</option>' for g in GAMES)
 status='Prüfungen im unten beschriebenen Umfang bestanden.' if not missing else 'Prüfung läuft noch: '+str(len(missing))+' erforderliche Ergebnisse fehlen.'
 body='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Uni-Language Ascendant · PT-BR</title><style>
 :root{color-scheme:dark;font:17px/1.6 system-ui;background:#101b2e;color:#edf5ff}*{box-sizing:border-box}body{margin:0}main{max-width:1150px;margin:auto;padding:32px 22px}header{border-bottom:5px solid #f7ce50;padding:22px 0}h1{font-size:clamp(2rem,5vw,3.7rem);line-height:1.1;margin:8px 0}h2{color:#ffd86b}a{color:#8ce1dc}section{background:#1c2b43;border:1px solid #3b526e;border-radius:20px;padding:24px;margin:24px 0}.kicker{color:#8ce1dc;letter-spacing:.12em;font-weight:700}.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(270px,100%),1fr));gap:20px}figure{margin:0}img{width:100%;height:auto;image-rendering:pixelated;border-radius:10px;background:#060b12}figcaption{font-size:.85rem;color:#c2d1e5;margin:8px 0 20px}select{font:inherit;padding:12px;border-radius:12px;background:#253955;color:white;border:1px solid #66819e}code{display:block;overflow-wrap:anywhere;color:#9ce6c5}details{margin:18px 0}summary{cursor:pointer;font-weight:650}table{border-collapse:collapse;width:100%;font-size:.85rem}td,th{padding:10px;text-align:left;border-bottom:1px solid #47617c}.scroll{overflow:auto}[hidden]{display:none!important}small{color:#c2d1e5}
 </style><main><header><p class="kicker">UNI-LANGUAGE ASCENDANT · PORTUGUÊS DO BRASIL</p><h1>Elf Editionen.<br>Im Spiel geprüft.</h1><p>'''+html.escape(manifest['version'])+' · '+status+'''</p></header>
 <section><h2>Was du hier siehst</h2><p>Die Heilungsbilder stammen aus echten NPC-Interaktionen. Die Tests prüfen außerdem die KP-Erholung und die Rückkehr zur Feldsteuerung. Für Menüs, Kämpfe und Endgame-Bildschirme werden gezielte Spielstände und Party-Daten vorbereitet; die Texte liefert jeweils das Spiel mit aktiver Mod.</p><p>Der frühere Satz „Missão concluída! Poções, saúde e proteção.“ war ein künstlicher Schrift-Test und ist kein Übersetzungsbeleg. Solche Bilder sind hier ausgeschlossen.</p><p>Geprüft werden Import, Textzuordnung, Attackennamen, Zeichen, ausgewählte Textbreiten, native Menüs, Grafikbeschriftungen, Kämpfe und echte Dialogabläufe. Das ist kein vollständiger Story-Durchlauf aller elf Spiele und kein Test sämtlicher Link- oder Mehrspielerzweige.</p><details><summary>Befund im englischen Basisspiel</summary><p>Emerald gibt beim abgelehnten Norman-Rückkampf mit nur einem kampffähigen Pokémon die Feldsteuerung nicht zurück. Der Fehler wurde im englischen Vergleich reproduziert; im übersetzten Modus behebt ihn die Kompatibilitätskorrektur der Mod. Der normale Sprachvergleich prüft Heilung, Menü, Speichern und Kampf separat.</p></details></section>
 <label>Edition anzeigen <select id="edition">'''+options+'</select></label>'+''.join(cards)+'''
 <section><h2>Mehr als Dialogtexte</h2><p>Die Mod ergänzt Attacken und Fähigkeiten, Itemnamen und Beschreibungen, Trainerklassen, Ortsnamen, Pokédex-Texte, Status- und Menübeschriftungen, Titel- und Weltgrafiken sowie native Nebenmenüs. Gen3 umfasst auch Wortlisten, PokéNav, Wettbewerbe, Beeren und Dekorationen; Feuerrot und Blattgrün zusätzlich Hilfe und Ruhmeschecker. Eigennamen, Pokémon-Artnamen und Hardwaretasten wie START/SELECT bleiben Eigennamen.</p><div class="shots">'''+deep+'''</div><p>Saphir bleibt das eigene Saphir-Spiel. Nur exakt identische Ausgangstexte werden aus der Rubin-Quelle übernommen; Unterschiede erhalten eigene Übersetzungen. Numerische Attacken- und Wort-IDs bleiben erhalten.</p></section>
 '''+optimization_html+'''<section id="performance"><h2>Performance</h2><p>Testgerät: '''+html.escape(environment.get('cpu','nicht erfasst')+' · '+str(round(environment.get('memory_bytes',0)/1024**3))+' GiB · '+environment.get('os','nicht erfasst'))+'''. Die Messläufe starten einzeln, nachdem alle funktionalen Testinstanzen beendet sind; andere Anwendungen bleiben geöffnet.</p><p>Je Edition zwei englische und zwei portugiesische Läufe in derselben ruhenden Außenwelt-Szene: jeweils 180 Aufwärmframes und 360 Messframes. Kämpfe und Dialoge sind funktional geprüft; diese Zeitmessung ist kein Kampf- oder Dialog-Stresstest. Der lokale Sprachcache vermeidet wiederholtes Kompilieren. Laden und Speicherbedarf können trotzdem höher liegen. Die Messungen unter Hintergrundlast und VSync sind ein Vergleich, kein Beweis für exakt null Performance-Einfluss.</p><p>Übersicht: Median der beiden Läufe je Sprache, jeweils <strong>Englisch / PT-BR</strong>.</p><div class="scroll"><table><tr><th>Edition</th><th>Beobachtete FPS</th><th>Update p95, ms</th><th>Laden, s</th><th>Lua-Heap, MiB</th></tr>'''+summary_rows+'''</table></div><details><summary>Alle einzelnen Messläufe</summary><div class="scroll"><table><tr><th>Edition / Sprache / Lauf</th><th>Zeichnen p50 / p95, ms</th><th>Update p50, ms</th><th>Mod laden, s</th><th>Cache</th><th>Lua-Heap, MiB</th></tr>'''+rows+'''</table></div></details><small>Lua-Heap ohne erzwungene Speicherbereinigung; kein Prozess-RAM-Messwert.</small></section>
 <section><h2>Deine Dateien und Quellen</h2><p>Benötigt werden deine exakte englische Basis-ROM und die passende PT-BR-Quelle. Revisionen sind nicht austauschbar. Bei Feuerrot/Blattgrün unterscheiden sich die Basis zum Anwenden des Fanpatches (1.1) und das US-Basisspiel im Recompiler (1.0). Die <a href="ROM-Liste.html">ROM-Liste</a> enthält Import-Identitäten; Patchbasis und Patch-Prüfsummen stehen in den <a href="https://github.com/Roxas2712/uni-language-ascendant/blob/main/tools/ptbr_sources.json">Quellangaben</a>.</p><ul>'''+links+'''</ul><p>Die Mod enthält keine ROMs oder Fanpatches. Eigene Ergänzungen sind an Ausgangsprüfsummen gebunden. Unbekannte ROM-Revisionen werden nicht stillschweigend übernommen.</p></section>
 <section><h2>Menü, Zurück und Reset</h2><p>Menüsprache und Spielsprache werden separat gewählt. Das Ascendant-Intro läuft einmal pro Mod-Profil. Zurück korrigiert eine Auswahl; Profil zurücksetzen startet die Einrichtung erneut. Ein Update erhält das Profil. Deinstallation löscht es; eine Neuinstallation beginnt neu. Dieser Hinweis erscheint vor der ersten Auswahl auf Englisch.</p></section>
 <footer>Basierend auf <a href="https://github.com/bryanthaboi/gen1recomp">Gen1Recomp</a> von BOIS CLUB GAMES, LLC. Messwerte und Prüffingerabdrücke: docs/PT-BR-QA.json.</footer></main><script>document.querySelector('#edition').addEventListener('change',e=>document.querySelectorAll('.game').forEach(s=>s.hidden=e.target.value!=='all'&&s.dataset.game!==e.target.value))</script></html>'''
 report['document_captures']=document_captures
 (ROOT/'docs/PT-BR-QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'mod/PT-BR.html').write_text(body)
 print('PTBR_REPORT',len(checks),'checks;',len(perf),'performance runs;',len(missing),'pending')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-final',action='store_true');build(p.parse_args().require_final)
