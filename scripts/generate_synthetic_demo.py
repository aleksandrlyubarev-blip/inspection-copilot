#!/usr/bin/env python3
"""Generate the deterministic synthetic PCB illustration used by the demo."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = REPO_ROOT / "examples" / "synthetic"


def _base_board() -> Image.Image:
    image = Image.new("RGB", (960, 540), "#0d2f28")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (70, 70, 890, 470),
        radius=28,
        fill="#174a3f",
        outline="#63b89f",
        width=4,
    )

    pad_color = "#d9b45b"
    solder_color = "#d8e0e5"
    for column in range(8):
        x = 160 + column * 85
        draw.rounded_rectangle((x, 205, x + 48, 265), radius=8, fill=pad_color)
        draw.rounded_rectangle((x, 305, x + 48, 365), radius=8, fill=pad_color)
        draw.ellipse((x + 7, 215, x + 41, 255), fill=solder_color)
        draw.ellipse((x + 7, 315, x + 41, 355), fill=solder_color)

    draw.text((96, 96), "SYNTHETIC QC FIXTURE", fill="#d7fff2")
    return image


def _bridge_fixture() -> Image.Image:
    image = _base_board()
    draw = ImageDraw.Draw(image)
    solder_color = "#d8e0e5"

    draw.rounded_rectangle((370, 245, 503, 325), radius=18, fill=solder_color)
    draw.rectangle((394, 235, 479, 335), fill=solder_color)
    draw.rectangle((388, 230, 485, 340), outline="#ff6b5f", width=7)
    draw.text((96, 420), "Highlighted region: simulated solder bridge", fill="#ffb4ae")
    return image


def _ambiguous_fixture() -> Image.Image:
    image = _base_board()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((370, 245, 503, 325), radius=18, fill="#bbc8ca")
    image = image.filter(ImageFilter.GaussianBlur(radius=7))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 78))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.text((96, 420), "Degraded image: automatic verdict unavailable", fill="#ffd28c")
    return image


def main() -> None:
    outputs = {
        "synthetic_bridge.png": _bridge_fixture(),
        "synthetic_ambiguous.png": _ambiguous_fixture(),
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for filename, image in outputs.items():
        output = OUTPUT_DIRECTORY / filename
        image.save(output, format="PNG", optimize=True)
        print(output.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
