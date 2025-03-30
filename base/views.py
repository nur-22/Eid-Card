from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import os
import json
import textwrap
from django.views.decorators.csrf import csrf_exempt


TEMPLATES_DIR = os.path.join(settings.STATICFILES_DIRS[0], "images")
GENERATED_CARDS_DIR = os.path.join(settings.STATICFILES_DIRS[0], "generated_cards")
FONTS_DIR = os.path.join(settings.STATICFILES_DIRS[0], "fonts")


if not os.path.exists(GENERATED_CARDS_DIR):
    os.makedirs(GENERATED_CARDS_DIR, exist_ok=True)

def home(request):
    if not os.path.exists(TEMPLATES_DIR):
        return JsonResponse({"error": "Template directory not found!"}, status=500)

    template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith((".png", ".jpg", ".jpeg"))]

    return render(request, "home.html", {"templates": template_files})

@csrf_exempt
def generate_card(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            template_name = data.get("template")
            name = data.get("name", "").strip()
            message = data.get("message", "").strip()
            font_color = data.get("font_color", "#0C2D48")  # Default color

            if not template_name or not name or not message:
                return JsonResponse({"error": "Missing required fields: template, name, or message."}, status=400)

            template_path = os.path.join(TEMPLATES_DIR, template_name)
            font_path = os.path.join(FONTS_DIR, "Pacifico-Regular.ttf")

            if not os.path.exists(template_path):
                return JsonResponse({"error": "Template not found."}, status=404)

            image = Image.open(template_path)
            draw = ImageDraw.Draw(image)
            width, height = image.size

            try:
                font_size = int(width * 0.07)
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                font = ImageFont.load_default()

            text_x = width // 2
            text_y = height // 3
            draw.text((text_x, text_y), name, font=font, fill=font_color, anchor="mm")

            message_y = text_y + font_size + 20
            wrapped_text = textwrap.wrap(message, width=30)
            font_size_message = int(width * 0.05)
            font_message = ImageFont.truetype(font_path, font_size_message)

            for line in wrapped_text:
                draw.text((text_x, message_y), line, font=font_message, fill=font_color, anchor="mm")
                message_y += font_size_message + 10

            output_filename = f"{name}_eid_card.png"
            output_path = os.path.join(GENERATED_CARDS_DIR, output_filename)
            image.save(output_path)

            card_url = f"{settings.STATIC_URL}generated_cards/{output_filename}"
            return JsonResponse({"card_url": card_url})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data received"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)
