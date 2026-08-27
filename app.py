"""
Gestar Bem — Backend multi-tema
6 identidades visuais distintas, cada uma com paleta + layout + elementos únicos
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os, io, zipfile, urllib.request, random, math

app = Flask(__name__)
CORS(app)

# ── fontes ────────────────────────────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

FONT_URLS = {
    "Lora-Regular.ttf":   "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "Lora-Bold.ttf":      "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "Poppins-Regular.ttf":"https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "Poppins-Medium.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
    "Poppins-Bold.ttf":   "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-Light.ttf":  "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Light.ttf",
}

def ensure_fonts():
    for name, url in FONT_URLS.items():
        dest = os.path.join(FONT_DIR, name)
        if not os.path.exists(dest):
            try:
                urllib.request.urlretrieve(url, dest)
                print(f"Fonte baixada: {name}")
            except Exception as e:
                print(f"Erro ao baixar {name}: {e}")

ensure_fonts()

def get_font(name, size):
    path = os.path.join(FONT_DIR, name)
    try:
        f = ImageFont.truetype(path, size)
        if "Lora" in name:
            try: f.set_variation_by_axes([700 if "Bold" in name else 450])
            except: pass
        return f
    except:
        return ImageFont.load_default()

def lora(size, bold=False):
    return get_font("Lora-Bold.ttf" if bold else "Lora-Regular.ttf", size)

def pp(size, weight="Regular"):
    m = {"Bold":"Bold","Medium":"Medium","Light":"Light",
         "Regular":"Regular","SemiBold":"Bold","ExtraLight":"Light"}
    return get_font(f"Poppins-{m.get(weight,'Regular')}.ttf", size)

W, H = 1080, 1350

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE TEMAS
# Cada tema define: bg, surface, accent, text, decorativo, layout_capa
# ══════════════════════════════════════════════════════════════════════════════

THEMES = {

    "roxo": {
        "name": "Roxo & Lilás",
        "bg":        (18,  14,  22),
        "bg2":       (52,  30,  60),
        "surface":   (245, 241, 250),
        "surface2":  (228, 220, 238),
        "accent":    (155, 107, 155),
        "accent2":   (110,  72, 110),
        "highlight": (210, 170, 230),
        "text_dark": (32,  24,  42),
        "text_dim":  (128, 118, 138),
        "text_light":(242, 238, 248),
        "sidebar_top":(200,184,216),
        "sidebar_bot":(155,107,155),
        "layout": "left_bold",
        "deco": "circles",
    },

    "verde": {
        "name": "Verde Musgo & Dourado",
        "bg":        (14,  20,  16),
        "bg2":       (28,  48,  30),
        "surface":   (242, 248, 242),
        "surface2":  (210, 232, 212),
        "accent":    (88,  148, 92),
        "accent2":   (58,  110, 62),
        "highlight": (198, 168, 80),
        "text_dark": (20,  38,  22),
        "text_dim":  (100, 128, 102),
        "text_light":(236, 248, 236),
        "sidebar_top":(198,220,140),
        "sidebar_bot":(88,148,92),
        "layout": "center_serif",
        "deco": "lines",
    },

    "terracota": {
        "name": "Terracota & Creme",
        "bg":        (28,  18,  12),
        "bg2":       (72,  38,  22),
        "surface":   (252, 246, 238),
        "surface2":  (238, 224, 208),
        "accent":    (196, 100,  72),
        "accent2":   (160,  72,  48),
        "highlight": (220, 180, 120),
        "text_dark": (48,  28,  16),
        "text_dim":  (140, 110,  88),
        "text_light":(252, 240, 228),
        "sidebar_top":(240,200,160),
        "sidebar_bot":(196,100,72),
        "layout": "split_diagonal",
        "deco": "organic",
    },

    "azul": {
        "name": "Azul Noite & Pêssego",
        "bg":        (10,  16,  32),
        "bg2":       (22,  40,  80),
        "surface":   (240, 246, 255),
        "surface2":  (210, 228, 252),
        "accent":    (72,  120, 200),
        "accent2":   (48,  88,  160),
        "highlight": (240, 180, 140),
        "text_dark": (16,  28,  56),
        "text_dim":  (100, 120, 160),
        "text_light":(230, 240, 255),
        "sidebar_top":(180,210,250),
        "sidebar_bot":(72,120,200),
        "layout": "left_bold",
        "deco": "dots",
    },

    "grafite": {
        "name": "Grafite & Laranja",
        "bg":        (20,  20,  20),
        "bg2":       (45,  35,  20),
        "surface":   (248, 248, 244),
        "surface2":  (232, 228, 220),
        "accent":    (220, 130,  50),
        "accent2":   (180,  96,  28),
        "highlight": (255, 190, 100),
        "text_dark": (28,  26,  22),
        "text_dim":  (120, 114, 100),
        "text_light":(252, 248, 238),
        "sidebar_top":(255,200,120),
        "sidebar_bot":(220,130,50),
        "layout": "center_serif",
        "deco": "geometric",
    },

    "bordo": {
        "name": "Bordô & Rosa",
        "bg":        (28,  10,  18),
        "bg2":       (72,  20,  42),
        "surface":   (255, 242, 248),
        "surface2":  (248, 220, 236),
        "accent":    (180,  60, 100),
        "accent2":   (140,  38,  72),
        "highlight": (248, 168, 196),
        "text_dark": (52,  14,  30),
        "text_dim":  (148,  96, 118),
        "text_light":(255, 238, 248),
        "sidebar_top":(248,180,212),
        "sidebar_bot":(180,60,100),
        "layout": "split_diagonal",
        "deco": "circles",
    },
}

THEME_KEYS = list(THEMES.keys())

# ── helpers comuns ────────────────────────────────────────────────────────────

def grain(img, s=10):
    arr = np.array(img).astype(np.float32)
    np.random.seed(random.randint(0,999))
    return Image.fromarray(np.clip(arr + np.random.normal(0,s,arr.shape),0,255).astype(np.uint8))

def sidebar_grad(d, top, bot):
    for py in range(H):
        t = py/H
        d.line([(0,py),(9,py)], fill=(
            int(top[0]+(bot[0]-top[0])*t),
            int(top[1]+(bot[1]-top[1])*t),
            int(top[2]+(bot[2]-top[2])*t)))
    d.rectangle([15,0,17,H], fill=(bot[0]//2,bot[1]//2,bot[2]//2))

def bg_gradient(d, start, col_from, col_to, strength=0.7):
    for py in range(start,H):
        t = (py-start)/(H-start)
        d.line([(0,py),(W,py)], fill=(
            int(col_from[0]+(col_to[0]-col_from[0])*t*strength),
            int(col_from[1]+(col_to[1]-col_from[1])*t*strength),
            int(col_from[2]+(col_to[2]-col_from[2])*t*strength)))

def wrap(d, text, font, max_w):
    words=text.split(); lines,cur=[],""
    for w in words:
        test=(cur+" "+w).strip()
        if d.textlength(test,font=font)<=max_w: cur=test
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def wrp(d, text, font, x, y, max_w, fill, gap=1.45):
    ls=wrap(d,text,font,max_w); a,de=font.getmetrics(); lh=int((a+de)*gap)
    for ln in ls: d.text((x,y),ln,font=font,fill=fill); y+=lh
    return y

def dots_row(d, active, total, accent):
    r=5; gap=24; tw=(total-1)*gap; cx0=W//2-tw//2
    for i in range(total):
        cx=cx0+i*gap
        if i==active: d.ellipse([cx-r,H-52-r,cx+r,H-52+r],fill=accent)
        else: d.ellipse([cx-r+2,H-52-r+2,cx+r-2,H-52+r-2],fill=(*accent[:3],80) if len(accent)==4 else (accent[0]//2,accent[1]//2,accent[2]//2))

def footer_dark(d, t, insta, nome):
    d.line([(54,H-84),(W-54,H-84)],fill=(t["bg2"][0]+20,t["bg2"][1]+20,t["bg2"][2]+20),width=1)
    ff=pp(22,"Light")
    d.text((54,H-60),insta,font=ff,fill=t["text_dim"])
    d.ellipse([W//2-3,H-47,W//2+3,H-41],fill=t["accent"])
    d.text((W-54-int(d.textlength(nome,font=ff)),H-60),nome,font=ff,fill=t["text_dim"])

def footer_light(d, t, insta, nome):
    d.line([(54,H-78),(W-54,H-78)],fill=t["surface2"],width=1)
    ff=pp(22,"Light")
    d.text((54,H-54),insta,font=ff,fill=t["text_dim"])
    d.ellipse([W//2-3,H-41,W//2+3,H-35],fill=t["accent"])
    d.text((W-54-int(d.textlength(nome,font=ff)),H-54),nome,font=ff,fill=t["text_dim"])

def header_dark(d, t, no_text):
    brand = "G E S T A R   B E M"
    d.line([(54,82),(W-54,82)],fill=(t["bg2"][0]+15,t["bg2"][1]+15,t["bg2"][2]+15),width=1)
    d.text((54,44),brand,font=pp(22,"Light"),fill=t["text_dim"])
    if no_text: d.text((54,106),no_text,font=pp(20,"Light"),fill=(*t["accent"][:3],180))

def header_light(d, t, tag, no_text):
    brand = "G E S T A R   B E M"
    d.line([(54,82),(W-54,82)],fill=t["surface2"],width=1)
    d.text((54,44),brand,font=pp(22,"Light"),fill=t["text_dim"])
    ft=pp(24,"Bold"); d.text((54,106),tag.upper(),font=ft,fill=t["accent2"])
    tw=int(d.textlength(tag.upper(),font=ft))
    d.line([(54,134),(54+tw,134)],fill=t["surface2"],width=2)
    d.text((W-54-int(d.textlength(no_text,font=pp(20,"Light"))),106),no_text,font=pp(20,"Light"),fill=t["accent"])

# ── elementos decorativos ─────────────────────────────────────────────────────

def deco_circles(img, idx, total, t):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ac=t["accent"]; ac2=t["bg2"]
    positions=[
        (idx*W,   80,  220, ac2, .28),
        ((idx+1)*W,H-80,200, ac2, .22),
        (W+60,    -60, 180, ac2, .20),
        (-60,     H+60,180, ac2, .18),
    ]
    for cx_g,cy,r,col,op in positions:
        cx_l=cx_g-idx*W
        ld.ellipse([cx_l-r,cy-r,cx_l+r,cy+r],fill=(*col,int(255*op)))
    ld.ellipse([W-120,-60,W+60,120],fill=(*ac,30))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def deco_lines(img, idx, t):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ac=t["accent"]; op=35
    for i in range(8):
        x=W-200+i*60; y_top=-100; y_bot=H+100
        ld.line([(x,y_top),(x-300,y_bot)],fill=(*ac,op),width=2)
    ld.rectangle([W-12,0,W,H],fill=(*ac,40))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def deco_organic(img, idx, t):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ac2=t["bg2"]; hl=t["highlight"]
    ld.ellipse([W-280,-120,W+120,280],fill=(*ac2,160))
    ld.ellipse([W-180,180,W+60,420],fill=(*ac2,100))
    ld.ellipse([-80,H-200,200,H+80],fill=(*ac2,120))
    ld.ellipse([W-100,H-100,W+100,H+100],fill=(*hl,25))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def deco_dots(img, idx, t):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ac=t["accent"]
    for row in range(0,H,60):
        for col in range(600,W+60,60):
            ld.ellipse([col-3,row-3,col+3,row+3],fill=(*ac,30))
    ld.ellipse([W-160,-80,W+80,160],fill=(*t["bg2"],180))
    ld.ellipse([-80,H-160,160,H+80],fill=(*t["bg2"],140))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def deco_geometric(img, idx, t):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ac=t["accent"]; ac2=t["bg2"]
    ld.rectangle([W-200,0,W,H],fill=(*ac2,120))
    ld.rectangle([W-210,0,W-200,H],fill=(*ac,80))
    ld.polygon([(W-200,0),(W,0),(W,400)],fill=(*ac,40))
    ld.rectangle([0,H-8,W,H],fill=(*ac,60))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def apply_deco(img, idx, total, t):
    deco = t["deco"]
    if deco=="circles":  return deco_circles(img, idx, total, t)
    if deco=="lines":    return deco_lines(img, idx, t)
    if deco=="organic":  return deco_organic(img, idx, t)
    if deco=="dots":     return deco_dots(img, idx, t)
    if deco=="geometric":return deco_geometric(img, idx, t)
    return deco_circles(img, idx, total, t)

# ── layouts de capa ───────────────────────────────────────────────────────────

def cover_left_bold(d, t, texto, label, insta, nome, idx, total):
    """Texto âncora à esquerda, tipografia corajosa"""
    x=54; y=175
    words=texto.split(); half=max(1,len(words)//2)
    l1=" ".join(words[:half]); l2=" ".join(words[half:])
    d.text((x,y),l1,font=lora(108,True),fill=t["text_light"])
    a,de=lora(108,True).getmetrics(); y+=a+de+6
    d.line([(x,y),(x+360,y)],fill=t["accent"],width=3); y+=20
    d.text((x,y),l2,font=lora(72),fill=(*t["accent"][:3],220))
    a,de=lora(72).getmetrics(); y+=a+de+44
    y=wrp(d,label,pp(33,"Light"),x,y,W-140,t["text_dim"],1.45); y+=38
    # hint
    fh=pp(22,"Light"); col=t["text_dim"]
    d.text((x,y),"arraste para ver",font=fh,fill=col)
    aw=int(d.textlength("arraste para ver",font=fh)); ax,ay=x+aw+12,y+13
    for pts in [[(ax,ay),(ax+30,ay)],[(ax+30,ay),(ax+20,ay-7)],[(ax+30,ay),(ax+20,ay+7)]]:
        d.line(pts,fill=col,width=2)
    a,de=fh.getmetrics(); y+=a+de+52
    # citação
    d.line([(x,y),(W-54,y)],fill=(t["bg2"][0]+20,t["bg2"][1]+20,t["bg2"][2]+20),width=1); y+=18
    d.text((x,y),"\u201c",font=lora(52,True),fill=t["highlight"])
    a,de=lora(52,True).getmetrics(); y+=a+de+4
    d.text((x,y),"Seu corpo está trabalhando",font=lora(40),fill=t["text_light"])
    a,de=lora(40).getmetrics(); y+=a+de+2
    d.text((x,y),"por você e pelo bebê.",font=lora(40),fill=t["text_light"])
    a,de=lora(40).getmetrics(); y+=a+de+12
    d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(20,"Light"),fill=t["text_dim"])
    dots_row(d,idx,total,t["accent"])
    footer_dark(d,t,insta,nome)

def cover_center_serif(d, t, texto, label, insta, nome, idx, total):
    """Título centralizado, estilo editorial de revista"""
    cx=W//2
    # linha decorativa topo
    d.line([(100,170),(W-100,170)],fill=t["accent"],width=1); 
    d.line([(100,178),(W-100,178)],fill=t["accent"],width=3)
    y=200
    # título linha a linha centralizado
    words=texto.split()
    lines_t=[]
    cur=""
    for w in words:
        test=(cur+" "+w).strip()
        img_tmp=Image.new("RGB",(1,1)); dt=ImageDraw.Draw(img_tmp)
        if dt.textlength(test,font=lora(88,True))<=W-160: cur=test
        else:
            if cur: lines_t.append(cur)
            cur=w
    if cur: lines_t.append(cur)
    for i,ln in enumerate(lines_t):
        f=lora(88,True); tw=int(ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(ln,font=f))
        col=t["highlight"] if i==len(lines_t)-1 else t["text_light"]
        d.text((cx-tw//2,y),ln,font=f,fill=col); a,de=f.getmetrics(); y+=a+de+8
    y+=20
    # separador com diamante
    d.line([(cx-120,y),(cx-16,y)],fill=t["accent"],width=1)
    d.polygon([(cx,y-8),(cx+10,y),(cx,y+8),(cx-10,y)],fill=t["accent"])
    d.line([(cx+16,y),(cx+120,y)],fill=t["accent"],width=1)
    y+=36
    # subtítulo
    ft=pp(32,"Light"); tw=int(ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(label,font=ft))
    if tw <= W-120:
        d.text((cx-tw//2,y),label,font=ft,fill=t["text_dim"])
        a,de=ft.getmetrics(); y+=a+de+48
    else:
        y=wrp(d,label,ft,80,y,W-160,t["text_dim"],1.4); y+=40
    # hint centralizado
    fh=pp(22,"Light")
    hint="arraste para ver ›"
    tw=int(ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(hint,font=fh))
    d.text((cx-tw//2,y),hint,font=fh,fill=t["text_dim"])
    a,de=fh.getmetrics(); y+=a+de+52
    # linha + citação centralizada
    d.line([(80,y),(W-80,y)],fill=(t["bg2"][0]+20,t["bg2"][1]+20,t["bg2"][2]+20),width=1); y+=20
    quote="\" Seu corpo trabalhando por você e pelo bebê. \""
    fq=lora(38); tw=int(ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(quote,font=fq))
    if tw<=W-120: d.text((cx-tw//2,y),quote,font=fq,fill=t["text_dim"])
    else: wrp(d,quote,fq,80,y,W-160,t["text_dim"],1.4)
    a,de=fq.getmetrics(); y+=a+de+10
    attr="— Jéssica D'Agostini · Nutricionista"
    tw=int(ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(attr,font=pp(20,"Light")))
    d.text((cx-tw//2,y),attr,font=pp(20,"Light"),fill=t["text_dim"])
    dots_row(d,idx,total,t["accent"])
    footer_dark(d,t,insta,nome)

def cover_split_diagonal(d, t, texto, label, insta, nome, idx, total):
    """Faixa diagonal de cor dividindo o slide"""
    # bloco de cor na metade superior
    pts=[(0,0),(W,0),(W,480),(0,620)]
    d.polygon(pts,fill=t["accent2"])
    # texto sobre o bloco colorido
    x=54; y=160
    words=texto.split(); half=max(1,len(words)//2)
    l1=" ".join(words[:half])
    d.text((x,y),l1,font=lora(98,True),fill=t["text_light"])
    a,de=lora(98,True).getmetrics(); y+=a+de+4
    d.text((x,y)," ".join(words[half:]),font=lora(98,True),fill=t["highlight"])
    a,de=lora(98,True).getmetrics(); y+=a+de+36
    # linha de separação na diagonal
    y=640
    d.line([(x,y),(x+320,y)],fill=t["text_light"],width=2); y+=26
    # texto abaixo em cor escura
    y=wrp(d,label,pp(34,"Light"),x,y,W-130,t["text_dim"],1.45); y+=36
    fh=pp(23,"Light"); col=t["text_dim"]
    d.text((x,y),"arraste para ver",font=fh,fill=col)
    aw=int(d.textlength("arraste para ver",font=fh)); ax,ay=x+aw+12,y+13
    for pts2 in [[(ax,ay),(ax+30,ay)],[(ax+30,ay),(ax+20,ay-7)],[(ax+30,ay),(ax+20,ay+7)]]:
        d.line(pts2,fill=col,width=2)
    a,de=fh.getmetrics(); y+=a+de+52
    d.line([(x,y),(W-54,y)],fill=(t["bg2"][0]+20,t["bg2"][1]+20,t["bg2"][2]+20),width=1); y+=18
    d.text((x,y),"\u201c",font=lora(50,True),fill=t["accent"])
    a,de=lora(50,True).getmetrics(); y+=a+de+4
    d.text((x,y),"Seu corpo está trabalhando por você.",font=lora(38),fill=t["text_light"])
    a,de=lora(38).getmetrics(); y+=a+de+10
    d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(20,"Light"),fill=t["text_dim"])
    dots_row(d,idx,total,t["accent"])
    footer_dark(d,t,insta,nome)

# ── slides internos ───────────────────────────────────────────────────────────

def slide_light(idx, slide, cfg, t, total):
    img=Image.new("RGB",(W,H),t["surface"]); d=ImageDraw.Draw(img)
    # detalhe de canto
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ld.ellipse([W-160,-80,W+80,160],fill=(*t["accent"][:3],30))
    img=Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB"); d=ImageDraw.Draw(img)
    sidebar_grad(d,t["sidebar_top"],t["sidebar_bot"])
    label=slide.get("label","Conteúdo"); texto=slide.get("texto","")
    no=f"No. {str(idx+1).zfill(2)}"
    header_light(d,t,label,no)
    x=54; y=185
    words=label.split()
    if len(words)>=2:
        d.text((x,y),words[0],font=lora(68,True),fill=t["text_dark"])
        a,de=lora(68,True).getmetrics(); y+=a+de+2
        d.text((x,y)," ".join(words[1:]),font=lora(68,True),fill=t["accent"])
        a,de=lora(68,True).getmetrics(); y+=a+de+24
    else:
        d.text((x,y),label,font=lora(68,True),fill=t["accent"])
        a,de=lora(68,True).getmetrics(); y+=a+de+24
    d.line([(x,y),(x+220,y)],fill=t["surface2"],width=2); y+=26
    wrp(d,texto,pp(34,"Regular"),x,y,W-120,t["text_dark"],1.48)
    dots_row(d,idx,total,t["accent"])
    insta=cfg.get("insta","@gestarbem_"); nome="por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip()
    footer_light(d,t,insta,nome)
    return grain(img,8)

def slide_emotional(idx, slide, cfg, t, total):
    img=Image.new("RGB",(W,H),t["bg"]); d=ImageDraw.Draw(img)
    bg_gradient(d,500,t["bg"],t["bg2"],0.65)
    sidebar_grad(d,t["sidebar_top"],t["sidebar_bot"])
    img=apply_deco(img,idx,total,t); d=ImageDraw.Draw(img)
    header_dark(d,t,f"No. {str(idx+1).zfill(2)}")
    insta=cfg.get("insta","@gestarbem_"); nome="por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip()
    x=54; y=200
    label=slide.get("label",""); texto=slide.get("texto","")
    d.text((x,y),"\u201c",font=lora(90,True),fill=t["accent"])
    a,de=lora(90,True).getmetrics(); y+=a+de-10
    parts=label.split("|") if "|" in label else [label]
    for i,ln in enumerate(parts[:3]):
        col=t["highlight"] if i==len(parts[:3])-1 else t["text_light"]
        d.text((x,y),ln.strip(),font=lora(82,True),fill=col)
        a,de=lora(82,True).getmetrics(); y+=a+de+4
    y+=14; d.line([(x,y),(x+260,y)],fill=(t["bg2"][0]+30,t["bg2"][1]+30,t["bg2"][2]+30),width=1); y+=28
    y=wrp(d,texto,pp(32,"Light"),x,y,W-120,t["text_dim"],1.48); y+=26
    d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(22,"Light"),fill=t["text_dim"])
    dots_row(d,idx,total,t["accent"])
    footer_dark(d,t,insta,nome)
    return grain(img,11)

def slide_cta(idx, slide, cfg, t, total):
    img=Image.new("RGB",(W,H),t["bg"]); d=ImageDraw.Draw(img)
    bg_gradient(d,380,t["bg"],t["bg2"],0.8)
    sidebar_grad(d,t["sidebar_top"],t["sidebar_bot"])
    img=apply_deco(img,idx,total,t); d=ImageDraw.Draw(img)
    d.line([(54,82),(W-54,82)],fill=(t["bg2"][0]+15,t["bg2"][1]+15,t["bg2"][2]+15),width=1)
    d.text((54,44),"G E S T A R   B E M",font=pp(22,"Light"),fill=t["text_dim"])
    insta=cfg.get("insta","@gestarbem_"); nome="por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip()
    x=54; y=165
    texto=slide.get("texto","Cada gestação é única.")
    parts=texto.split("."); titulo=parts[0].strip()+"."
    resto=".".join(parts[1:]).strip() if len(parts)>1 else ""
    d.text((x,y),titulo,font=lora(80,True),fill=t["text_light"])
    a,de=lora(80,True).getmetrics(); y+=a+de+12
    d.line([(x,y),(x+260,y)],fill=t["accent"],width=2); y+=28
    if resto: y=wrp(d,resto,pp(32,"Light"),x,y,W-120,t["text_dim"],1.46); y+=28
    for txt in ["Salva este post para os dias difíceis.","Comenta aqui: você já sabia disso? 👇"]:
        d.ellipse([x,y+7,x+12,y+19],fill=t["accent"])
        ls=wrap(d,txt,pp(30,"Medium"),W-150); a,de=pp(30,"Medium").getmetrics(); lh=int((a+de)*1.38)
        for i,ln in enumerate(ls): d.text((x+28,y+i*lh),ln,font=pp(30,"Medium"),fill=t["text_light"])
        y+=lh*len(ls)+22
    y+=20
    d.rounded_rectangle([x,y,W-54,y+88],radius=20,fill=(t["bg2"][0]+10,t["bg2"][1]+10,t["bg2"][2]+10))
    d.rounded_rectangle([x,y,W-54,y+88],radius=20,outline=t["accent"],width=2)
    label=f"{cfg.get('nome','Gestar Bem')} · {insta}"
    lw=int(d.textlength(label,font=pp(26,"Bold")))
    d.text((W//2-lw//2,y+26),label,font=pp(26,"Bold"),fill=t["sidebar_top"])
    dots_row(d,idx,total,t["accent"])
    footer_dark(d,t,insta,nome)
    return grain(img,11)

def slide_cover(idx, slide, cfg, t, total):
    img=Image.new("RGB",(W,H),t["bg"]); d=ImageDraw.Draw(img)
    bg_gradient(d,640,t["bg"],t["bg2"],0.7)
    sidebar_grad(d,t["sidebar_top"],t["sidebar_bot"])
    img=apply_deco(img,idx,total,t); d=ImageDraw.Draw(img)
    header_dark(d,t,"No. 01")
    insta=cfg.get("insta","@gestarbem_"); nome="por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip()
    texto=slide.get("texto",""); label=slide.get("label","")
    layout=t["layout"]
    if layout=="left_bold":       cover_left_bold(d,t,texto,label,insta,nome,idx,total)
    elif layout=="center_serif":  cover_center_serif(d,t,texto,label,insta,nome,idx,total)
    elif layout=="split_diagonal":cover_split_diagonal(d,t,texto,label,insta,nome,idx,total)
    else:                         cover_left_bold(d,t,texto,label,insta,nome,idx,total)
    return grain(img,11)

# ── rota principal ────────────────────────────────────────────────────────────

@app.after_request
def cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/", methods=["GET"])
def health():
    fonts_ok=all(os.path.exists(os.path.join(FONT_DIR,f)) for f in FONT_URLS)
    return jsonify({"status":"ok","service":"Gestar Bem Multi-Theme","fonts":fonts_ok,
                    "temas":list(THEMES.keys())})

@app.route("/temas", methods=["GET"])
def temas():
    return jsonify({k:{"nome":v["name"],"layout":v["layout"],"deco":v["deco"]}
                    for k,v in THEMES.items()})

@app.route("/gerar", methods=["POST","OPTIONS"])
def gerar():
    if request.method=="OPTIONS": return jsonify({}),200
    try:
        data   = request.get_json(force=True)
        slides = data.get("slides",[])
        cfg    = data.get("cfg",{})
        tema_key = data.get("tema","")  # vazio = aleatório

        if not slides: return jsonify({"erro":"Nenhum slide enviado"}),400

        # seleciona tema
        if tema_key and tema_key in THEMES:
            t = THEMES[tema_key]
        else:
            t = THEMES[random.choice(THEME_KEYS)]

        n=len(slides); images=[]
        for i,slide in enumerate(slides):
            if   i==0:   img=slide_cover(i,slide,cfg,t,n)
            elif i==n-1: img=slide_cta(i,slide,cfg,t,n)
            elif i==n-2: img=slide_emotional(i,slide,cfg,t,n)
            else:        img=slide_light(i,slide,cfg,t,n)
            images.append((f"slide-{str(i+1).zfill(2)}.png",img))

        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as zf:
            for name,img in images:
                ib=io.BytesIO(); img.save(ib,"PNG"); zf.writestr(name,ib.getvalue())
        buf.seek(0)
        return send_file(buf,mimetype="application/zip",as_attachment=True,
                         download_name=f"gestar-bem-{t['name'].split()[0].lower()}.zip")
    except Exception as e:
        import traceback
        return jsonify({"erro":str(e),"traceback":traceback.format_exc()}),500

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
