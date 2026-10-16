from pathlib import Path
import json,html,statistics as st
R=Path(__file__).resolve().parents[1]
raw=json.loads((R/'build/performance/results.json').read_text());loads=json.loads((R/'build/load-times.json').read_text());catalog=json.loads((R/'tools/rom_requirements.json').read_text())
rows=[]
def mean(a,metric,key='meanMs'):
 if key=='meanMs':return sum(x[metric][key]*x[metric]['n'] for x in a)/sum(x[metric]['n'] for x in a)
 return max(x[metric][key] for x in a)
for c in catalog:
 g=c['game'];base=[x for x in raw if x['game']==g and x['language']=='baseline'];de=[x for x in raw if x['game']==g and x['language']=='de'];en=[x for x in raw if x['game']==g and x['language']=='en']
 assert len(base)==2 and len(de)==2 and len(en)==1,g
 cold=next(x for x in loads if x['game']==g and x['mode']=='cold');warm=next(x for x in loads if x['game']==g and x['mode']=='warm')
 assert not cold['cacheHit'] and warm['cacheHit']
 rows.append(dict(game=g,coldSeconds=cold['seconds'],warmSeconds=warm['seconds'],baseUpdateMs=mean(base,'update'),deUpdateMs=mean(de,'update'),enUpdateMs=mean(en,'update'),baseDrawMs=mean(base,'draw'),deDrawMs=mean(de,'draw'),deUpdateP95Ms=mean(de,'update','p95Ms'),baseUpdateP95Ms=mean(base,'update','p95Ms'),deDrawP95Ms=mean(de,'draw','p95Ms'),frames=sum(x['draw']['n'] for x in base+de+en),memoryDeltaMiB=(st.mean(x['luaMemoryKiB'] for x in de)-st.mean(x['luaMemoryKiB'] for x in base))/1024))
report=dict(games=rows,rawRuns=len(raw),frames=sum(x['frames'] for x in rows),method='Two baseline, two German and one English mod run per edition, 360-900 overworld frames each. Draw includes GPU/driver wait. Concurrent unrelated game tests caused uncontrolled CPU/GPU load. Cold/warm cache measured separately. This is a diagnostic sample, not a whole-game performance guarantee.')
(R/'build/performance-summary.json').write_text(json.dumps(report,indent=2)+'\n')
body='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Performance · Uni-Language Ascendant 1.3</title><style>body{font:16px/1.5 system-ui;background:#101d2b;color:#edf5f8;max-width:1200px;margin:40px auto;padding:0 24px}h1{font-size:36px}p{max-width:1000px;color:#bfd0dd}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:12px;border-bottom:1px solid #334455}th{color:#8fe0bc}aside{padding:20px;background:#233246;border-radius:8px}.scroll{overflow-x:auto}</style><h1>Performance-Prüfung</h1><p>Uni-Language Ascendant 1.3.0 · macOS / LÖVE 12 / Metal</p>
<aside>Die ROM-Dekodierung läuft nur bei einem fehlenden oder ungültigen Sprach-Cache. Warmstarts laden und prüfen das Ergebnis erneut. Das kostet weiterhin Startzeit. Die Sprachwahl entfernt ihre Frame-Wrapper nach der Bestätigung vollständig.</aside>
<p>'''+str(report['rawRuns'])+' Läufe / '+str(report['frames'])+''' gemessene Frames. Pro Edition: zweimal Basisspiel ohne Sprachmod, zweimal Deutsch mit Mod und einmal Englisch mit Mod. Je Lauf 360-900 Overworld-Frames nach 180 Aufwärmframes. Die Szenen sind pro Edition gleich.</p>
<div class="scroll"><table><thead><tr><th>Edition</th><th>Erstverarbeitung</th><th>Warmer Mod-Start</th><th>Update Basis</th><th>Update Deutsch</th><th>Update Englisch-Mod</th><th>Draw Basis / Deutsch</th><th>Update p95 DE*</th></tr></thead><tbody>'''
for c,x in zip(catalog,rows):
 vals=[c['name'],f"{x['coldSeconds']:.3f} s",f"{x['warmSeconds']:.3f} s",f"{x['baseUpdateMs']:.3f} ms",f"{x['deUpdateMs']:.3f} ms",f"{x['enUpdateMs']:.3f} ms",f"{x['baseDrawMs']:.2f} / {x['deDrawMs']:.2f} ms",f"{x['deUpdateP95Ms']:.3f} ms"]
 body+='<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in vals)+'</tr>'
body+='''</tbody></table></div><p>* Größerer p95-Wert der beiden Deutsch-Läufe, kein gepooltes Gesamtperzentil.</p>
<h2>Was diese Zahlen aussagen</h2><p>Die Update-Spalte misst den Game:update-Aufruf. Draw misst Game:draw einschließlich möglicher GPU-/Treiber-/VSync-Wartezeiten; das ist keine Messung reiner CPU-Zeichenarbeit. 60 Bilder pro Sekunde entsprechen einem Gesamtbudget von 16,67 ms. Update- und Draw-Aufrufe sind lediglich Teile dieser Pipeline.</p>
<p>Parallel liefen andere Spieltests auf demselben Rechner. Dadurch schwanken CPU- und GPU-Zeiten auch innerhalb der Baseline deutlich. Kleine Unterschiede zwischen Sprachen sind unter diesen Bedingungen nicht belastbar. Für eine präzise Prozentangabe muss die Serie auf einem ansonsten ruhenden Rechner wiederholt werden.</p>
<p>Gemessen wurde die normale Oberwelt, kein vollständiger Durchlauf, keine Worst-Case-Kämpfe oder große Mod-Kombination. Die Messung rechtfertigt keine pauschale Behauptung „null Performance-Kosten“. Sie trennt die einmalige Verarbeitung, den weiterhin nötigen Cache-Start und den laufenden Spielbetrieb.</p>
<p>Die Startzeiten messen den Sprachmod-Einstieg, nicht den kompletten Launcher- oder Basisimport. Erstverarbeitung und Warmstart wurden pro Edition mit gezielt leerem beziehungsweise erneut verwendetem QA-Cache geprüft. Originale ROMs und Nutzerspielstände wurden dabei nicht verändert.</p></html>'''
(R/'mod/Performance.html').write_text(body)
print('PERFORMANCE_REPORT_OK',report['rawRuns'],report['frames'])
for x in rows:print(x['game'],'cold',round(x['coldSeconds'],3),'warm',round(x['warmSeconds'],3),'update delta',round(x['deUpdateMs']-x['baseUpdateMs'],3))
