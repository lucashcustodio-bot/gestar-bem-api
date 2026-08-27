#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import numpy as np, os

W,H=1080,1350; OUT="/home/claude/slides_v4"
GF="/usr/share/fonts/truetype/google-fonts"
os.makedirs(OUT,exist_ok=True)

def lora(size,bold=False):
    f=ImageFont.truetype(f"{GF}/Lora-Variable.ttf",size)
    try: f.set_variation_by_axes([700 if bold else 420])
    except: pass
    return f
def pp(size,weight="Regular"):
    w={"SemiBold":"Bold","ExtraLight":"Light"}.get(weight,weight)
    if w not in {"Regular","Medium","Bold","Light"}: w="Regular"
    return ImageFont.truetype(f"{GF}/Poppins-{w}.ttf",size)

BG=(20,16,12); CREAM=(244,237,224); DIM=(144,134,116)
GOLD=(196,163,96); GOLD2=(56,44,18); ROSE=(192,106,94); ROSE2=(62,22,20)

def grain(img,s=10):
    arr=np.array(img).astype(np.float32)
    np.random.seed(7)
    return Image.fromarray(np.clip(arr+np.random.normal(0,s,arr.shape),0,255).astype(np.uint8))

img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)

# gradiente inferior
for py in range(760,H):
    t=(py-760)/(H-760)
    r=int(BG[0]+(ROSE2[0]-BG[0])*t*0.52)
    g=int(BG[1]+(ROSE2[1]-BG[1])*t*0.52)
    b=int(BG[2]+(ROSE2[2]-BG[2])*t*0.52)
    d.line([(0,py),(W,py)],fill=(r,g,b))

# sidebar
d.rectangle([0,0,9,H],fill=GOLD); d.rectangle([15,0,17,H],fill=GOLD2)

# "E" fantasma
el=Image.new("RGB",(W,H),BG); ed=ImageDraw.Draw(el)
fe=lora(820,bold=True); ew=int(ed.textlength("E",font=fe))
ed.text((W-ew+170,190),"E",font=fe,fill=(28,22,16))
img=Image.blend(img,el,0.68); d=ImageDraw.Draw(img)

# topo
d.line([(54,82),(W-54,82)],fill=GOLD2,width=1)
d.text((54,44),"G E S T A R   B E M",font=pp(22,"Light"),fill=DIM)
d.text((54,106),"No. 01",font=pp(20,"Light"),fill=GOLD)

x=54; y=172
def text(t,f,c,g):
    global y; d.text((x,y),t,font=f,fill=c)
    a,de=f.getmetrics(); y+=a+de+g
def hline(col,w,length,g):
    global y; d.line([(x,y),(x+length,y)],fill=col,width=w); y+=g

# enjoo
text("enjoo",      lora(126,True), CREAM, 8)
hline(GOLD,2,370,16)
text("na gravidez",lora(54),       DIM,   42)
text("não é",      lora(86,True),  CREAM, 8)
text("frescura.",  lora(102,True), ROSE,  24)
hline((42,34,24),1,190,20)
text("Tem explicação.",    pp(31,"Light"), DIM, 4)
text("E tem o que fazer.",pp(31,"Light"), DIM, 32)

# hint
fh=pp(22,"Light"); col=(80,72,60)
d.text((x,y),"arraste para ver",font=fh,fill=col)
aw=int(d.textlength("arraste para ver",font=fh))
ax,ay=x+aw+12,y+12
for pts in [[(ax,ay),(ax+32,ay)],[(ax+32,ay),(ax+21,ay-7)],[(ax+32,ay),(ax+21,ay+7)]]:
    d.line(pts,fill=col,width=2)
a,de=fh.getmetrics(); y+=a+de+48

# divisor + citação
hline((44,36,26),1,W-108,16)
d.text((x,y),"\u201c",font=lora(56,True),fill=GOLD)
a,de=lora(56,True).getmetrics(); y+=a+de+6
text("Seu corpo está trabalhando", lora(43), CREAM, 2)
text("por você e pelo bebê.",      lora(43), CREAM, 12)
text("— Jéssica D'Agostini · Nutricionista", pp(21,"Light"), DIM, 0)

print("content ends at y=",y)

# rodapé
d.line([(54,H-84),(W-54,H-84)],fill=(36,28,20),width=1)
ff=pp(22,"Light")
d.text((54,H-60),"@gestarbem_",font=ff,fill=DIM)
d.ellipse([W//2-3,H-47,W//2+3,H-41],fill=GOLD)
t2="por Jéssica D'Agostini"
d.text((W-54-int(d.textlength(t2,font=ff)),H-60),t2,font=ff,fill=DIM)

img=grain(img,10)
img.save(f"{OUT}/cover_ok.png"); print("saved")
