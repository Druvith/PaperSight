"""Generate realistic test form images for GemmaSight.

Creates photographed-paper-form style images with handwritten-style text
to test the Ollama extraction pipeline.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import os

OUTPUT_DIR = "/Users/druvithgowda/Desktop/validation-hackathon/tests/fixtures/forms"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Warm paper background color
PAPER_BG = (250, 247, 240)
TEXT_COLOR = (45, 40, 35)
LIGHT_TEXT = (140, 130, 120)
ACCENT_COLOR = (180, 60, 60)

def make_paper_texture(width, height):
    """Create a slightly noisy paper texture."""
    img = Image.new('RGB', (width, height), PAPER_BG)
    pixels = img.load()
    for x in range(width):
        for y in range(height):
            noise = random.randint(-8, 8)
            r = max(0, min(255, PAPER_BG[0] + noise))
            g = max(0, min(255, PAPER_BG[1] + noise))
            b = max(0, min(255, PAPER_BG[2] + noise))
            pixels[x, y] = (r, g, b)
    return img

def draw_handwritten_text(draw, text, pos, font_size=18, color=TEXT_COLOR, jitter=1):
    """Draw text with slight jitter to simulate handwriting."""
    x, y = pos
    # Use default font since we may not have custom handwriting fonts
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Draw each character with slight offset for handwriting feel
    cx = x
    for char in text:
        offset_y = random.randint(-jitter, jitter)
        offset_x = random.randint(-1, 1)
        draw.text((cx + offset_x, y + offset_y), char, fill=color, font=font)
        bbox = draw.textbbox((0, 0), char, font=font)
        cx += (bbox[2] - bbox[0]) + random.randint(0, 2)

def draw_form_field(draw, label, value, y_pos, width=500, label_color=LIGHT_TEXT, value_color=TEXT_COLOR):
    """Draw a labeled form field."""
    # Label
    draw.text((40, y_pos), label, fill=label_color)
    # Underline
    draw.line([(150, y_pos + 22), (width - 40, y_pos + 22)], fill=(200, 190, 180), width=1)
    # Value
    if value:
        draw.text((155, y_pos - 2), value, fill=value_color)

def generate_form(filename, patient_data, quality="good", add_stains=False, rotation=0):
    """Generate a photographed form image."""
    width, height = 600, 800
    img = make_paper_texture(width, height)
    draw = ImageDraw.Draw(img)
    
    # Header
    try:
        header_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
        sub_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except:
        header_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
    
    draw.text((40, 30), "RURAL HEALTH CENTER", fill=ACCENT_COLOR, font=header_font)
    draw.text((40, 58), "Patient Intake Form", fill=LIGHT_TEXT, font=sub_font)
    draw.text((40, 80), "-" * 60, fill=(200, 190, 180))
    
    # Fields
    y = 120
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
        draw_form_field(draw, label, value, y, width)
        y += 55
    
    # Signature area
    y += 20
    draw.text((40, y), "Signature:", fill=LIGHT_TEXT)
    draw.line([(150, y + 22), (300, y + 22)], fill=(100, 90, 80), width=1)
    # Scribble signature
    scribble_points = []
    sx = 155
    sy = y + 10
    for i in range(20):
        scribble_points.append((sx, sy))
        sx += random.randint(3, 8)
        sy += random.randint(-3, 3)
    if len(scribble_points) > 1:
        draw.line(scribble_points, fill=(60, 50, 40), width=1)
    
    # Date stamp
    draw.text((400, y), "Date: 27/04/2026", fill=LIGHT_TEXT, font=sub_font)
    
    # Add stains if requested
    if add_stains:
        for _ in range(random.randint(2, 5)):
            sx = random.randint(50, width - 50)
            sy = random.randint(100, height - 50)
            r = random.randint(8, 20)
            draw.ellipse([(sx-r, sy-r), (sx+r, sy+r)], fill=(220, 210, 190, 80))
    
    # Quality degradation
    if quality == "blurry":
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    elif quality == "noisy":
        pixels = img.load()
        for x in range(0, width, 2):
            for y in range(0, height, 2):
                r, g, b = pixels[x, y]
                noise = random.randint(-20, 20)
                pixels[x, y] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, g + noise)),
                    max(0, min(255, b + noise))
                )
    elif quality == "overexposed":
        pixels = img.load()
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                pixels[x, y] = (
                    min(255, r + 40),
                    min(255, g + 40),
                    min(255, b + 30)
                )
    
    # Slight rotation to simulate handheld photo
    if rotation != 0:
        img = img.rotate(rotation, fillcolor=PAPER_BG, expand=True)
    
    # Crop back to reasonable size if rotated
    if rotation != 0:
        w, h = img.size
        img = img.crop((20, 20, w - 20, h - 20))
    
    # Resize to simulate phone camera resolution
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    
    img.save(os.path.join(OUTPUT_DIR, filename), "JPEG", quality=85)
    print(f"Generated: {filename}")

# Generate test forms
forms = [
    {
        "filename": "form_01_clear.jpg",
        "data": {
            "patient_name": "Ravi Shankar",
            "age": "67",
            "gender": "Male",
            "chief_complaint": "Chest-pain radiating to arm",
            "duration": "15 minutes",
            "allergies": "None known",
            "medications": "Aspirin 75mg",
            "referred_by": "Ambulance",
        },
        "quality": "good",
        "rotation": random.randint(-2, 2),
    },
    {
        "filename": "form_02_fever.jpg",
        "data": {
            "patient_name": "Lakshmi Devi",
            "age": "34",
            "gender": "Female",
            "chief_complaint": "High-fever and severe-headache",
            "duration": "2 days",
            "allergies": "Sulfa drugs",
            "medications": "Paracetamol",
            "referred_by": "ASHA worker",
        },
        "quality": "good",
        "rotation": random.randint(-3, 3),
    },
    {
        "filename": "form_03_blurry.jpg",
        "data": {
            "patient_name": "Suresh Patel",
            "age": "58",
            "gender": "Male",
            "chief_complaint": "Difficulty-breathing",
            "duration": "45 min",
            "allergies": "None",
            "medications": "Amlodipine",
            "referred_by": "Self",
        },
        "quality": "blurry",
        "rotation": random.randint(-4, 4),
        "add_stains": True,
    },
    {
        "filename": "form_04_pediatric.jpg",
        "data": {
            "patient_name": "Aarav Sharma",
            "age": "4",
            "gender": "Male",
            "chief_complaint": "High-fever and vomiting",
            "duration": "6 hours",
            "allergies": "Penicillin",
            "medications": "ORS sachets",
            "referred_by": "Mother",
        },
        "quality": "noisy",
        "rotation": random.randint(-5, 5),
    },
    {
        "filename": "form_05_overexposed.jpg",
        "data": {
            "patient_name": "Meena Kumari",
            "age": "72",
            "gender": "Female",
            "chief_complaint": "Fall and hip-pain",
            "duration": "3 hours",
            "allergies": "None known",
            "medications": "Calcium supplements",
            "referred_by": "Family member",
        },
        "quality": "overexposed",
        "rotation": random.randint(-3, 3),
    },
    {
        "filename": "form_06_pregnancy.jpg",
        "data": {
            "patient_name": "Sunita Rao",
            "age": "26",
            "gender": "Female",
            "chief_complaint": "Abdominal-pain and bleeding",
            "duration": "1 hour",
            "allergies": "None",
            "medications": "Iron tablets",
            "referred_by": "ANM",
        },
        "quality": "good",
        "rotation": random.randint(-2, 2),
        "add_stains": True,
    },
]

for form in forms:
    generate_form(
        form["filename"],
        form["data"],
        quality=form["quality"],
        rotation=form["rotation"],
        add_stains=form.get("add_stains", False)
    )

print(f"\nAll {len(forms)} test forms generated in {OUTPUT_DIR}")
