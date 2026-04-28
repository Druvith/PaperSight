"""Unified form image generator for GemmaSight test fixtures.

Supports three styles:
  * standard  — photographed-paper look with optional noise/blur/rotation
  * clear     — large crisp text, no distortions
  * minimal   — only age + chief complaint

Usage:
    uv run python tests/fixtures/form_generator.py
"""

from __future__ import annotations

import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = Path(__file__).parent / "forms"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Fonts (cross-platform fallback)
# ---------------------------------------------------------------------------
_FONT_CANDIDATES = {
    "header_bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
    "header": [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ],
    "value_bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
    "label": [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ],
}


def _load_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES.get(role, []):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Paper / drawing helpers
# ---------------------------------------------------------------------------
def _paper(width: int, height: int, color: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", (width, height), color)


def _draw_field(
    draw: ImageDraw.ImageDraw,
    label: str,
    value: str,
    y: int,
    width: int,
    fonts: dict[str, ImageFont.FreeTypeFont],
    label_color: tuple[int, int, int],
    value_color: tuple[int, int, int],
    line_color: tuple[int, int, int] = (200, 190, 180),
    label_x: int = 40,
    value_x: int = 155,
    line_x_start: int = 150,
) -> None:
    draw.text((label_x, y), label, fill=label_color, font=fonts["label"])
    draw.line(
        [(line_x_start, y + 22), (width - 40, y + 22)],
        fill=line_color,
        width=1,
    )
    if value:
        draw.text((value_x, y - 2), value, fill=value_color, font=fonts["value"])


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def _style_standard() -> dict:
    return {
        "width": 600,
        "height": 800,
        "paper": (250, 247, 240),
        "text": (45, 40, 35),
        "label": (140, 130, 120),
        "accent": (180, 60, 60),
        "header_size": 22,
        "sub_size": 14,
        "label_size": 18,
        "value_size": 18,
        "field_gap": 55,
        "top_margin": 120,
        "resize_to": None,  # computed later
        "quality": 85,
    }


def _style_clear() -> dict:
    return {
        "width": 800,
        "height": 1000,
        "paper": (255, 255, 255),
        "text": (30, 30, 30),
        "label": (100, 100, 100),
        "accent": (160, 50, 50),
        "header_size": 28,
        "sub_size": 18,
        "label_size": 16,
        "value_size": 22,
        "field_gap": 80,
        "top_margin": 160,
        "resize_to": None,
        "quality": 95,
    }


def _style_minimal() -> dict:
    return {
        "width": 600,
        "height": 500,
        "paper": (255, 255, 255),
        "text": (30, 30, 30),
        "label": (100, 100, 100),
        "accent": (160, 50, 50),
        "header_size": 24,
        "sub_size": 14,
        "label_size": 16,
        "value_size": 20,
        "field_gap": 80,
        "top_margin": 140,
        "resize_to": None,
        "quality": 95,
    }


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------
def generate(
    filename: str,
    data: dict[str, str],
    style: str = "standard",
    rotation: int = 0,
    add_stains: bool = False,
    quality_override: str | None = None,  # "blurry", "noisy", "overexposed"
) -> None:
    """Generate a test form image and save it to OUTPUT_DIR."""
    cfg = {"standard": _style_standard, "clear": _style_clear, "minimal": _style_minimal}[style]()
    w, h = cfg["width"], cfg["height"]

    img = _paper(w, h, cfg["paper"])
    draw = ImageDraw.Draw(img)

    fonts = {
        "header": _load_font("header_bold", cfg["header_size"]),
        "sub": _load_font("header", cfg["sub_size"]),
        "label": _load_font("label", cfg["label_size"]),
        "value": _load_font("value_bold", cfg["value_size"]),
    }

    # Header
    draw.text((40, 30), "RURAL HEALTH CENTER", fill=cfg["accent"], font=fonts["header"])
    draw.text((40, 58 if style == "standard" else 80), "Patient Intake Form", fill=cfg["label"], font=fonts["sub"])
    draw.line([(40, cfg["top_margin"] - 20), (w - 40, cfg["top_margin"] - 20)], fill=(200, 190, 180), width=1 if style == "standard" else 2)

    # Fields
    y = cfg["top_margin"]
    if style == "minimal":
        fields = [
            ("Age:", data.get("age", "")),
            ("Chief Complaint:", data.get("chief_complaint", "")),
        ]
    else:
        fields = [
            ("Patient Name:", data.get("patient_name", "")),
            ("Age:", data.get("age", "")),
            ("Gender:", data.get("gender", "")),
            ("Chief Complaint:", data.get("chief_complaint", "")),
            ("Duration:", data.get("duration", "")),
            ("Allergies:", data.get("allergies", "")),
            ("Medications:", data.get("medications", "")),
            ("Referred By:", data.get("referred_by", "")),
        ]

    for label, value in fields:
        _draw_field(draw, label, value, y, w, fonts, cfg["label"], cfg["text"])
        y += cfg["field_gap"]

    # Signature area (standard only)
    if style == "standard":
        y += 20
        draw.text((40, y), "Signature:", fill=cfg["label"])
        draw.line([(150, y + 22), (300, y + 22)], fill=(100, 90, 80), width=1)
        scribble_points = []
        sx, sy = 155, y + 10
        for _ in range(20):
            scribble_points.append((sx, sy))
            sx += random.randint(3, 8)
            sy += random.randint(-3, 3)
        if len(scribble_points) > 1:
            draw.line(scribble_points, fill=(60, 50, 40), width=1)
        draw.text((400, y), "Date: 27/04/2026", fill=cfg["label"], font=fonts["sub"])

    # Clear form signature
    if style == "clear":
        y += 30
        draw.text((60, y), "Signature:", fill=cfg["label"], font=fonts["label"])
        draw.line([(180, y + 30), (400, y + 30)], fill=(100, 100, 100), width=2)
        draw.text((500, y), "Date: 27/04/2026", fill=cfg["label"], font=fonts["sub"])

    # Minimal footer
    if style == "minimal":
        y += 20
        draw.text(
            (50, y),
            "Note: Other fields will be collected at bedside.",
            fill=cfg["label"],
            font=fonts["sub"],
        )

    # Stains
    if add_stains:
        for _ in range(random.randint(2, 5)):
            sx = random.randint(50, w - 50)
            sy = random.randint(100, h - 50)
            r = random.randint(8, 20)
            draw.ellipse([(sx - r, sy - r), (sx + r, sy + r)], fill=(220, 210, 190, 80))

    # Quality degradation
    if quality_override == "blurry":
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    elif quality_override == "noisy":
        pixels = img.load()
        for x in range(0, w, 2):
            for y in range(0, h, 2):
                r, g, b = pixels[x, y]
                noise = random.randint(-20, 20)
                pixels[x, y] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, g + noise)),
                    max(0, min(255, b + noise)),
                )
    elif quality_override == "overexposed":
        pixels = img.load()
        for x in range(w):
            for y in range(h):
                r, g, b = pixels[x, y]
                pixels[x, y] = (
                    min(255, r + 40),
                    min(255, g + 40),
                    min(255, b + 30),
                )

    # Rotation
    if rotation != 0:
        img = img.rotate(rotation, fillcolor=cfg["paper"], expand=True)
        iw, ih = img.size
        img = img.crop((20, 20, iw - 20, ih - 20))

    # Resize
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)

    out_path = OUTPUT_DIR / filename
    img.save(out_path, "JPEG", quality=cfg["quality"])
    print(f"Generated: {out_path}")


# ---------------------------------------------------------------------------
# Presets (kept compatible with the original three scripts)
# ---------------------------------------------------------------------------
def main() -> None:
    random.seed(42)

    # === Standard forms (from generate_forms.py) ===
    standard_forms = [
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
            "quality_override": None,
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
            "quality_override": None,
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
            "quality_override": "blurry",
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
            "quality_override": "noisy",
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
            "quality_override": "overexposed",
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
            "quality_override": None,
            "rotation": random.randint(-2, 2),
            "add_stains": True,
        },
    ]

    for form in standard_forms:
        generate(
            form["filename"],
            form["data"],
            style="standard",
            rotation=form.get("rotation", 0),
            add_stains=form.get("add_stains", False),
            quality_override=form.get("quality_override"),
        )

    # === Clear form (from generate_clear_form.py) ===
    generate(
        "form_05_clear.jpg",
        {
            "patient_name": "Meena Kumari",
            "age": "72",
            "gender": "Female",
            "chief_complaint": "Fall and hip-pain",
            "duration": "3 hours",
            "allergies": "None known",
            "medications": "Calcium supplements",
            "referred_by": "Family member",
        },
        style="clear",
    )

    # === Minimal forms (from generate_minimal_form.py) ===
    minimal_cases = [
        ("minimal_01_red.jpg", "67", "chest-pain"),
        ("minimal_02_yellow.jpg", "34", "fever and headache"),
        ("minimal_03_elderly_fall.jpg", "72", "fall and hip-pain"),
    ]
    for filename, age, complaint in minimal_cases:
        generate(
            filename,
            {"age": age, "chief_complaint": complaint},
            style="minimal",
        )

    print(f"\nAll test forms generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
