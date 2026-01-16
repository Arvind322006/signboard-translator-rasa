from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import base64
import cv2
import numpy as np
import easyocr
from googletrans import Translator
import re
import json

# 📌 Load place info from JSON
with open("data/places.json", "r", encoding="utf-8") as f:
    places_data = json.load(f)


# 🔹 1. Action for signboard translation
class ActionTranslateSign(Action):
    def name(self):
        return "action_translate_sign"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        detected_text = ""
        metadata = tracker.latest_message.get("metadata", {})
        image_data = metadata.get("image")

        place_found = None

        if image_data:
            # If user uploaded image → OCR + translation
            try:
                header, encoded = image_data.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                reader = easyocr.Reader(['en', 'ta'])
                results = reader.readtext(img)

                if results:
                    detected_text = " ".join([res[1] for res in results])
                else:
                    dispatcher.utter_message(text="❌ Couldn’t detect any text in the image.")
                    return []

            except Exception as e:
                dispatcher.utter_message(text=f"⚠️ Error processing image: {str(e)}")
                return []

        else:
            # If only text → clean input
            user_message = tracker.latest_message.get("text", "").strip()
            if user_message:
                detected_text = re.sub(r"(translate|to english|in english)", "", user_message, flags=re.I).strip()

        # If no text found
        if not detected_text:
            dispatcher.utter_message(text="⚠️ No text provided to translate.")
            return []

        # Translate
        translator = Translator()
        translated = translator.translate(detected_text, src="auto", dest="en")

        # Show detected + translated (always separate bubbles)
        dispatcher.utter_message(text=f"📝 Detected: {detected_text}")
        dispatcher.utter_message(text=f"🌍 English: {translated.text}")

        # Only if IMAGE uploaded → add full place info
        if image_data:
            for place in places_data:
                if place.lower() in detected_text.lower() or place in detected_text or place.lower() in translated.text.lower():
                    place_found = place
                    break

            if place_found:
                info = places_data[place_found]
                response = (
                    f"📌 Overview: {info.get('overview','N/A')}\n\n"
                    f"⭐ Famous: {', '.join(info.get('famous', []))}\n\n"
                    f"✨ Special: {info.get('special','N/A')}\n\n"
                    f"🗺️ Tourist places: {', '.join(info.get('tourist_places', []))}\n\n"
                    f"🍴 Food: {info.get('food','N/A')}\n\n"
                    f"🎭 Culture: {info.get('culture','N/A')}"
                )
                dispatcher.utter_message(text=response)

        return []


# 🔹 2. Action for user queries (famous, special, etc.)
class ActionGetPlaceInfo(Action):
    def name(self):
        return "action_get_place_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        user_message = tracker.latest_message.get("text", "").lower()

        place_found = None
        for place in places_data.keys():
            if place.lower() in user_message:
                place_found = place
                break

        if not place_found:
            dispatcher.utter_message(text="⚠️ I couldn’t find which city you are asking about.")
            return []

        info = places_data[place_found]
        response = ""

        if "overview" in user_message:
            response = f"📌 Overview of {place_found}: {info.get('overview','N/A')}"
        elif "famous" in user_message:
            response = f"⭐ Famous in {place_found}: {', '.join(info.get('famous', []))}"
        elif "special" in user_message:
            response = f"✨ Special in {place_found}: {info.get('special','N/A')}"
        elif "tourist" in user_message or "places" in user_message:
            response = f"🗺️ Tourist places in {place_found}: {', '.join(info.get('tourist_places', []))}"
        elif "food" in user_message:
            response = f"🍴 Famous food in {place_found}: {info.get('food','N/A')}"
        elif "culture" in user_message:
            response = f"🎭 Culture of {place_found}: {info.get('culture','N/A')}"
        else:
            response = (
                f"📌 Overview: {info.get('overview','N/A')}\n\n"
                f"⭐ Famous: {', '.join(info.get('famous', []))}\n\n"
                f"✨ Special: {info.get('special','N/A')}\n\n"
                f"🗺️ Tourist places: {', '.join(info.get('tourist_places', []))}\n\n"
                f"🍴 Food: {info.get('food','N/A')}\n\n"
                f"🎭 Culture: {info.get('culture','N/A')}"
            )

        dispatcher.utter_message(text=response)
        return []
