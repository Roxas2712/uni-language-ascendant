from pathlib import Path
import json,statistics as st
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];O=R/'output/pdf';O.mkdir(exist_ok=True,parents=True)
rows=json.loads((R/'tools/rom_requirements.json').read_text());perf=json.loads((R/'build/performance-summary.json').read_text())
pdfmetrics.registerFont(TTFont('Doc','/System/Library/Fonts/Supplemental/Arial.ttf'));pdfmetrics.registerFont(TTFont('Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
W,H=842,595;c=canvas.Canvas(str(O/'Uni-Language-Ascendant-1.3.pdf'),pagesize=(W,H));c.setTitle('Uni-Language Ascendant 1.3 - Elf Editionen, Sprachwahl und Live-Vergleich')
BG='#101d2b';FG='#edf5f8';MUTED='#a9bdca';GREEN='#8fe0bc';BLUE='#9ac8ff'
def txt(x,y,s,size=10,color=FG,bold=False):
 c.setFillColor(HexColor(color));c.setFont('Bold' if bold else 'Doc',size);c.drawString(x,y,str(s))
def page(n,title,sub):
 c.setFillColor(HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
 txt(32,564,'UNI-LANGUAGE ASCENDANT / 1.3.0 / LIVE-DOKUMENTATION',9,GREEN,True)
 txt(32,533,title,24,bold=True);txt(32,513,sub,10,MUTED)
 c.setStrokeColor(HexColor('#324455'));c.line(32,32,810,32)
 txt(32,18,'16.10.2026 | Echte Spielbilder aus isoliertem Upstream-Build; Screenshots nur beschnitten/skaliert.',8,MUTED)
 txt(776,18,f'{n} / 8',8,MUTED)
def pic(path,x,y,w,h,crop=None):
 im=Image.open(path).convert('RGB')
 if crop:im=im.crop(crop)
 c.drawImage(ImageReader(im),x,y,w,h)
def pair(game,shot,y,crop=(288,64,768,416)):
 for x,lang,label,color in [(245,'en','ENGLISCH',BLUE),(530,'de','DEUTSCH',GREEN)]:
  txt(x,y,label,9,color,True);pic(R/f'build/comparison/{game}-{shot}-{lang}.png',x,y-170,264,158,crop)
page(1,'Elf Editionen. Eine eigenständige Mod.','Gen1: Rot, Blau, Gelb · Gen2: Gold, Silber, Kristall · Gen3: alle fünf Editionen')
pic(R/'build/firered-startup.png',32,86,520,390)
for i,line in enumerate(['Vor dem Titelbild','Zuerst: eine von neun Menüsprachen.','Danach: Englisch oder Deutsch im Spiel.','','Menüsprache ist separat gespeichert.','Mit L jederzeit vor Spielstart ändern.','','Version + SHA-1 sind direkt sichtbar.','Tab blättert durch die ROM-Liste.','','Spielsprachwechsel: Engine-Neustart,','danach Edition im Launcher starten.']):
 txt(574,463-i*23,line,11 if i else 15,GREEN if i==0 else FG,i==0)
c.showPage()
page(2,'Welche ROMs werden benötigt?','Pro Edition: US-Basis plus deutsche ROM. Diese SHA-1-Prüfsummen gelten für die komplette Datei.')
txt(32,483,'Edition',10,bold=True);txt(158,483,'US / ENGLISCH · 1.0 / REVISION 0',10,BLUE,True);txt(485,483,'DEUTSCH · 1.0, AUSSER SAPHIR 1.1',10,GREEN,True)
for i,row in enumerate(rows):
 y=454-i*34
 txt(32,y,row['name'],11,bold=True);txt(32,y-13,'Gen '+str(row['generation']),8,MUTED)
 for x,source in [(158,row['base']),(485,row['sources'][0])]:
  c.setFillColor(HexColor(FG));c.setFont('Courier',8);c.drawString(x,y,source['sha1'])
  txt(x,y-13,'Revision '+('1 / 1.1' if row['game']=='sapphire' and x==485 else '0 / 1.0'),8,MUTED)
 c.setStrokeColor(HexColor('#263747'));c.line(32,y-20,810,y-20)
txt(32,57,'Die vorhandene Saphir-Datei (99f7ad71...) weicht ab und wird abgelehnt. Erwartet: 7e6e034f... .',9,GREEN)
txt(32,43,'Feuerrot DE und Saphir DE sind mit SHA-1-identischen Referenz-Builds getestet. Eigene ROMs werden nicht mitgeliefert.',8,MUTED)
c.showPage()
for n,g,name,where in [(3,'firered','Feuerrot','Vertania City'),(4,'sapphire','Saphir','Rosaltstadt')]:
 page(n,name+': Center und Markt',where+' · gleiche Karte und Position · deutsche Beschriftung aus den ROM-Kacheln')
 txt(32,466,'Pokémon-Center',14,bold=True);txt(32,438,'P.C wird zu POKé.',11,MUTED);pair(g,'center',478)
 txt(32,252,'Pokémon-Markt',14,bold=True);txt(32,224,'MART wird zu MRKT.',11,GREEN);txt(32,204,'So steht es in der deutschen ROM.',10,MUTED);pair(g,'mart',264)
 c.showPage()
page(5,'Gen3: alle fünf Editionen im Spiel','Deutsche ROM-Menüs und Namen · unveränderte Werte, Regeln und Speicherformate des US-Basisspiels')
for i,g in enumerate(['firered','leafgreen','ruby','sapphire','emerald']):
 x=32+(i%3)*264;y=290-(i//3)*220
 label=next(r['name'] for r in rows if r['game']==g)
 txt(x,y+185,label,13,GREEN,True);pic(R/f'build/comparison/{g}-summary-de.png',x,y,248,174,(0,48,1024,768))
txt(560,228,'Profilumfang',14,bold=True)
for i,line in enumerate(['Dialoge, Namen und Beschreibungen','Titel, Schriften und Menü-Grafiken','Welt-Tilesets und Beschilderung','','Zusätzliche Engine-Texte können','weiterhin Englisch sein. Kein','vollständiger Spieldurchlauf-Test.']):txt(560,203-i*19,line,10,MUTED)
c.showPage()
page(6,'Gen1 und Gen2: sechs geprüfte Editionen','Bereits aufgenommene Live-Vergleiche · Markt- und Center-Grafiken stammen aus der jeweiligen deutschen ROM')
for i,g in enumerate(['red','blue','yellow','gold','silver','crystal']):
 x=32+(i%3)*264;y=284-(i//3)*220;label=next(r['name'] for r in rows if r['game']==g)
 txt(x,y+192,label,13,GREEN,True);pic(R/f'build/gb-comparison/{g}-mart-de.png',x,y,248,186)
c.showPage()
page(7,'Performance: Verarbeitung und Spielbetrieb','Lokale Vergleichsmessungen · Basisspiel ohne Mod, Englisch mit Mod und Deutsch mit Mod')
headers=[(32,'Edition'),(170,'Erstverarbeitung'),(295,'Cache-Start'),(410,'Update EN / DE'),(560,'Draw EN / DE'),(705,'Update p95 DE*')]
for x,t in headers:txt(x,480,t,10,GREEN,True)
for i,row in enumerate(perf['games']):
 y=451-i*28;name=next(r['name'] for r in rows if r['game']==row['game'])
 vals=[name,f"{row['coldSeconds']:.2f} s",f"{row['warmSeconds']:.2f} s",f"{row['baseUpdateMs']:.3f} / {row['deUpdateMs']:.3f} ms",f"{row['baseDrawMs']:.2f} / {row['deDrawMs']:.2f} ms",f"{row['deUpdateP95Ms']:.3f} ms"]
 for (x,_),v in zip(headers,vals):txt(x,y,v,9)
for i,line in enumerate(['Je Edition zwei Vergleichsläufe pro Baseline/Deutsch, zusätzlich ein englischer Mod-Lauf.',
 '360-900 gemessene Overworld-Frames pro Lauf. Erstverarbeitung und Cache-Start separat gemessen.',
 'Draw misst den gesamten Aufruf inklusive möglicher GPU-/VSync-Wartezeit, nicht reine CPU-Arbeit.',
 'Parallel liefen andere Spieltests. Kleine Differenzen sind nicht belastbar. * Größerer p95 der zwei DE-Läufe.',
 'Die Startauswahl entfernt ihre Frame-Wrapper nach Bestätigung. Während des Spiels wird keine ROM neu dekodiert.']):txt(32,128-i*17,line,9,MUTED)
c.showPage()
page(8,'Was ist fertig, was bleibt erweiterbar?','Getestete Profile und klare Grenzen')
sections=[('Als Mod verfügbar',[
 'Alle elf Editionen, einschließlich Feuerrot DE 1.0 und Saphir DE 1.1.',
 'Sprachauswahl vor dem Titelbild, Speicherung pro Edition und Wechsel per Engine-Neustart.',
 'Prüfung von ROM-Größe, MD5 und SHA-1. Unbekannte Revisionen werden nicht stillschweigend akzeptiert.',
 'Einmalige Sprachverarbeitung mit geprüftem lokalen Cache; keine ROM in der ZIP.']),
 ('Geprüft',[
 'Start, deutsche Daten, unveränderte Spielwerte, Grafikvergleich und Cache-Wiederverwendung.',
 'Bryans Upstream-Commit 1925fa9f97661f1e2d0922f7c6eb9546d262fd29: 2.039 Quelldateien unverändert.',
 'macOS / LÖVE 12 mit bekanntem Metal-Konfigurationsfix; kein vollständiger Spielverlauf.']),
 ('Erweiterungen',[
 'Neue Sprache: geprüftes ROM-Profil, Import-Eintrag, Zeichensatz und bei Bedarf Laufzeitadapter.',
 'Neue Generation: zusätzlicher Adapter und Unterstützung der Spielengine im Recompiler.',
 'Spiel: Deutsch/Englisch. Menü: DE, EN, FR, IT, ES, JA, KO, Chinesisch vereinfacht/traditionell.',
 'Emerald USA/Europe (BPEE) enthält keine weiteren vollständigen Sprachpakete.']),
 ('Für deinen nächsten Import',[
 'Deutsche Feuerrot-ROM gemäß SHA-1-Liste bereitstellen.',
 'Saphir-Datei neu prüfen: erwartet 7e6e034f..., vorhanden 99f7ad71... mit abweichendem Audiobereich.'])]
y=472
for title,lines in sections:
 txt(32,y,title,15,GREEN,True);y-=25
 for line in lines:txt(32,y,line,10);y-=20
 y-=17
c.showPage();c.save();print(O/'Uni-Language-Ascendant-1.3.pdf')
