from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
SHOTS=ROOT/'build/comparison'
OUT=ROOT/'output/pdf'
OUT.mkdir(parents=True,exist_ok=True)
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
pdfmetrics.registerFont(TTFont('Doc',FONT));pdfmetrics.registerFont(TTFont('DocBold',BOLD))
W,H=842,595
c=canvas.Canvas(str(OUT/'ROM-Sprachmod-Ingame-Vergleich.pdf'),pagesize=(W,H))
c.setTitle('ROM Language Source 1.1 - Ingame-Vergleich Deutsch / Englisch')
c.setAuthor('Lokale Live-Aufnahmen aus Gen1Recomp')
BG='#101D2B';FG='#EDF5F8';MUTED='#A9BDCA';GREEN='#8FE0BC';BLUE='#9AC8FF'
def text(x,y,s,size=10,color=FG,bold=False):
 c.setFillColor(HexColor(color));c.setFont('DocBold' if bold else 'Doc',size);c.drawString(x,y,s)
def page(n,title,sub):
 c.setFillColor(HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
 text(34,562,'ROM LANGUAGE SOURCE  /  LIVE-VERGLEICH  /  1.1.0',9,GREEN,True)
 text(34,532,title,23,bold=True);text(34,513,sub,10,MUTED)
 c.setStrokeColor(HexColor('#324455'));c.line(34,33,808,33)
 text(34,19,'16.10.2026  |  Gleiche Karte und Position. Echte Spielbilder, nur beschnitten und skaliert.',8,MUTED)
 text(759,19,f'{n} / 5',8,MUTED)
def pic(game,shot,lang,box,x,y,w,h):
 im=Image.open(SHOTS/f'{game}-{shot}-{lang}.png').convert('RGB').crop(box)
 # Nearest-neighbour scaling keeps screenshot pixels crisp in the PDF.
 factor=max(1,int(900/im.width));im=im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST)
 c.drawImage(ImageReader(im),x,y,width=w,height=h,mask='auto',preserveAspectRatio=True,anchor='c')
def row(game,shot,title,caption,y,box):
 text(34,y,title,12,bold=True)
 text(252,y,'ENGLISCH / US',9,BLUE,True);text(545,y,'DEUTSCH / MOD',9,GREEN,True)
 # A wide image column plus separate close-up of the sign on world pages.
 if shot=='summary':
  for x,lang in [(252,'en'),(545,'de')]:pic(game,shot,lang,box,x,y-182,263,164)
 else:
  for x,lang in [(252,'en'),(545,'de')]:
   pic(game,shot,lang,box,x,y-180,200,169)
   sx=375 if game=='leafgreen' else 570
   sy=283 if game=='leafgreen' else 278
   if shot=='gym':sx,sy=365,270
   crop=(sx,sy,sx+85,sy+45)
   pic(game,shot,lang,crop,x+205,y-74,58,31)
   text(x+205,y-87,'Detail',7,MUTED)
 # Short explanatory text in a dedicated left column.
 for i,line in enumerate(caption):text(34,y-28-i*16,line,10,MUTED)

page(1,'Blattgrün: Center und Markt','Vertania City | US LeafGreen + deutsche Blattgrün-ROM | Außenkacheln aus der ROM')
row('leafgreen','center','Pokémon-Center',['P.C wird zu POKé.','Die Buchstaben stecken','in den Gebäudekacheln.'],482,(288,64,704,416))
row('leafgreen','mart','Pokémon-Markt',['MART wird zu MRKT.','Das deutsche Kürzel ist','kein Darstellungsfehler.'],260,(288,64,704,416))
c.showPage()
page(2,'Blattgrün: Arena und Statusmenü','Auch Beschilderung und eingebettete Menütexte wechseln mit der Sprachquelle.')
row('leafgreen','gym','Arena',['GYM wird zu ARN.','Auch das freistehende','Schild ist lokalisiert.'],482,(208,32,704,416))
row('leafgreen','summary','Pokémon-Status',['BULBASAUR / BISASAM','OVERGROW / NOTDÜNGER','Angriff, Vert., Sp. Ang.','und weitere ROM-Texte.'],260,(0,64,1024,704))
c.showPage()
page(3,'Rubin: gleiche Welt, deutsche Schilder','Rosaltstadt | US Ruby 1.0 + deutsche Rubin-ROM 1.0')
row('ruby','center','Pokémon-Center',['P.C wird zu POKé.','Die deutschen Kacheln','werden im US-Spiel','gerendert.'],482,(320,64,768,416))
row('ruby','mart','Pokémon-Markt',['MART wird zu MRKT.','Geometrie, Karten und','Spielregeln stammen','weiter vom Basisspiel.'],260,(320,64,768,416))
c.showPage()
page(4,'Smaragd: Beschriftung aus der Sprach-ROM','Rosaltstadt | US Emerald + deutsche Smaragd-ROM')
row('emerald','center','Pokémon-Center',['P.C wird zu POKé.','Keine nachgezeichnete','Übersetzung: die Grafik','kommt aus deiner ROM.'],482,(320,64,768,416))
row('emerald','mart','Pokémon-Markt',['MART wird zu MRKT.','Alle 75 Welt-Tileset-Paare','dieser Edition werden','aus der Quelle erzeugt.'],260,(320,64,768,416))
c.showPage()
page(5,'Menüs und der neue Import-Cache','Rubin / Smaragd | Einmal verarbeiten, anschließend geprüfte lokale Daten wiederverwenden.')
row('ruby','summary','Rubin-Menü',['Deutsche Wertebezeichnungen','und Fähigkeitstexte.','Gleiche Testdaten und','gleicher Zufallsstartwert.'],482,(0,64,1024,704))
row('emerald','summary','Smaragd-Menü',['Aktuell geprüft: Deutsch','für Blattgrün, Rubin, Smaragd.','Weitere Sprachen benötigen','geprüfte Profile. Gen1/2 folgt','erst als separates Vorhaben.'],260,(0,64,1024,704))
c.save()

# A compact, readable preview focused on the exact sign pixels.
preview=Image.new('RGB',(1500,1070),BG);d=ImageDraw.Draw(preview)
f=ImageFont.truetype(FONT,26);b=ImageFont.truetype(BOLD,36);small=ImageFont.truetype(FONT,23)
d.text((40,28),'Blattgrün: die Schilder wechseln tatsächlich',font=b,fill=FG)
d.text((40,83),'Live im US-Basisspiel - mit deutscher ROM als Mod-Quelle',font=f,fill=MUTED)
d.text((420,150),'ENGLISCH',font=f,fill=BLUE);d.text((940,150),'DEUTSCH',font=f,fill=GREEN)
for i,(shot,label,crop) in enumerate([
 ('center','Pokémon-Center',(375,283,460,328)),
 ('mart','Pokémon-Markt',(375,283,460,328)),
 ('gym','Arena',(365,270,450,315))]):
 y=220+i*245;d.text((40,y+65),label,font=f,fill=FG)
 for x,lang in [(410,'en'),(930,'de')]:
  im=Image.open(SHOTS/f'leafgreen-{shot}-{lang}.png').crop(crop).resize((425,225),Image.Resampling.NEAREST)
  preview.paste(im,(x,y))
d.text((40,1000),'P.C → POKé   ·   MART → MRKT   ·   GYM → ARN',font=b,fill=GREEN)
preview.save(OUT/'Schilder-Englisch-Deutsch.png')
print(OUT/'ROM-Sprachmod-Ingame-Vergleich.pdf')
