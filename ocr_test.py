import easyocr
import pytesseract
from PIL import Image
from googletrans import Translator

# Use your actual file
image_path = "/mnt/e/rasa_project/signboard.jpg"

# --- EasyOCR ---
reader = easyocr.Reader(['ta', 'en'])  # Tamil + English
results = reader.readtext(image_path)

print("🔎 EasyOCR Results:")
translator = Translator()

for (bbox, text, prob) in results:
    print(f"Detected: {text} (confidence: {prob:.2f})")
    # Translate Tamil text to English
    translated = translator.translate(text, src="ta", dest="en")
    print(f"🌍 Translated: {translated.text}")

# --- Tesseract ---
print("\n🔎 Tesseract Results:")
img = Image.open(image_path)
tess_text = pytesseract.image_to_string(img, lang="tam")
print(tess_text.strip())
