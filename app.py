from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os, io, zipfile, urllib.request

app = Flask(__name__)
CORS(app)

# ── fontes: baixa automaticamente se não existirem ───────────────────────────
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

FONTS_NEEDED = {
    "Lora-Regular.ttf":  "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "Lora-Bold.ttf":     "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-Regular.ttf":"https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "Poppins-Medium.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
    "Poppins-Bold.ttf":   "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-Light.ttf":  "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Light.ttf",
}

# URLs corretas para Lora
LORA_URL = "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf"

def ensure_fonts():
    for name, url in FONTS_NEEDED.items():
        dest = os.path.join(FONT_DIR, name)
        if not os.path.exists(dest):
            print(f"Baixando fonte {name}...")
            try:
                # Lora tem arquivo variável único
                if "Lora" in name:
                    urllib.request.urlretrieve(LORA_URL, dest)
                else:
                    urllib.request.urlretrieve(url, dest)
                print(f"  OK: {name}")
            except Exception as e:
                print(f"  ERRO ao baixar {name}: {e}")

ensure_fonts()

def get_font(name, size):
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def lora(size, bold=False):
    return get_font("Lora-Bold.ttf" if bold else "Lora-Regular.ttf", size)

def pp(size, weight="Regular"):
    m = {"Bold":"Bold","Medium":"Medium","Light":"Light",
         "Regular":"Regular","SemiBold":"Bold","ExtraLight":"Light"}
    return get_font(f"Poppins-{m.get(weight,'Regular')}.ttf", size)

# ── paleta ────────────────────────────────────────────────────────────────────
BG       = (18,  14,  22)
PURPLE   = (155, 107, 155)
PURPLE2  = (52,  30,  60)
LILAC    = (200, 184, 216)
LILAC_DIM= (138, 122, 152)
LILAC_BG = (245, 241, 250)
LILAC_MID= (228, 220, 238)
CREAM    = (242, 238, 248)
DIM      = (128, 118, 138)
DARK_TXT = (32,  24,  42)
DIM_TXT  = (96,  84,  108)
PURPLE3  = (110, 72,  110)
ACCENT   = (210, 170, 230)
W, H = 1080, 1350

def grain(img, s=10):
    arr = np.array(img).astype(np.float32)
    np.random.seed(13)
    return Image.fromarray(np.clip(arr + np.random.normal(0, s, arr.shape), 0, 255).astype(np.uint8))

def sidebar(d, top, bot):
    for py in range(H):
        t = py/H
        d.line([(0,py),(9,py)], fill=(int(top[0]+(bot[0]-top[0])*t),
               int(top[1]+(bot[1]-top[1])*t),int(top[2]+(bot[2]-top[2])*t)))
    d.rectangle([15,0,17,H], fill=(bot[0]//3,bot[1]//3,bot[2]//3))

def bg_grad(d, start, col, s=0.7):
    for py in range(start,H):
        t=(py-start)/(H-start)
        d.line([(0,py),(W,py)], fill=(int(BG[0]+(col[0]-BG[0])*t*s),
               int(BG[1]+(col[1]-BG[1])*t*s),int(BG[2]+(col[2]-BG[2])*t*s)))

def circles(img, cfg_c):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    for cx,cy,r,col,op in cfg_c:
        ld.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(col[0],col[1],col[2],int(255*op)))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def wrap(d,text,font,max_w):
    words=text.split(); lines,cur=[],""
    for w in words:
        test=(cur+" "+w).strip()
        if d.textlength(test,font=font)<=max_w: cur=test
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def wrp(d,text,font,x,y,max_w,fill,gap=1.45):
    ls=wrap(d,text,font,max_w); a,de=font.getmetrics(); lh=int((a+de)*gap)
    for ln in ls: d.text((x,y),ln,font=font,fill=fill); y+=lh
    return y

def dots(d,active,dark=False):
    r=5; gap=24; tw=6*gap; cx0=W//2-tw//2
    for i in range(7):
        cx=cx0+i*gap
        if i==active: d.ellipse([cx-r,H-52-r,cx+r,H-52+r],fill=PURPLE)
        else: d.ellipse([cx-r+2,H-52-r+2,cx+r-2,H-52+r-2],fill=LILAC if dark else LILAC_DIM)

def dark_hdr(d,no):
    d.line([(54,82),(W-54,82)],fill=(42,32,52),width=1)
    d.text((54,44),"G E S T A R   B E M",font=pp(22,"Light"),fill=DIM)
    if no: d.text((54,106),no,font=pp(20,"Light"),fill=LILAC_DIM)

def light_hdr(d,tag,no):
    d.line([(54,82),(W-54,82)],fill=LILAC_MID,width=1)
    d.text((54,44),"G E S T A R   B E M",font=pp(22,"Light"),fill=DIM_TXT)
    ft=pp(24,"Bold"); d.text((54,106),tag.upper(),font=ft,fill=PURPLE3)
    tw=int(d.textlength(tag.upper(),font=ft)); d.line([(54,134),(54+tw,134)],fill=LILAC_MID,width=2)
    d.text((W-54-int(d.textlength(no,font=pp(20,"Light"))),106),no,font=pp(20,"Light"),fill=LILAC_DIM)

def dark_ftr(d,insta,nome):
    d.line([(54,H-84),(W-54,H-84)],fill=(36,26,46),width=1)
    ff=pp(22,"Light"); d.text((54,H-60),insta,font=ff,fill=DIM)
    d.ellipse([W//2-3,H-47,W//2+3,H-41],fill=LILAC)
    d.text((W-54-int(d.textlength(nome,font=ff)),H-60),nome,font=ff,fill=DIM)

def light_ftr(d,insta,nome):
    d.line([(54,H-78),(W-54,H-78)],fill=LILAC_MID,width=1)
    ff=pp(22,"Light"); d.text((54,H-54),insta,font=ff,fill=DIM_TXT)
    d.ellipse([W//2-3,H-41,W//2+3,H-35],fill=PURPLE)
    d.text((W-54-int(d.textlength(nome,font=ff)),H-54),nome,font=ff,fill=DIM_TXT)

PANO_D=[(1*W,80,220,PURPLE2,.28),(2*W,H-80,200,PURPLE2,.22),(3*W,60,240,PURPLE2,.25),
        (4*W,H-60,210,PURPLE2,.22),(5*W,80,230,PURPLE2,.26),(6*W,H-80,220,PURPLE2,.24),
        (0,0,180,PURPLE2,.18),(7*W,0,180,PURPLE2,.18),(0,H,180,PURPLE2,.18),(7*W,H,180,PURPLE2,.18)]
PANO_L=[(1*W,80,220,(180,160,200),.18),(2*W,H-80,200,(180,160,200),.16),
        (3*W,60,240,(180,160,200),.18),(4*W,H-60,210,(180,160,200),.16),(5*W,80,230,(180,160,200),.17)]

def get_c(idx,light=False):
    src=PANO_L if light else PANO_D; res=[]
    for cx_g,cy,r,col,op in src:
        cx_l=cx_g-idx*W
        if cx_l+r>0 and cx_l-r<W: res.append((cx_l,cy,r,col,op))
    return res

def ftr_names(cfg):
    insta=cfg.get("insta","@gestarbem_")
    prof=cfg.get("prof","Jéssica D'Agostini")
    nome="por "+prof.split("·")[0].strip()
    return insta,nome

def slide_cover(idx,slide,cfg):
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    bg_grad(d,740,PURPLE2,.7); sidebar(d,LILAC,PURPLE)
    img=circles(img,get_c(idx)); d=ImageDraw.Draw(img)
    dark_hdr(d,"No. 01")
    insta,nome=ftr_names(cfg)
    x=54; y=172
    texto=slide.get("texto",""); label=slide.get("label","")
    words=texto.split(); half=max(1,len(words)//2)
    l1=" ".join(words[:half]); l2=" ".join(words[half:])
    d.text((x,y),l1,font=lora(102,True),fill=CREAM); a,de=lora(102,True).getmetrics(); y+=a+de+6
    d.line([(x,y),(x+380,y)],fill=PURPLE,width=2); y+=18
    d.text((x,y),l2,font=lora(72,True),fill=LILAC_DIM); a,de=lora(72,True).getmetrics(); y+=a+de+36
    d.line([(x,y),(x+180,y)],fill=(40,28,50),width=1); y+=20
    y=wrp(d,label,pp(32,"Light"),x,y,W-120,DIM,1.45); y+=32
    fh=pp(22,"Light"); col=(100,88,112)
    d.text((x,y),"arraste para ver",font=fh,fill=col)
    aw=int(d.textlength("arraste para ver",font=fh)); ax,ay=x+aw+12,y+12
    for pts in [[(ax,ay),(ax+32,ay)],[(ax+32,ay),(ax+21,ay-7)],[(ax+32,ay),(ax+21,ay+7)]]: d.line(pts,fill=col,width=2)
    a,de=fh.getmetrics(); y+=a+de+48
    d.line([(x,y),(x+W-108,y)],fill=(48,34,58),width=1); y+=16
    d.text((x,y),"\u201c",font=lora(52,True),fill=ACCENT); a,de=lora(52,True).getmetrics(); y+=a+de+4
    d.text((x,y),"Seu corpo está trabalhando",font=lora(40),fill=CREAM); a,de=lora(40).getmetrics(); y+=a+de+2
    d.text((x,y),"por você e pelo bebê.",font=lora(40),fill=CREAM); a,de=lora(40).getmetrics(); y+=a+de+10
    d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(20,"Light"),fill=LILAC_DIM)
    dots(d,idx,dark=True); dark_ftr(d,insta,nome)
    return grain(img,11)

def slide_light(idx,slide,cfg):
    img=Image.new("RGB",(W,H),LILAC_BG); d=ImageDraw.Draw(img)
    img=circles(img,get_c(idx,light=True)); d=ImageDraw.Draw(img)
    sidebar(d,LILAC,PURPLE)
    label=slide.get("label","Conteúdo"); texto=slide.get("texto","")
    no=f"No. {str(idx+1).zfill(2)}"
    light_hdr(d,label,no)
    insta,nome=ftr_names(cfg)
    x=54; y=185
    words=label.split()
    if len(words)>=2:
        d.text((x,y),words[0],font=lora(68,True),fill=DARK_TXT); a,de=lora(68,True).getmetrics(); y+=a+de+2
        d.text((x,y)," ".join(words[1:]),font=lora(68,True),fill=PURPLE); a,de=lora(68,True).getmetrics(); y+=a+de+24
    else:
        d.text((x,y),label,font=lora(68,True),fill=PURPLE); a,de=lora(68,True).getmetrics(); y+=a+de+24
    d.line([(x,y),(x+240,y)],fill=LILAC_MID,width=2); y+=26
    wrp(d,texto,pp(34,"Regular"),x,y,W-120,DARK_TXT,1.48)
    dots(d,idx); light_ftr(d,insta,nome)
    return grain(img,8)

def slide_emotional(idx,slide,cfg):
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    bg_grad(d,600,PURPLE2,.6); sidebar(d,LILAC,PURPLE)
    img=circles(img,get_c(idx)); d=ImageDraw.Draw(img)
    dark_hdr(d,f"No. {str(idx+1).zfill(2)}")
    insta,nome=ftr_names(cfg)
    x=54; y=200
    label=slide.get("label",""); texto=slide.get("texto","")
    d.text((x,y),"\u201c",font=lora(90,True),fill=PURPLE); a,de=lora(90,True).getmetrics(); y+=a+de-10
    parts=label.split("|") if "|" in label else [label]
    for i,ln in enumerate(parts[:3]):
        col=PURPLE if i==len(parts[:3])-1 else CREAM
        d.text((x,y),ln.strip(),font=lora(82,True),fill=col); a,de=lora(82,True).getmetrics(); y+=a+de+4
    y+=12; d.line([(x,y),(x+280,y)],fill=(60,42,70),width=1); y+=26
    y=wrp(d,texto,pp(32,"Light"),x,y,W-120,DIM,1.48); y+=24
    d.text((x,y),"— Jéssica D'Agostini · Nutricionista",font=pp(22,"Light"),fill=LILAC_DIM)
    dots(d,idx,dark=True); dark_ftr(d,insta,nome)
    return grain(img,11)

def slide_cta(idx,slide,cfg):
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    bg_grad(d,440,PURPLE2,.78); sidebar(d,LILAC,PURPLE)
    img=circles(img,get_c(idx)); d=ImageDraw.Draw(img)
    d.line([(54,82),(W-54,82)],fill=(42,32,52),width=1)
    d.text((54,44),"G E S T A R   B E M",font=pp(22,"Light"),fill=DIM)
    insta,nome=ftr_names(cfg)
    x=54; y=160
    texto=slide.get("texto","Cada gestação é única.")
    parts=texto.split("."); titulo=parts[0].strip()+"."
    resto=".".join(parts[1:]).strip() if len(parts)>1 else ""
    d.text((x,y),titulo,font=lora(80,True),fill=CREAM); a,de=lora(80,True).getmetrics(); y+=a+de+12
    d.line([(x,y),(x+280,y)],fill=PURPLE,width=2); y+=26
    if resto: y=wrp(d,resto,pp(33,"Light"),x,y,W-120,DIM,1.46); y+=28
    for txt in ["Salva este post para os dias difíceis.","Comenta aqui: você já sabia disso? 👇"]:
        d.ellipse([x,y+7,x+12,y+19],fill=LILAC)
        ls=wrap(d,txt,pp(31,"Medium"),W-150); a,de=pp(31,"Medium").getmetrics(); lh=int((a+de)*1.38)
        for i,ln in enumerate(ls): d.text((x+28,y+i*lh),ln,font=pp(31,"Medium"),fill=CREAM)
        y+=lh*len(ls)+22
    y+=20
    d.rounded_rectangle([x,y,W-54,y+88],radius=20,fill=(40,28,52))
    d.rounded_rectangle([x,y,W-54,y+88],radius=20,outline=PURPLE,width=2)
    label=f"{cfg.get('nome','Gestar Bem')} · {insta}"
    lw=int(d.textlength(label,font=pp(26,"Bold")))
    d.text((W//2-lw//2,y+26),label,font=pp(26,"Bold"),fill=LILAC)
    dots(d,idx,dark=True); dark_ftr(d,insta,nome)
    return grain(img,11)

# ── rotas ─────────────────────────────────────────────────────────────────────

@app.after_request
def cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/", methods=["GET"])
def health():
    fonts_ok = all(os.path.exists(os.path.join(FONT_DIR,f)) for f in FONTS_NEEDED)
    return jsonify({"status":"ok","service":"Gestar Bem Image Generator","fonts":fonts_ok})

@app.route("/gerar", methods=["POST","OPTIONS"])
def gerar():
    if request.method=="OPTIONS":
        return jsonify({}), 200
    try:
        data   = request.get_json(force=True)
        slides = data.get("slides",[])
        cfg    = data.get("cfg",{})
        if not slides:
            return jsonify({"erro":"Nenhum slide enviado"}), 400
        n=len(slides); images=[]
        for i,slide in enumerate(slides):
            if   i==0:   img=slide_cover(i,slide,cfg)
            elif i==n-1: img=slide_cta(i,slide,cfg)
            elif i==n-2: img=slide_emotional(i,slide,cfg)
            else:        img=slide_light(i,slide,cfg)
            images.append((f"slide-{str(i+1).zfill(2)}.png",img))
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as zf:
            for name,img in images:
                ib=io.BytesIO(); img.save(ib,"PNG"); zf.writestr(name,ib.getvalue())
        buf.seek(0)
        return send_file(buf,mimetype="application/zip",as_attachment=True,download_name="gestar-bem-carrossel.zip")
    except Exception as e:
        import traceback
        return jsonify({"erro":str(e),"traceback":traceback.format_exc()}), 500

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
