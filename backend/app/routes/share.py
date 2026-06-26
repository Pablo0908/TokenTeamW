"""Public badge-share pages. The shared link serves Open Graph meta tags + a
generated preview card so social platforms (WhatsApp, Facebook, Discord, ...)
render a rich card with the badge name, description, event and 'Join us at Lyfter!'."""
import os
from html import escape
from io import BytesIO

from flask import Blueprint, Response, abort, current_app, request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from app.models import badge as badge_model
from app.models import event as event_model

share_bp = Blueprint("share", __name__)

JOIN_TEXT = "Join us at Lyfter!"
NAVY = (45, 50, 61)
NAVY_DEEP = (12, 15, 22)
WHITE = (243, 245, 250)
MUTED = (170, 178, 192)
# Lyfter brand accents keyed by the badge's color name.
ACCENTS = {
    "primary": (113, 206, 255), "info": (113, 206, 255),
    "secondary": (215, 152, 231), "accent": (255, 204, 139),
    "warning": (255, 204, 139), "success": (173, 209, 149),
    "error": (232, 143, 149),
}
_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _font(size, bold=False):
    for path in (
        f"C:/Windows/Fonts/segoeui{'b' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and (cur or words):
        # ellipsize the last line if content remains
        last = lines[-1]
        while draw.textlength(last + "…", font=font) > max_w and len(last) > 1:
            last = last[:-1]
        if draw.textlength(text, font=font) > max_w * max_lines:
            lines[-1] = last + "…"
    return lines


def _card_png(name, description, event_name, color):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), NAVY_DEEP)
    d = ImageDraw.Draw(img)
    accent = ACCENTS.get(color, ACCENTS["primary"])

    # vertical wash + accent glow corner
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(
            int(NAVY[0] * (1 - t) + NAVY_DEEP[0] * t),
            int(NAVY[1] * (1 - t) + NAVY_DEEP[1] * t),
            int(NAVY[2] * (1 - t) + NAVY_DEEP[2] * t),
        ))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W - 340, -220, W + 200, 300], fill=accent + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)

    pad = 80
    # header: logo + LYFTER wordmark
    y = pad
    try:
        logo = Image.open(os.path.join(_ASSETS, "lyfter-logo.png")).convert("RGBA").resize((96, 96), Image.LANCZOS)
        img.paste(logo, (pad, y), logo)
        d.text((pad + 116, y + 26), "LYFTER", font=_font(46, bold=True), fill=WHITE)
    except Exception:
        d.text((pad, y + 26), "LYFTER", font=_font(46, bold=True), fill=WHITE)
    y += 150
    d.line([(pad, y), (pad + 120, y)], fill=accent, width=6)
    y += 36

    # badge name
    nf = _font(74, bold=True)
    for ln in _wrap(d, name or "Badge", nf, W - 2 * pad, 2):
        d.text((pad, y), ln, font=nf, fill=WHITE)
        y += 88

    # description
    if description:
        y += 8
        df = _font(34)
        for ln in _wrap(d, description, df, W - 2 * pad, 2):
            d.text((pad, y), ln, font=df, fill=MUTED)
            y += 46

    # event (drawn dot marker — avoids font glyph gaps)
    if event_name:
        y += 18
        d.ellipse([pad, y + 8, pad + 20, y + 28], fill=accent)
        d.text((pad + 34, y), event_name, font=_font(34, bold=True), fill=accent)

    # call to action (bottom)
    d.text((pad, H - pad - 52), JOIN_TEXT, font=_font(52, bold=True), fill=WHITE)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _load(badge_id):
    badge = badge_model.find_by_id(badge_id)
    if not badge:
        abort(404)
    event = event_model.find_by_id(badge.get("event_id")) if badge.get("event_id") else None
    return badge, (event.get("name", "") if event else "")


@share_bp.route("/share/badge/<badge_id>/image.png")
def badge_image(badge_id):
    badge, event_name = _load(badge_id)
    png = _card_png(badge.get("name", ""), badge.get("description", ""), event_name, badge.get("color", "primary"))
    resp = Response(png, mimetype="image/png")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@share_bp.route("/share/badge/<badge_id>")
def badge_page(badge_id):
    badge, event_name = _load(badge_id)
    name = badge.get("name", "Badge")
    desc = badge.get("description", "")
    app_url = current_app.config.get("FRONTEND_URL", "/")
    img_url = request.host_url.rstrip("/") + f"/share/badge/{badge_id}/image.png"
    page_url = request.host_url.rstrip("/") + f"/share/badge/{badge_id}"
    summary = " · ".join(p for p in (desc, event_name) if p)
    og_desc = (summary + " — " if summary else "") + JOIN_TEXT

    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(name)} — Lyfter</title>
<meta name="description" content="{escape(og_desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Lyfter">
<meta property="og:url" content="{escape(page_url)}">
<meta property="og:title" content="{escape(name)}">
<meta property="og:description" content="{escape(og_desc)}">
<meta property="og:image" content="{escape(img_url)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(name)}">
<meta name="twitter:description" content="{escape(og_desc)}">
<meta name="twitter:image" content="{escape(img_url)}">
<style>
  body{{margin:0;font-family:'Segoe UI',system-ui,sans-serif;background:#0c0f16;color:#e7eaf1;
    min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;}}
  .card{{max-width:640px;width:100%;text-align:center;}}
  .card img{{width:100%;border-radius:18px;box-shadow:0 30px 70px -30px rgba(0,0,0,.8);}}
  h1{{font-size:1.5rem;margin:22px 0 6px;}}
  p{{color:#aab2c0;margin:0 0 22px;}}
  a.btn{{display:inline-block;background:#71ceff;color:#0f1720;font-weight:700;text-decoration:none;
    padding:14px 26px;border-radius:12px;}}
</style></head>
<body><div class="card">
  <img src="{escape(img_url)}" alt="{escape(name)}">
  <h1>{escape(name)}</h1>
  <p>{escape(og_desc)}</p>
  <a class="btn" href="{escape(app_url)}">Open Lyfter</a>
</div></body></html>"""
    return Response(html, mimetype="text/html")
