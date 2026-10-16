"""Build the small PT-BR in-game QA document from actual local captures."""
from pathlib import Path
import base64,html,json,statistics

ROOT=Path(__file__).resolve().parents[1]
qa=ROOT/'build/ptbr-qa'
runs=[]
for path in sorted([*qa.glob('*performance-[12].log'),*qa.glob('*-remainder-performance.log')]):
    for line in path.read_text().splitlines():
        if line.startswith('PERFORMANCE_JSON '):
            row=json.loads(line[len('PERFORMANCE_JSON '):]);row['run']=path.stem;runs.append(row)
assert len(runs)==10
report={'format':1,'status':'preview-not-all-games-complete','scene':'Oldale Town in each corresponding game',
        'frames_per_run':360,'total_measured_frames':sum(r['draw']['n'] for r in runs),
        'background_load':'Other independently running game instances were active. These are exploratory comparisons, not an isolated performance certification.',
        'mapped_keys':15655,'edition_mapped_keys':{'emerald':15655,'ruby':13457,'sapphire':13457},'full_playthrough':False,'live_battle':'scripted wild battle, fixed Tackle fixture, victory and return to field','runs':runs}
checks = {
    'pt-BR-remainder-regression.log': ['LANGUAGE_LIVE_OK', 'LANGUAGE_BATTLE_OK', 'LANGUAGE_HEALING_OK', 'LANGUAGE_DIALOGUE_EVIDENCE'],
    'en-english-regression.log': ['LANGUAGE_LIVE_OK', 'LANGUAGE_BATTLE_OK'],
    'en-healing-regression.log': ['LANGUAGE_LIVE_OK', 'LANGUAGE_HEALING_OK'],
    'en-menu-final.log': ['PTBR_MENU_OK'],
    'pt-BR-picker-final.log': ['RELEASE_UI_OK'],
    'de-german-regression.log': ['LANGUAGE_LOAD '],
    'fr-regression.log': ['LANGUAGE_LOAD '],
    'it-regression.log': ['LANGUAGE_LOAD '],
    'es-regression.log': ['LANGUAGE_LOAD '],
    'install-preview3.log': ['PTBR_INSTALL_OK'],
    'ruby-pt-BR-remainder-regression.log': ['LANGUAGE_HEALING_OK', 'LANGUAGE_LIVE_OK'],
    'sapphire-pt-BR-remainder-regression.log': ['LANGUAGE_HEALING_OK', 'LANGUAGE_DEX_OK', 'LANGUAGE_LIVE_OK'],
    'en-real-npc-dialogues.log': ['LANGUAGE_DIALOGUES_OK'],
    'pt-BR-ingrain.log': ['LANGUAGE_BATTLE_DIALOGUES_OK'],
    'en-ingrain.log': ['LANGUAGE_BATTLE_DIALOGUES_OK'],
    'ruby-pt-BR-ingrain.log': ['LANGUAGE_BATTLE_DIALOGUES_OK'],
    'sapphire-pt-BR-ingrain.log': ['LANGUAGE_BATTLE_DIALOGUES_OK'],
}
report['live_checks'] = []
for name, markers in checks.items():
    log = (qa/name).read_text()
    assert all(marker in log for marker in markers), f'Missing QA result: {name}'
    assert 'LANGUAGE_LIVE_FAILED' not in log, name
    report['live_checks'].append({'log':name, 'passed_markers':markers})
report['authored_keys']={'emerald':1544,'ruby':733,'sapphire':1142}
report['authored_prose_entries']={'emerald':937,'ruby':218}
report['dialogue_evidence']=[]
for name in ('pt-BR-remainder-regression.log','en-real-npc-dialogues.log','pt-BR-ingrain.log','en-ingrain.log','ruby-pt-BR-ingrain.log','sapphire-pt-BR-ingrain.log'):
    for line in (qa/name).read_text().splitlines():
        for marker in ('LANGUAGE_DIALOGUE_EVIDENCE ','LANGUAGE_BATTLE_DIALOGUE_EVIDENCE '):
            if line.startswith(marker):
                row=json.loads(line[len(marker):]);row['log']=name
                report['dialogue_evidence'].append(row)
assert len(report['dialogue_evidence'])==10
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/PT-BR-QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
parts=[]
shots=[('ptbr-menu.png','Menu em português','Das Mod-Menü lässt sich unabhängig von der Spielsprache wählen. Zehn Menüsprachen, Rücksprung und Profil-Reset sind verfügbar.'),
       ('ptbr-game-language.png','Die passende Sprach-ROM','Die Spielauswahl zeigt nur importierte Profile. Bei PT-BR steht direkt dabei, dass die Fanübersetzung noch englische Texte enthält.'),
       ('pt-BR-title.png','Esmeralda','Titelgrafik und Start-Schriftzug stammen aus der lokal eingelesenen Zambrakas-ROM.'),
       ('pt-BR-center.png','Pokémon-Center von außen','Die Weltgrafiken werden aus der Sprach-ROM gelesen; Kartendaten und Spielablauf bleiben bei der US-Basis.'),
       ('pt-BR-mart.png','Das Ladenschild bleibt MART','Diese Übersetzung ändert die Ladenfront nicht. Der Import erzeugt keine erfundene portugiesische Beschriftung.'),
       ('pt-BR-healing.png','Schwester Joy: tatsächlicher Heilungsablauf','Eigene PT-BR-Korrektur: „Seus POKéMON estão com a saúde recuperada.“ Im echten Gespräch über die Theke getestet: verletztes Pokémon heilen lassen, Dialog beenden und Feldsteuerung zurückerhalten. Kein künstlich eingeblendeter Dialog.'),
       ('sapphire-pt-BR-dex-abra-1.png','Saphir: eigener Pokédex-Text','203 editionsspezifische Einträge wurden neu übersetzt. 405 Seiten sind mit der tatsächlichen Spielschrift auf Zeilenbreite und Seitenlänge geprüft. Sichtbare englische Grafikbeschriftungen wie PAGE bleiben noch offen.'),
       ('pt-BR-summary.png','Statusbildschirm','Übersetzte Texte, Schrift und Oberflächengrafiken im laufenden Spiel.'),
       ('pt-BR-battle.png','RATTATA apareceu!','Live-Kampf gegen ein wildes Rattata. Mit einer festen Tackle-Testattacke bis zum Sieg und zurück ins Feld geprüft.')]
for filename,title,caption in shots:
    data=base64.b64encode((qa/filename).read_bytes()).decode()
    parts.append(f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(title)}"><figcaption><h2>{html.escape(title)}</h2><p>{html.escape(caption)}</p></figcaption></figure>')
comparisons=[]
for case,title,caption in [
 ('rooftop-weather','Gesperrte Dachterrasse','Echte NPC-Interaktion im Kaufhaus von Seegrasulb City. Testzustand: das Unwetter der legendären Pokémon ist aktiv. Beide Sprachläufe erreichen das Dialogende.'),
 ('captain-scanner','Das verlassene Schiff','Echte NPC-Interaktion im Kapitänsbüro. Testzustand: der Scanner wurde bereits getauscht. Keine direkte Einblendung eines Textschlüssels.'),
 ('lottery-prize','Lotterie: Spielername und Preis','Echtes Gespräch mit der Lotterie-Angestellten. Im Test wartet ein Meisterball auf Abholung. Der Name TEST erscheint; der Beutel erhält genau einen Meisterball. Der Test erzeugt keinen Zufallsgewinn.'),
 ('ingrain','Verwurzler im tatsächlichen Kampf','Sonnkern verwendet Verwurzler gegen ein wildes Rattata. Der Test prüft den Verwurzelungszustand, die angezeigte Meldung und anschließend Sieg mit Absorber samt Rückkehr ins Feld.')]:
    images=[]
    for lang,label in [('en','English'),('pt-BR','Português (Brasil)')]:
        filename=('emerald-' if case=='ingrain' else '')+lang+'-'+case+'.png'
        data=base64.b64encode((qa/filename).read_bytes()).decode()
        images.append(f'<div><b>{label}</b><img src="data:image/png;base64,{data}" alt="{html.escape(title)} – {label}"></div>')
    comparisons.append('<section class="panel"><h2>'+html.escape(title)+'</h2><div class="comparison">'+''.join(images)+'</div><p>'+html.escape(caption)+'</p></section>')
rows=''.join(f'<tr><td>{html.escape(r['game'])} · {html.escape(r["language"])} · {html.escape(r["run"].split("-")[-1])}</td><td>{r["draw"]["p50Ms"]:.2f} ms</td><td>{r["draw"]["p95Ms"]:.2f} ms</td><td>{r["modLoadSeconds"]:.2f} s</td><td>{r["luaMemoryKiB"]/1024:.1f} MiB</td></tr>' for r in runs)
body='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PT-BR · Uni-Language Ascendant</title>
<style>body{margin:0;background:#edf0df;color:#20303b;font:17px/1.55 system-ui}main{max-width:1060px;margin:auto;padding:30px}header{background:#cf3740;color:#fff8db;padding:32px;border:3px solid #20303b;border-radius:22px;box-shadow:0 6px #20303b}h1{font-size:42px;line-height:1.1}h2{font-size:23px;margin:0 0 8px}aside,.panel{background:#fffbea;border:2px solid #20303b;border-radius:16px;padding:22px;margin:28px 0}figure{margin:28px 0;background:#fffbea;border:2px solid #20303b;border-radius:16px;overflow:hidden}img{display:block;width:100%;image-rendering:pixelated}figcaption{padding:24px}figcaption p{margin:0}code{overflow-wrap:anywhere;font-size:14px}table{width:100%;border-collapse:collapse;font-size:15px}td,th{padding:10px;text-align:left;border-bottom:1px solid #b8c1b4}a{color:#08676e}.table{overflow:auto}small{color:#52666f}footer{padding:25px 0}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:12px}.comparison img{margin-top:8px}@media(max-width:700px){.comparison{grid-template-columns:1fr}}</style>
<main><header><p>UNI-LANGUAGE ASCENDANT · PT-BR PREVIEW</p><h1>Seu mundo. Seu idioma.</h1><p>Emerald und das Mod-Menü im Live-Test · 16. Oktober 2026</p></header>
<aside><b>Der Gesamtauftrag ist noch nicht abgeschlossen.</b> Dieses Preview bietet das PT-BR-Menü und ein getestetes Importprofil für Emerald/Zambrakas 2013. Rubin und Saphir haben zusätzliche Entwicklungsprofile mit unvollständiger Sprachprüfung; die übrigen acht Editionen bleiben ausgeblendet. Der Emerald-Patch selbst enthält weiterhin englische Texte; 15.655 zugeordnete Textschlüssel bedeuten keine vollständig portugiesische Übersetzung.</aside>
<section class="panel"><h2>Korrektur zum früheren Screenshot</h2><p>„Missão concluída! Poções, saúde e proteção.“ war eine künstliche Schriftprobe im Rubin-Test, kein Spieldialog. Dieses Bild belegt keine korrekte Übersetzung von Schwester Joy. Auch die frühere Emerald-Bildunterschrift war unzureichend: Der Fanpatch enthält dort selbst „Missão cumprida“, das wir jetzt durch eine eigene, sinngemäße Übersetzung ersetzen. Die Aufnahme unten stammt aus dem tatsächlichen Heilungsablauf.</p></section>
'''+''.join(comparisons)+''.join(parts)+'''
<section class="panel"><h2>Neue eigene Übersetzungen</h2><p>937 Emerald-Texte und 218 zusätzliche Rubin-Texte sind neu übersetzt. Die eigenen Korrekturen decken einschließlich identischer Verweise 1.544 Emerald-, 733 Rubin- und 1.142 Saphir-Schlüssel ab. Saphir enthält weiterhin seine 203 eigenen Pokédex-Einträge. Andere Editionen erhalten eine Korrektur nur bei identischem vollständigem Ausgangstext samt Variablen; editionsspezifische Korrekturen haben Vorrang.</p><p>Der erweiterte Resttext-Scan berücksichtigt jetzt auch kurze Texte und Wörter mit Akzenten. Die Prüfliste enthält noch offene Kandidaten, darunter Eigennamen und tatsächlich englische Meldungen. Sie ist kein Beweis einer vollständigen Übersetzung. Textprüfungen und Live-Belege sind getrennt erfasst.</p></section><section class="panel"><h2>Geprüft</h2><p>Alle 15.655 Textschlüssel wurden einem Profil zugeordnet. Der vollständige Import funktioniert kalt und aus dem Compile-Cache. Live geprüft wurden Titel, Center und Ladenfront, tatsächlicher Heilungsdialog einschließlich KP-Erholung und Rückkehr zur Feldsteuerung, Akzente, Statusbildschirm, Speichern/Laden, ein wilder Kampf bis zum Sieg und zurück ins Feld, Menüwahl, Maus-/Tastatur-Navigation, Zurück, Reset-Abbruch und die Glyphen sämtlicher zehn Menüsprachen. Mit dem echten Mod-Installer geprüft: ZIP-Installation, Update mit Profilerhalt, Deinstallation mit Profil-Löschung und frische Neuinstallation. Separat geprüft: Profil-Reset, falsche Importidentitäten, Decoder-Aufräumen, ungültige Speicherzugriffe und BPS-Prüfsummen.</p><p>Kein kompletter Spieldurchlauf, keine vollständige sprachliche Prüfung aller Dialoge und kein vollständiger Test sämtlicher Kämpfe, Link-Funktionen oder Endgame-Ereignisse.</p></section>
<section class="panel"><h2>Performance: Oldale Town, zehn Läufe</h2><p>Je 360 gemessene Frames nach 180 Aufwärmframes, insgesamt 3.600 Messframes. Zwei aktuelle Emerald-Läufe nach den Dialogergänzungen; vier Emerald-Läufe aus dem ersten Preview; zusätzlich je ein älterer EN/PT-BR-Lauf für Rubin und Saphir. Rubin: 14,81/14,82 ms Median; Saphir: 14,81/15,04 ms. Aktuell Emerald: 13,51 ms Median bei Englisch und 13,83 ms bei PT-BR; 4,89 s Mod-Ladezeit trotz Compile-Cache. Der gemessene Lua-Heap liegt bei rund 99/222 MiB, ohne erzwungene Speicherbereinigung. Diese kurzen Messungen unter paralleler Hintergrundlast belegen keinen fehlenden Performance-Einfluss. Der Compile-Cache erspart den erneuten ROM-Import; Laden und Speicherbedarf bleiben höher als bei Englisch.</p><div class="table"><table><tr><th>Sprache / Lauf</th><th>Zeichnen p50</th><th>p95</th><th>Mod laden</th><th>Lua-Heap*</th></tr>'''+rows+'''</table></div><p><small>*Kein erzwungener GC vor der Messung; der Lua-Heap ist kein genauer Prozess-RAM-Wert. Andere Spielinstanzen waren während der Messungen aktiv. Das ist ein orientierender Vergleich unter wechselnder Hintergrundlast, kein Nachweis von exakt null Performance-Einfluss. Kaltimporte dauerten in den bisherigen Läufen etwa 4–17 s; die Laufzeiten sind nicht auf einen unbelasteten Rechner übertragbar.</small></p></section>
<section class="panel"><h2>Deine benötigten Dateien</h2><p>Basis: Pokémon Emerald (USA, Europe), BPEE, Revision 0.<br><code>SHA-1 f3ae088181bf583e55daf962a92bb46f4f1d07b7</code></p><p>Sprach-ROM: eigener Basis-Dump mit Zambrakas 2013-12-08, ohne zusätzlichen Tag-/Nacht-Patch.<br><code>SHA-1 18a2b0acdba046c71b8677bb58c9ee7d36f7a91f</code></p><p>Der <a href="https://github.com/RetroAchievements/RAPatches/blob/main/GBA/Translation/Portuguese/668-PokemonEmerald-Portuguese.zip">BPS-Patch bei RetroAchievements</a> liefert mit dieser Basis die geprüfte Sprach-ROM. Übersetzungsautor: Zambrakas. Die Mod enthält weder ROM noch Patch oder extrahierte Originaltexte. Eigene Dialogkorrekturen werden separat mit Prüfsummen der zugehörigen US-Ausgangstexte geliefert.</p></section>
<section class="panel"><h2>Die übrigen Editionen</h2><p>Rot und Blau: Übersetzungsquellen gebaut; das Mod-Profil fehlt noch. Gelb: Quellbuild ebenfalls erstellt; Laufzeitprofil und Live-Test fehlen. Gold und Silber: Patch-Versionen lokal auf passende eigene Basis-ROMs angewendet; Laufzeitprofile und Live-Tests fehlen. Rubin: Live-Smoke-Test und Heilungsablauf geprüft, vollständige Sprachprüfung offen. Kristall: Patch beschafft, passende Basisrevision und Profil noch offen. Feuerrot und Blattgrün: Basisrevision 1.1 nachgebaut und die Übersetzungspatches angewendet; die verschobenen Textadressen müssen noch verifiziert und Laufzeitprofile erstellt werden. Saphir: eigene US-Basis mit der importierten Rubin-PT-BR-Textquelle, 13.047 exakt übereinstimmende Ausgangstexte wiederverwendet und 203 eigene Pokédex-Einträge ergänzt. Titel und Welt bleiben aus Saphir. Heilung, Pokédex, Kampf und Speichern/Laden geprüft; englische Grafikbeschriftungen und Attackennamen wie INGRAIN, ABSORB und TACKLE sowie weitere Sprachprüfung bleiben offen.</p><p>Nur Rubin und Saphir sind davon als Entwicklungsprofile aktiviert. Ein bestandener Smoke-Test ist keine vollständige sprachliche Freigabe.</p></section>
<footer>Uni-Language Ascendant · basiert auf <a href="https://github.com/bryanthaboi/gen1recomp">Gen1Recomp</a> von BOIS CLUB GAMES, LLC.</footer></main></html>'''
(ROOT/'mod/PT-BR.html').write_text(body)
print('PTBR_REPORT_OK',len(shots)+8,'screenshots',report['total_measured_frames'],'measured frames')
