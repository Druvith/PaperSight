"""Generate a crystal-clear test form for the elderly fall case."""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "/Users/druvithgowda/Desktop/validation-hackathon/tests/fixtures/forms"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Clean white paper
PAPER_BG = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
LABEL_COLOR = (100, 100, 100)
ACCENT_COLOR = (160, 50, 50)

def generate_clear_form(filename, patient_data):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), PAPER_BG)
    draw = ImageDraw.Draw(img)
    
    # Load clean fonts
    try:
        header_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
        sub_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
        value_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    except:
        header_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
    
    # Header
    draw.text((60, 40), "RURAL HEALTH CENTER", fill=ACCENT_COLOR, font=header_font)
    draw.text((60, 80), "Patient Intake Form", fill=LABEL_COLOR, font=sub_font)
    draw.line([(60, 115), (width - 60, 115)], fill=(200, 200, 200), width=2)
    
    # Fields with large clear text
    y = 160
    fields = [
        ("Patient Name:", patient_data.get("patient_name", "")),
        ("Age:", patient_data.get("age", "")),
        ("Gender:", patient_data.get("gender", "")),
        ("Chief Complaint:", patient_data.get("chief_complaint", "")),
        ("Duration:", patient_data.get("duration", "")),
        ("Allergies:", patient_data.get("allergies", "")),
        ("Medications:", patient_data.get("medications", "")),
        ("Referred By:", patient_data.get("referred_by", "")),
    ]
    
    for label, value in fields:
        # Label
        draw.text((60, y), label, fill=LABEL_COLOR, font=label_font)
        # Long underline
        draw.line([(220, y + 30), (width - 60, y + 30)], fill=(180, 180, 180), width=2)
        # Value in bold, slightly larger
        if value:
            draw.text((225, y - 2), value, fill=TEXT_COLOR, font=value_font)
        y += 80
    
    # Signature
    y += 30
    draw.text((60, y), "Signature:", fill=LABEL_COLOR, font=label_font)
    draw.line([(180, y + 30), (400, y + 30)], fill=(100, 100, 100), width=2)
    
    # Date
    draw.text((500, y), "Date: 27/04/2026", fill=LABEL_COLOR, font=sub_font)
    
    # No rotation, no blur, no noise - just slight resize
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    
    img.save(os.path.join(OUTPUT_DIR, filename), "JPEG", quality=95)
    print(f"Generated crystal-clear form: {filename}")

# Generate the elderly fall case - crystal clear
generate_clear_form("form_05_clear.jpg", {
    "patient_name": "Meena Kumari",
    "age": "72",
    "gender": "Female",
    "chief_complaint": "Fall and hip-pain",
    "duration": "3 hours",
    "allergies": "None known",
    "medications": "Calcium supplements",
    "referred_by": "Family member",
})

print(f"\nClear form saved to {OUTPUT_DIR}/form_05_clear.jpg")
