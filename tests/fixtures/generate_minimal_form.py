"""Generate a minimal form with only age + chief complaint."""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "/Users/druvithgowda/Desktop/validation-hackathon/tests/fixtures/forms"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PAPER_BG = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
LABEL_COLOR = (100, 100, 100)
ACCENT_COLOR = (160, 50, 50)

def generate_minimal_form(filename, age, chief_complaint):
    width, height = 600, 500
    img = Image.new('RGB', (width, height), PAPER_BG)
    draw = ImageDraw.Draw(img)
    
    try:
        header_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
        sub_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
        label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
        value_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    except:
        header_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
    
    # Header
    draw.text((50, 30), "EMERGENCY TRIAGE", fill=ACCENT_COLOR, font=header_font)
    draw.text((50, 65), "Minimal Intake", fill=LABEL_COLOR, font=sub_font)
    draw.line([(50, 95), (width - 50, 95)], fill=(200, 200, 200), width=2)
    
    # Only 2 fields
    y = 140
    
    # Age
    draw.text((50, y), "Age:", fill=LABEL_COLOR, font=label_font)
    draw.line([(150, y + 28), (width - 50, y + 28)], fill=(180, 180, 180), width=2)
    draw.text((155, y - 2), age, fill=TEXT_COLOR, font=value_font)
    
    y += 80
    
    # Chief Complaint
    draw.text((50, y), "Chief Complaint:", fill=LABEL_COLOR, font=label_font)
    draw.line([(200, y + 28), (width - 50, y + 28)], fill=(180, 180, 180), width=2)
    draw.text((205, y - 2), chief_complaint, fill=TEXT_COLOR, font=value_font)
    
    # Footer note
    y += 100
    draw.text((50, y), "Note: Other fields will be collected at bedside.", fill=LABEL_COLOR, font=sub_font)
    
    # No rotation, minimal processing
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    img.save(os.path.join(OUTPUT_DIR, filename), "JPEG", quality=95)
    print(f"Generated minimal form: {filename}")

# Test cases
generate_minimal_form("minimal_01_red.jpg", "67", "chest-pain")
generate_minimal_form("minimal_02_yellow.jpg", "34", "fever and headache")
generate_minimal_form("minimal_03_elderly_fall.jpg", "72", "fall and hip-pain")

print(f"\nAll minimal forms saved to {OUTPUT_DIR}")
