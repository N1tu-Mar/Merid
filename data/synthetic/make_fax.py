"""Generate the synthetic referral fax the demo path needs.

Run: python -m data.synthetic.make_fax

Until this existed there was no document anywhere in the repo. The worklist
ran on hand-written feature dicts in referrals.json, which meant the fax
path demonstrated the rule engine reading an answer sheet — the sandbox and
both extractors never ran on it.

The page is built to exercise the things that separate reading a *page* from
reading OCR's flattening of one:

  - the bleeding red flag is a TICKED CHECKBOX, never spelled out in prose
  - the second feature (bowel habit change) is also a checkbox
  - the referring physician's dismissal is a HANDWRITTEN margin note
  - the printed "Requesting:" line says routine

So a text-only reader sees a routine referral for a 42-year-old with no
stated red flags. A reader that sees the page sees two ticked boxes that
fire YOUNG_BLEEDING_PLUS_FEATURE. That gap is the demo.

Everything is synthetic. The patient does not exist and the practice does
not exist.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent
WIDTH, HEIGHT = 1240, 1754  # A4 at 150 DPI

# Fax scans are grey, not white, and that is what the model will see.
PAPER = (247, 245, 240)
INK = (28, 28, 32)
PEN = (16, 32, 120)  # ballpoint blue, for the annotation


def _font(size: int, *, bold: bool = False, italic: bool = False):
    """Best-effort real fonts, falling back to PIL's bitmap default.

    A missing font must not fail the generator — a plainer page is still a
    usable document, and this script runs on whatever laptop is nearest.
    """
    candidates = []
    if italic:
        candidates += ["/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"]
    if bold:
        candidates += ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    candidates += ["/System/Library/Fonts/Supplemental/Arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _checkbox(draw, x: int, y: int, ticked: bool, label: str, font) -> None:
    """A form checkbox. The tick is drawn as strokes, not a character, so it
    reads as a mark on a page rather than as text an OCR pass would find."""
    box = 22
    draw.rectangle([x, y, x + box, y + box], outline=INK, width=2)
    if ticked:
        draw.line([x + 4, y + 11, x + 9, y + box - 5], fill=INK, width=3)
        draw.line([x + 9, y + box - 5, x + box - 3, y + 4], fill=INK, width=3)
    draw.text((x + box + 14, y + 2), label, font=font, fill=INK)


def build() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    d = ImageDraw.Draw(img)

    h1, h2, body, small = _font(38, bold=True), _font(24, bold=True), _font(22), _font(18)
    hand = _font(27, italic=True)

    # fax header strip
    d.text((60, 40), "FAX TRANSMISSION  ::  PAGE 1 OF 1  ::  RECEIVED 07/24/2026 08:14", font=small, fill=(90, 90, 95))
    d.line([60, 70, WIDTH - 60, 70], fill=(150, 150, 155), width=1)

    d.text((60, 100), "CENTRAL VALLEY FAMILY MEDICINE", font=h1, fill=INK)
    d.text((60, 148), "1820 Merced Street, Suite 210  ·  Tel (559) 555-0182  ·  Fax (559) 555-0183", font=small, fill=INK)
    d.line([60, 190, WIDTH - 60, 190], fill=INK, width=3)

    d.text((60, 215), "GASTROENTEROLOGY REFERRAL", font=h2, fill=INK)

    y = 270
    for label, value in [
        ("Patient", "Dara Whitlock"),
        ("DOB", "14 Mar 1984          Age: 42"),
        ("MRN", "CVF-0099817"),
        ("Insurance", "Meridian Health Plan   Member ID: MHP-4471902-01"),
        ("Referred by", "R. Alcarez, MD"),
        ("Date", "23 July 2026"),
    ]:
        d.text((60, y), f"{label}:", font=body, fill=INK)
        d.text((280, y), value, font=body, fill=INK)
        y += 38

    y += 20
    d.line([60, y, WIDTH - 60, y], fill=INK, width=1)
    y += 25
    d.text((60, y), "PRESENTING FEATURES  (tick all that apply)", font=h2, fill=INK)
    y += 48

    # The clinically decisive content is here, as marks on a page.
    for label, ticked in [
        ("Rectal bleeding", True),
        ("Change in bowel habit", True),
        ("Unintentional weight loss", False),
        ("Abdominal pain", False),
        ("Iron deficiency anaemia", False),
        ("Palpable abdominal / rectal mass", False),
    ]:
        _checkbox(d, 70, y, ticked, label, body)
        y += 42

    y += 10
    d.text((60, y), "Duration of symptoms:", font=body, fill=INK)
    d.text((340, y), "approximately 3 weeks", font=body, fill=INK)
    y += 42
    d.text((60, y), "FIT / FOBT:", font=body, fill=INK)
    d.text((340, y), "not performed", font=body, fill=INK)
    y += 42
    d.text((60, y), "Previous colonoscopy:", font=body, fill=INK)
    d.text((340, y), "none on record", font=body, fill=INK)
    y += 42
    d.text((60, y), "Family history of bowel cancer:", font=body, fill=INK)
    d.text((340 + 120, y), "none reported", font=body, fill=INK)

    y += 70
    d.line([60, y, WIDTH - 60, y], fill=INK, width=1)
    y += 25
    d.text((60, y), "CLINICAL NOTES", font=h2, fill=INK)
    y += 44
    for line in [
        "42-year-old presenting with a three week history of intermittent",
        "bright red bleeding, with looser stools over the same period.",
        "Otherwise systemically well. Abdomen soft, non-tender.",
    ]:
        d.text((70, y), line, font=body, fill=INK)
        y += 34

    y += 30
    d.text((60, y), "Requesting:", font=body, fill=INK)
    d.text((280, y), "ROUTINE gastroenterology opinion", font=body, fill=INK)

    # The handwritten dismissal — the thing the system has to catch. Drawn
    # in pen blue, tilted, in the margin, exactly where OCR loses it.
    # Placed in clear space rather than over the printed block: the point of
    # the demo is that one reader can see the page and the other cannot, not
    # that the annotation sabotages OCR of the printed text.
    note = Image.new("RGBA", (620, 130), (0, 0, 0, 0))
    nd = ImageDraw.Draw(note)
    nd.text((0, 0), "probable haemorrhoids —", font=hand, fill=PEN)
    nd.text((0, 42), "reassured pt, no urgency", font=hand, fill=PEN)
    nd.line([0, 96, 430, 92], fill=PEN, width=2)
    rotated = note.rotate(-4, expand=True, resample=Image.BICUBIC)
    img.paste(rotated, (150, y + 60), rotated)

    y += 210
    d.text((60, y), "Signed: R. Alcarez, MD", font=body, fill=INK)

    d.text((60, HEIGHT - 60), "DEMO — synthetic data. Not for clinical use.", font=small, fill=(120, 120, 125))
    return img


def main() -> None:
    img = build()
    png = OUT_DIR / "referral_42yo_fax.png"
    pdf = OUT_DIR / "referral_42yo_fax.pdf"
    img.save(png)
    img.save(pdf, "PDF", resolution=150.0)
    print(f"wrote {png} ({png.stat().st_size // 1024} KB)")
    print(f"wrote {pdf} ({pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
