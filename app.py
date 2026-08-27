"""
Gestar Bem — Backend de geração de imagens
Roda na Render (gratuito) e serve os slides prontos para download
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os, io, zipfile, json, tempfile

app = Flask(__name__)
CORS(app)  # permite chamadas do site na Netlify

# ── fontes ────────────────────────────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

def lora(size, bold=False):
    path = os.path.join(FONT_DIR, "Lora-Bold.ttf" if bold else "Lora-Regular.ttf")
    return ImageFont.truetype(path, size)

def pp(size, weight="Regular"):
    names = {"Bold":"Bold","Medium":"Medium","Light":"Light","Regular":"Regular",
             "SemiBold":"Bold","ExtraLight":"Light"}
    w = names.get(weight, "Regular")
    path = os.path.join(FONT_DIR, f"Poppins-{w}.ttf")
    return ImageFont.truetype(path, size)

# ── paleta ────────────────────────────────────────────────────────────────────
BG      = (18, 14, 22)
PURPLE  = (155,107,155)
PURPLE2 = (52, 30, 60)
LILAC   = (200,184,216)
LILAC_DIM=(138,122,152)
LILAC_BG=(245,241,250)
LILAC_MID=(228,220,238)
CREAM   = (242,238,248)
DIM     = (128,118,138)
DARK_TXT= (32, 24, 42)
DIM_TXT = (96, 84,108)
PURPLE3 = (110,72,110)
ACCENT  = (210,170,230)

W, H = 1080, 1350

def grain(img, s=10):
    arr = np.array(img).astype(np.float32)
    np.random.seed(13)
    return Image.fromarray(np.clip(arr + np.random.normal(0, s, arr.shape), 0, 255).astype(np.uint8))

def sidebar(d, top, bot):
    for py in range(H):
        t = py / H
        d.line([(0,py),(9,py)], fill=(
            int(top[0]+(bot[0]-top[0])*t),
            int(top[1]+(bot[1]-top[1])*t),
            int(top[2]+(bot[2]-top[2])*t)))
    d.rectangle([15,0,17,H], fill=(bot[0]//3,bot[1]//3,bot[2]//3))

def bg_grad(d, start, col, s=0.7):
    for py in range(start, H):
        t = (py-start)/(H-start)
        d.line([(0,py),(W,py)], fill=(
            int(BG[0]+(col[0]-BG[0])*t*s),
            int(BG[1]+(col[1]-BG[1])*t*s),
            int(BG[2]+(col[2]-BG[2])*t*s)))

def draw_circles(img, cfg):
    layer = Image.new("RGBA",(W,H),(0,0,0,0))
    ld = ImageDraw.Draw(layer)
    for cx,cy,r,col,op in cfg:
        ld.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(col[0],col[1],col[2],int(255*op)))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

def wrap(d, text, font, max_w):
    words = text.split(); lines, cur = [], ""
    for w in words:
        test = (cur+" "+w).strip()
        if d.textlength(test, font=font) <= max_w: cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def wrp(d, text, font, x, y, max_w, fill, gap=1.45):
    lines = wrap(d, text, font, max_w)
    a, de = font.getmetrics(); lh = int((a+de)*gap)
    for ln in lines: d.text((x,y), ln, font=font, fill=fill); y += lh
    return y

def dots(d, active, dark=False):
    r=5; gap=24; tw=6*gap; cx0=W//2-tw//2
    for i in range(7):
        cx = cx0+i*gap
        if i==active: d.ellipse([cx-r,H-52-r,cx+r,H-52+r], fill=PURPLE)
        else: d.ellipse([cx-r+2,H-52-r+2,cx+r-2,H-52+r-2], fill=LILAC if dark else LILAC_DIM)

def dark_hdr(d, no):
    d.line([(54,82),(W-54,82)], fill=(42,32,52), width=1)
    d.text((54,44), "G E S T A R   B E M", font=pp(22,"Light"), fill=DIM)
    if no: d.text((54,106), no, font=pp(20,"Light"), fill=LILAC_DIM)

def light_hdr(d, tag, no):
    d.line([(54,82),(W-54,82)], fill=LILAC_MID, width=1)
    d.text((54,44), "G E S T A R   B E M", font=pp(22,"Light"), fill=DIM_TXT)
    ft = pp(24,"Bold"); d.text((54,106), tag.upper(), font=ft, fill=PURPLE3)
    tw = int(d.textlength(tag.upper(), font=ft))
    d.line([(54,134),(54+tw,134)], fill=LILAC_MID, width=2)
    d.text((W-54-int(d.textlength(no, font=pp(20,"Light"))),106), no, font=pp(20,"Light"), fill=LILAC_DIM)

def dark_ftr(d, insta="@gestarbem_", nome="por Jéssica D'Agostini"):
    d.line([(54,H-84),(W-54,H-84)], fill=(36,26,46), width=1)
    ff = pp(22,"Light"); d.text((54,H-60), insta, font=ff, fill=DIM)
    d.ellipse([W//2-3,H-47,W//2+3,H-41], fill=LILAC)
    d.text((W-54-int(d.textlength(nome,font=ff)),H-60), nome, font=ff, fill=DIM)

def light_ftr(d, insta="@gestarbem_", nome="por Jéssica D'Agostini"):
    d.line([(54,H-78),(W-54,H-78)], fill=LILAC_MID, width=1)
    ff = pp(22,"Light"); d.text((54,H-54), insta, font=ff, fill=DIM_TXT)
    d.ellipse([W//2-3,H-41,W//2+3,H-35], fill=PURPLE)
    d.text((W-54-int(d.textlength(nome,font=ff)),H-54), nome, font=ff, fill=DIM_TXT)

# círculos panorâmicos conectados
PANO_DARK = [
    (1*W,80,220,PURPLE2,0.28),(2*W,H-80,200,PURPLE2,0.22),
    (3*W,60,240,PURPLE2,0.25),(4*W,H-60,210,PURPLE2,0.22),
    (5*W,80,230,PURPLE2,0.26),(6*W,H-80,220,PURPLE2,0.24),
    (0,0,180,PURPLE2,0.18),(7*W,0,180,PURPLE2,0.18),
    (0,H,180,PURPLE2,0.18),(7*W,H,180,PURPLE2,0.18),
]
PANO_LIGHT = [
    (1*W,80,220,(180,160,200),0.18),(2*W,H-80,200,(180,160,200),0.16),
    (3*W,60,240,(180,160,200),0.18),(4*W,H-60,210,(180,160,200),0.16),
    (5*W,80,230,(180,160,200),0.17),
]

def get_circles(idx, light=False):
    src = PANO_LIGHT if light else PANO_DARK
    res = []
    for cx_g,cy,r,col,op in src:
        cx_l = cx_g - idx*W
        if cx_l+r > 0 and cx_l-r < W:
            res.append((cx_l,cy,r,col,op))
    return res

# ── geradores de slide ────────────────────────────────────────────────────────

def make_dark_slide(idx, slide_data, cfg, grad_start=740):
    img = Image.new("RGB",(W,H),BG); d = ImageDraw.Draw(img)
    bg_grad(d, grad_start, PURPLE2, 0.7)
    sidebar(d, LILAC, PURPLE)
    img = draw_circles(img, get_circles(idx)); d = ImageDraw.Draw(img)
    dark_hdr(d, f"No. {str(idx+1).zfill(2)}")

    x=54; y=172
    label = slide_data.get("label","")
    texto = slide_data.get("texto","")

    if idx == 0:  # CAPA
        # título grande
        words = texto.split()
        half = len(words)//2
        line1 = " ".join(words[:half])
        line2 = " ".join(words[half:])
        d.text((x,y), line1, font=lora(102,True), fill=CREAM)
        a,de=lora(102,True).getmetrics(); y+=a+de+6
        d.line([(x,y),(x+380,y)], fill=PURPLE, width=2); y+=18
        d.text((x,y), line2, font=lora(72,True), fill=LILAC_DIM)
        a,de=lora(72,True).getmetrics(); y+=a+de+36
        d.line([(x,y),(x+180,y)], fill=(40,28,50), width=1); y+=20
        y = wrp(d, label, pp(32,"Light"), x, y, W-120, DIM, 1.45)
        y += 32
        fh = pp(22,"Light"); col=(100,88,112)
        d.text((x,y),"arraste para ver",font=fh,fill=col)
        aw=int(d.textlength("arraste para ver",font=fh)); ax,ay=x+aw+12,y+12
        for pts in [[(ax,ay),(ax+32,ay)],[(ax+32,ay),(ax+21,ay-7)],[(ax+32,ay),(ax+21,ay+7)]]:
            d.line(pts,fill=col,width=2)
        a,de=fh.getmetrics(); y+=a+de+48
        d.line([(x,y),(x+W-108,y)],fill=(48,34,58),width=1); y+=16
        d.text((x,y),"\u201c",font=lora(52,True),fill=ACCENT)
        a,de=lora(52,True).getmetrics(); y+=a+de+4
        d.text((x,y),"Seu corpo está trabalhando",font=lora(40),fill=CREAM)
        a,de=lora(40).getmetrics(); y+=a+de+2
        d.text((x,y),"por você e pelo bebê.",font=lora(40),fill=CREAM)
        a,de=lora(40).getmetrics(); y+=a+de+10
        d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(20,"Light"),fill=LILAC_DIM)
    else:  # CTA e emocional
        d.text((x,y),"\u201c",font=lora(90,True),fill=PURPLE)
        a,de=lora(90,True).getmetrics(); y+=a+de-10
        lines_h = label.split("|") if "|" in label else [label]
        for i,ln in enumerate(lines_h):
            col = PURPLE if i==len(lines_h)-1 else CREAM
            d.text((x,y),ln.strip(),font=lora(86,True),fill=col)
            a,de=lora(86,True).getmetrics(); y+=a+de+4
        y+=12; d.line([(x,y),(x+280,y)],fill=(60,42,70),width=1); y+=26
        y = wrp(d,texto,pp(32,"Light"),x,y,W-120,DIM,1.48)
        y+=24
        d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(22,"Light"),fill=LILAC_DIM)

    dots(d,idx,dark=True)
    dark_ftr(d, cfg.get("insta","@gestarbem_"), "por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip())
    return grain(img,11)

def make_light_slide(idx, slide_data, cfg):
    img = Image.new("RGB",(W,H),LILAC_BG); d = ImageDraw.Draw(img)
    img = draw_circles(img, get_circles(idx, light=True)); d = ImageDraw.Draw(img)
    sidebar(d, LILAC, PURPLE)
    label = slide_data.get("label","Conteúdo")
    texto = slide_data.get("texto","")
    no = f"No. {str(idx+1).zfill(2)}"
    light_hdr(d, label, no)
    x=54; y=185
    # headline em duas cores
    words = label.split()
    if len(words) >= 2:
        d.text((x,y),words[0],font=lora(68,True),fill=DARK_TXT)
        a,de=lora(68,True).getmetrics(); y+=a+de+2
        d.text((x,y)," ".join(words[1:]),font=lora(68,True),fill=PURPLE)
        a,de=lora(68,True).getmetrics(); y+=a+de+24
    else:
        d.text((x,y),label,font=lora(68,True),fill=PURPLE)
        a,de=lora(68,True).getmetrics(); y+=a+de+24
    d.line([(x,y),(x+240,y)],fill=LILAC_MID,width=2); y+=26
    y = wrp(d,texto,pp(34,"Regular"),x,y,W-120,DARK_TXT,1.48)
    dots(d,idx)
    light_ftr(d, cfg.get("insta","@gestarbem_"), "por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip())
    return grain(img,8)

def make_cta_slide(idx, slide_data, cfg):
    img = Image.new("RGB",(W,H),BG); d = ImageDraw.Draw(img)
    bg_grad(d,440,PURPLE2,0.78); sidebar(d,LILAC,PURPLE)
    img = draw_circles(img,get_circles(idx)); d = ImageDraw.Draw(img)
    d.line([(54,82),(W-54,82)],fill=(42,32,52),width=1)
    d.text((54,44),"G E S T A R   B E M",font=pp(22,"Light"),fill=DIM)
    x=54; y=160
    texto = slide_data.get("texto","")
    parts = texto.split(".")
    titulo = parts[0].strip() if parts else "Cada gestação é única."
    resto  = ".".join(parts[1:]).strip() if len(parts)>1 else ""
    d.text((x,y),titulo,font=lora(80,True),fill=CREAM)
    a,de=lora(80,True).getmetrics(); y+=a+de+12
    d.line([(x,y),(x+280,y)],fill=PURPLE,width=2); y+=26
    if resto:
        y = wrp(d,resto,pp(33,"Light"),x,y,W-120,DIM,1.46); y+=32
    # CTAs
    ctas = [
        "Salva este post para os dias difíceis.",
        slide_data.get("cta","Comenta aqui: você já sabia disso? 👇")
    ]
    for txt in ctas:
        d.ellipse([x,y+7,x+12,y+19],fill=LILAC)
        lines = wrap(d,txt,pp(31,"Medium"),W-120-28)
        a,de=pp(31,"Medium").getmetrics(); lh=int((a+de)*1.38)
        for i,ln in enumerate(lines): d.text((x+28,y+i*lh),ln,font=pp(31,"Medium"),fill=CREAM)
        y+=lh*len(lines)+22
    y+=20
    d.rounded_rectangle([x,y,W-54,y+88],radius=20,fill=(40,28,52))
    d.rounded_rectangle([x,y,W-54,y+88],radius=20,outline=PURPLE,width=2)
    nome = cfg.get("nome","Gestar Bem")
    insta = cfg.get("insta","@gestarbem_")
    label = f"{nome} · {insta}"
    lw = int(d.textlength(label,font=pp(26,"Bold")))
    d.text((W//2-lw//2,y+26),label,font=pp(26,"Bold"),fill=LILAC)
    dots(d,idx,dark=True)
    dark_ftr(d, insta, "por "+cfg.get("prof","Jéssica D'Agostini").split("·")[0].strip())
    return grain(img,11)

# ── rotas ─────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"Gestar Bem Image Generator"})

@app.route("/gerar", methods=["POST"])
def gerar():
    """
    Recebe JSON com slides e configurações, devolve ZIP com as imagens.
    Body: { "slides": [...], "cfg": { "nome":..., "insta":..., "prof":... } }
    """
    try:
        data = request.get_json()
        slides = data.get("slides", [])
        cfg   = data.get("cfg", {})

        if not slides:
            return jsonify({"erro": "Nenhum slide enviado"}), 400

        images = []
        for i, slide in enumerate(slides):
            if i == 0:
                img = make_dark_slide(i, slide, cfg, grad_start=740)
            elif i == len(slides)-1:
                img = make_cta_slide(i, slide, cfg)
            elif i == len(slides)-2:
                img = make_dark_slide(i, slide, cfg, grad_start=600)
            else:
                img = make_light_slide(i, slide, cfg)
            images.append((f"slide-{str(i+1).zfill(2)}.png", img))

        # empacota em ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, img in images:
                img_buf = io.BytesIO()
                img.save(img_buf, "PNG")
                zf.writestr(name, img_buf.getvalue())
        buf.seek(0)

        return send_file(buf, mimetype="application/zip",
                         as_attachment=True, download_name="gestar-bem-carrossel.zip")

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
