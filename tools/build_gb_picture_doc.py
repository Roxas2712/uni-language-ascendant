from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];S=R/'build/gb-comparison';O=R/'output/pdf';O.mkdir(exist_ok=True,parents=True)
pdfmetrics.registerFont(TTFont('Doc','/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
W,H=595,842
c=canvas.Canvas(str(O/'Gen1-Gen2-ROM-Sprachmod-Ingame.pdf'),pagesize=(W,H))
c.setTitle('ROM Language Source 1.2.0 - Gen1 und Gen2 im Live-Vergleich');c.setAuthor('Lokale Ingame-Dokumentation')
BG='#101d2b';FG='#edf5f8';MUTED='#a9bdca';GREEN='#8fe0bc';BLUE='#9ac8ff'
def txt(x,y,s,size=10,color=FG,bold=False):
 c.setFillColor(HexColor(color));c.setFont('Bold' if bold else 'Doc',size);c.drawString(x,y,s)
def page(n,title,sub):
 c.setFillColor(HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
 txt(28,810,'ROM LANGUAGE SOURCE  /  1.2.0',9,GREEN,True)
 txt(28,777,title,23,bold=True);txt(28,756,sub,10,MUTED)
 c.setStrokeColor(HexColor('#324455'));c.line(28,35,567,35)
 txt(28,20,'16.10.2026  |  Echte Spielbilder aus Bryans unverändertem Recompiler*',8,MUTED)
 txt(540,20,f'{n} / 7',8,MUTED)
def pic(game,shot,lang,x,y,w,h):
 im=Image.open(S/f'{game}-{shot}-{lang}.png').convert('RGB')
 c.drawImage(ImageReader(im),x,y,w,h)
def pair(game,shot,label,y):
 txt(28,y,label,11,bold=True)
 txt(28,y-19,'ENGLISCH / US-BASIS',8,BLUE,True);txt(306,y-19,'DEUTSCH / ROM-MOD',8,GREEN,True)
 pic(game,shot,'en',28,y-215,261,195.75);pic(game,shot,'de',306,y-215,261,195.75)
games=[('red','Rot','Kanto / Vertania City',2582),('blue','Blau','Kanto / Vertania City',2582),('yellow','Gelb','Kanto / Vertania City',2695),('gold','Gold','Johto / Rosalia City',3044),('silver','Silber','Johto / Rosalia City',3044),('crystal','Kristall','Johto / Rosalia City',3991)]
page(1,'Sechs Editionen. Eine Sprachmod.','Gen1 + Gen2: eigene deutsche ROM über dem passenden US-Basisspiel.')
txt(28,715,'Der sichtbare Unterschied',14,bold=True)
# Same full scene, English versus German. A separate sign enlargement below.
txt(28,692,'ENGLISCH',9,BLUE,True);txt(306,692,'DEUTSCH',9,GREEN,True)
pic('gold','center','en',28,489,261,195.75);pic('gold','center','de',306,489,261,195.75)
txt(28,465,'MART wird MRKT. Die Grafik stammt aus der deutschen ROM.',11,GREEN,True)
txt(28,433,'Einmal importieren, danach aus dem lokalen Cache starten',13,bold=True)
for i,line in enumerate([
 '1. Das jeweilige US-Spiel regulär importieren.',
 '2. Mod-ZIP installieren und die passende deutsche ROM auswählen.',
 '3. Spiel starten: Texte und Grafiken werden einmal verarbeitet.',
 '4. Weitere Starts verwenden den geprüften lokalen Cache.',
 'Zum Wechsel auf Englisch: Mod deaktivieren und neu starten.'
]):txt(28,408-i*20,line,10)
txt(28,290,'Was geprüft wurde',13,bold=True)
for i,line in enumerate([
 'Alle sechs ROM-Paare: Start, Cache-Neustart, deaktivierte Mod,',
 'Texte, Grafikvergleich sowie unveränderte Pokémon- und Attackenwerte.',
 '48 Live-Aufnahmen: Titel, Center, Markt und Stadtschild auf beiden Sprachen.',
 'Die nächsten Seiten zeigen jeweils dieselbe Karte und Spielerposition.'
]):txt(28,266-i*17,line,10)
txt(28,177,'Grenzen der Aussage',13,bold=True)
for i,line in enumerate([
 'Die Dialogzahlen beziehen sich auf die zugeordnete Referenz, inklusive Leer-Slots.',
 'Recompiler-Zusatzmenüs und dynamische Engine-Texte können Englisch bleiben.',
 'Kein vollständiger Spieldurchlauf. Weitere Sprachen brauchen geprüfte Profile.',
 'Die verteilte Mod enthält keine ROM, keine extrahierten Dialoge und keine Bilder.',
 '*Quellstand 1925fa9; macOS mit separatem Metal-Konfigurationsfix.',
 'Bewegliche NPCs und Animationen können sich zwischen den Aufnahmen unterscheiden.'
]):txt(28,155-i*15,line,8.8,MUTED)
c.showPage()
for n,(g,name,place,count) in enumerate(games,2):
 page(n,name+' / Englisch und Deutsch',place+'  |  '+f'{count:,}'.replace(',','.')+' zugeordnete Dialogeinträge')
 pair(g,'center','01  Pokémon-Center / Front',731)
 pair(g,'mart','02  Markt / Front und Beschriftung',505)
 pair(g,'dialogue','03  Stadtschild / Originaldialog und Schrift',279)
 c.showPage()
c.save()
# Native-resolution sign comparison suitable for a quick in-chat preview.
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',30)
preview=Image.new('RGB',(1100,420),'#101d2b');d=ImageDraw.Draw(preview)
d.text((30,18),'GEN1  /  MART  →  MRKT',font=font,fill='#edf5f8')
for i,lang in enumerate(['en','de']):
 d.text((30+i*550,73),'ENGLISCH' if lang=='en' else 'DEUTSCH',font=font,fill='#9ac8ff' if i==0 else '#8fe0bc')
 im=Image.open(S/f'red-mart-{lang}.png').convert('RGB').crop((500,275,600,320)).resize((500,225),Image.Resampling.NEAREST)
 preview.paste(im,(30+i*550,130))
preview.save(O/'Gen1-MART-MRKT.png')
print(O/'Gen1-Gen2-ROM-Sprachmod-Ingame.pdf')
