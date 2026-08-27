"""
Roda uma vez para baixar as fontes necessárias.
Execute: python download_fonts.py
"""
import urllib.request, os

os.makedirs("fonts", exist_ok=True)

fonts = {
    "Lora-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "Lora-Bold.ttf":    "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "Poppins-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "Poppins-Medium.ttf":  "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
    "Poppins-Bold.ttf":    "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-Light.ttf":   "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Light.ttf",
}

for name, url in fonts.items():
    dest = os.path.join("fonts", name)
    print(f"Baixando {name}...")
    urllib.request.urlretrieve(url, dest)

print("Fontes baixadas!")
