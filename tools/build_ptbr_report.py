"""Build the small PT-BR in-game QA document from actual local captures."""
from pathlib import Path
import base64,html,json,statistics

ROOT=Path(__file__).resolve().parents[1]
qa=ROOT/'build/ptbr-qa'
runs=[]
for path in sorted(qa.glob('*performance-[12].log')):
    for line in path.read_text().splitlines():
        if line.startswith('PERFORMANCE_JSON '):
            row=json.loads(line[len('PERFORMANCE_JSON '):]);row['run']=path.stem;runs.append(row)
assert len(runs)==4
report={'format':1,'status':'preview-not-all-games-complete','scene':'EM_OLDALE_TOWN',
        'frames_per_run':360,'total_measured_frames':sum(r['draw']['n'] for r in runs),
        'background_load':'Other independently running game instances were active. These are exploratory comparisons, not an isolated performance certification.',
        'mapped_keys':15655,'full_playthrough':False,'live_battle':'scripted wild battle, fixed Tackle fixture, victory and return to field','runs':runs}
checks = {
    'pt-BR-live-final.log': ['LANGUAGE_LIVE_OK', 'LANGUAGE_BATTLE_OK'],
    'en-english-regression.log': ['LANGUAGE_LIVE_OK', 'LANGUAGE_BATTLE_OK'],
    'en-menu-final.log': ['PTBR_MENU_OK'],
    'pt-BR-picker-final.log': ['RELEASE_UI_OK'],
    'de-german-regression.log': ['LANGUAGE_LOAD '],
    'fr-regression.log': ['LANGUAGE_LOAD '],
    'it-regression.log': ['LANGUAGE_LOAD '],
    'es-regression.log': ['LANGUAGE_LOAD '],
    'install.log': ['PTBR_INSTALL_OK'],
}
report['live_checks'] = []
for name, markers in checks.items():
    log = (qa/name).read_text()
    assert all(marker in log for marker in markers), f'Missing QA result: {name}'
    assert 'LANGUAGE_LIVE_FAILED' not in log, name
    report['live_checks'].append({'log':name, 'passed_markers':markers})
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/PT-BR-QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
parts=[]
shots=[('ptbr-menu.png','Menu em português','Das Mod-Menü lässt sich unabhängig von der Spielsprache wählen. Zehn Menüsprachen, Rücksprung und Profil-Reset sind verfügbar.'),
       ('ptbr-game-language.png','Die passende Sprach-ROM','Die Spielauswahl zeigt nur importierte Profile. Bei PT-BR steht direkt dabei, dass die Fanübersetzung noch englische Texte enthält.'),
       ('pt-BR-title.png','Esmeralda','Titelgrafik und Start-Schriftzug stammen aus der lokal eingelesenen Zambrakas-ROM.'),
       ('pt-BR-center.png','Pokémon-Center von außen','Die Weltgrafiken werden aus der Sprach-ROM gelesen; Kartendaten und Spielablauf bleiben bei der US-Basis.'),
       ('pt-BR-mart.png','Das Ladenschild bleibt MART','Diese Übersetzung ändert die Ladenfront nicht. Der Import erzeugt keine erfundene portugiesische Beschriftung.'),
       ('pt-BR-accents.png','Missão · saúde','Originaler übersetzter Center-Dialog, für den Darstellungstest gezielt eingeblendet. Die ROM verwendet eigene Schriftzellen für ã, õ und í; die Mod ordnet sie passend zu.'),
       ('pt-BR-summary.png','Statusbildschirm','Übersetzte Texte, Schrift und Oberflächengrafiken im laufenden Spiel.'),
       ('pt-BR-battle.png','RATTATA apareceu!','Live-Kampf gegen ein wildes Rattata. Mit einer festen Tackle-Testattacke bis zum Sieg und zurück ins Feld geprüft.')]
for filename,title,caption in shots:
    data=base64.b64encode((qa/filename).read_bytes()).decode()
    parts.append(f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(title)}"><figcaption><h2>{html.escape(title)}</h2><p>{html.escape(caption)}</p></figcaption></figure>')
rows=''.join(f'<tr><td>{html.escape(r["language"])} · {html.escape(r["run"].split("-")[-1])}</td><td>{r["draw"]["p50Ms"]:.2f} ms</td><td>{r["draw"]["p95Ms"]:.2f} ms</td><td>{r["modLoadSeconds"]:.2f} s</td><td>{r["luaMemoryKiB"]/1024:.1f} MiB</td></tr>' for r in runs)
body='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PT-BR · Uni-Language Ascendant</title>
<style>body{margin:0;background:#edf0df;color:#20303b;font:17px/1.55 system-ui}main{max-width:1060px;margin:auto;padding:30px}header{background:#cf3740;color:#fff8db;padding:32px;border:3px solid #20303b;border-radius:22px;box-shadow:0 6px #20303b}h1{font-size:42px;line-height:1.1}h2{font-size:23px;margin:0 0 8px}aside,.panel{background:#fffbea;border:2px solid #20303b;border-radius:16px;padding:22px;margin:28px 0}figure{margin:28px 0;background:#fffbea;border:2px solid #20303b;border-radius:16px;overflow:hidden}img{display:block;width:100%;image-rendering:pixelated}figcaption{padding:24px}figcaption p{margin:0}code{overflow-wrap:anywhere;font-size:14px}table{width:100%;border-collapse:collapse;font-size:15px}td,th{padding:10px;text-align:left;border-bottom:1px solid #b8c1b4}a{color:#08676e}.table{overflow:auto}small{color:#52666f}footer{padding:25px 0}</style>
<main><header><p>UNI-LANGUAGE ASCENDANT · PT-BR PREVIEW</p><h1>Seu mundo. Seu idioma.</h1><p>Emerald und das Mod-Menü im Live-Test · 16. Oktober 2026</p></header>
<aside><b>Der Gesamtauftrag ist noch nicht abgeschlossen.</b> Dieses Preview bietet das PT-BR-Menü und ein getestetes Importprofil für Emerald/Zambrakas 2013. Die anderen zehn Editionen sind in PT-BR noch ausgeblendet. Der Emerald-Patch selbst enthält weiterhin englische Texte; 15.655 zugeordnete Textschlüssel bedeuten keine vollständig portugiesische Übersetzung.</aside>
'''+''.join(parts)+'''
<section class="panel"><h2>Geprüft</h2><p>Alle 15.655 Textschlüssel wurden einem Profil zugeordnet. Der vollständige Import funktioniert kalt und aus dem Compile-Cache. Live geprüft wurden Titel, Center und Ladenfront, gezielt angezeigte Dialoge, Akzente, Statusbildschirm, Speichern/Laden, ein wilder Kampf bis zum Sieg und zurück ins Feld, Menüwahl, Maus-/Tastatur-Navigation, Zurück, Reset-Abbruch und die Glyphen sämtlicher zehn Menüsprachen. Mit dem echten Mod-Installer geprüft: ZIP-Installation, Update mit Profilerhalt, Deinstallation mit Profil-Löschung und frische Neuinstallation. Separat geprüft: Profil-Reset, falsche Importidentitäten, Decoder-Aufräumen, ungültige Speicherzugriffe und BPS-Prüfsummen.</p><p>Kein kompletter Spieldurchlauf, keine vollständige sprachliche Prüfung aller Dialoge und kein vollständiger Test sämtlicher Kämpfe, Link-Funktionen oder Endgame-Ereignisse.</p></section>
<section class="panel"><h2>Performance: gleicher Ort, vier Läufe</h2><p>Je 360 gemessene Frames nach 180 Aufwärmframes, insgesamt 1.440 Messframes. Beide Sprachen lagen bei rund 14–15 ms medianer Zeichenzeit. Der Compile-Cache erspart den erneuten ROM-Import; Laden und Speicherbedarf bleiben höher als bei Englisch.</p><div class="table"><table><tr><th>Sprache / Lauf</th><th>Zeichnen p50</th><th>p95</th><th>Mod laden</th><th>Lua-Heap*</th></tr>'''+rows+'''</table></div><p><small>*Kein erzwungener GC vor der Messung; der Lua-Heap ist kein genauer Prozess-RAM-Wert. Andere Spielinstanzen waren während der Messungen aktiv. Das ist ein orientierender Vergleich unter wechselnder Hintergrundlast, kein Nachweis von exakt null Performance-Einfluss. Kaltimporte dauerten in den bisherigen Läufen etwa 4–17 s; die Laufzeiten sind nicht auf einen unbelasteten Rechner übertragbar.</small></p></section>
<section class="panel"><h2>Deine benötigten Dateien</h2><p>Basis: Pokémon Emerald (USA, Europe), BPEE, Revision 0.<br><code>SHA-1 f3ae088181bf583e55daf962a92bb46f4f1d07b7</code></p><p>Sprach-ROM: eigener Basis-Dump mit Zambrakas 2013-12-08, ohne zusätzlichen Tag-/Nacht-Patch.<br><code>SHA-1 18a2b0acdba046c71b8677bb58c9ee7d36f7a91f</code></p><p>Der <a href="https://github.com/RetroAchievements/RAPatches/blob/main/GBA/Translation/Portuguese/668-PokemonEmerald-Portuguese.zip">BPS-Patch bei RetroAchievements</a> liefert mit dieser Basis die geprüfte Sprach-ROM. Übersetzungsautor: Zambrakas. Die Mod enthält weder ROM noch Patch oder extrahierte Spieltexte.</p></section>
<section class="panel"><h2>Die übrigen Editionen</h2><p>Rot und Blau: Übersetzungsquellen gebaut; das Mod-Profil fehlt noch. Gelb: Quellbuild wegen fehlender Grafikdateien noch offen. Gold, Silber und Rubin: Patch-Versionen lokal auf passende eigene Basis-ROMs angewendet; Laufzeitprofile und Live-Tests fehlen. Kristall sowie Feuerrot und Blattgrün: Patches beschafft; benötigte Basisrevisionen noch nicht vollständig verifiziert. Saphir: eigene Übersetzung begonnen, 13 Dialogentwürfe; 7.717 eindeutige Texteinheiten im Arbeitsbestand, davon 2.581 mit ungeprüften Emerald-Vorschlägen.</p><p>Keines dieser zehn PT-BR-Profile ist freigeschaltet oder als getestet ausgewiesen.</p></section>
<footer>Uni-Language Ascendant · basiert auf <a href="https://github.com/bryanthaboi/gen1recomp">Gen1Recomp</a> von BOIS CLUB GAMES, LLC.</footer></main></html>'''
(ROOT/'mod/PT-BR.html').write_text(body)
print('PTBR_REPORT_OK',len(shots),'screenshots',report['total_measured_frames'],'measured frames')
