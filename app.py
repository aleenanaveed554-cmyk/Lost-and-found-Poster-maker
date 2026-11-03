import io
import json
import math
import os
import urllib.request
from datetime import date

import streamlit as st
from groq import Groq
from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    RTL_OK = True
except Exception:  # Urdu shaping libs missing
    RTL_OK = False

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(page_title="Lost & Found Poster Maker", page_icon="🔎", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1200px;}
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        border-radius: 12px; font-weight: 700;
    }
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- CONSTANTS -----------------------------
W, H = 1080, 1350
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Fonts are downloaded once from Google Fonts. For best reliability, commit the
# .ttf files into a "fonts" folder next to app.py and the downloads are skipped.
GF = "https://github.com/google/fonts/raw/main/ofl/"
FONT_SOURCES = {
    "title": ("Poppins-ExtraBold.ttf", GF + "poppins/Poppins-ExtraBold.ttf"),
    "body": ("Poppins-Bold.ttf", GF + "poppins/Poppins-Bold.ttf"),
    "hand": ("Chewy-Regular.ttf", GF + "chewy/Chewy-Regular.ttf"),
    "urdu": ("Amiri-Bold.ttf", GF + "amiri/Amiri-Bold.ttf"),
}
SYSTEM_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

THEMES = {
    "Berry (like reference)": dict(bg="#C2408B", wave="#F5CF4A", base="#C5B3C9", text="#B04468", cyan="#62D9E8"),
    "Ocean blue": dict(bg="#2B6CB0", wave="#FFD166", base="#C9D8EA", text="#1F4E8C", cyan="#7BE0D6"),
    "Forest green": dict(bg="#1F8A70", wave="#F4D35E", base="#CFE3D6", text="#176650", cyan="#8BE3F0"),
    "Sunset orange": dict(bg="#E4572E", wave="#FFC857", base="#F1D6C8", text="#B03A1A", cyan="#6FD6E8"),
}

LABELS = {
    "English": dict(lost_title="LOST", found_title="FOUND", contact="CONTACT", reward="REWARD",
                    lost_loc="LAST SEEN", found_loc="FOUND AT", date="DATE", photo="PHOTO"),
    "Simple English": dict(lost_title="LOST", found_title="FOUND", contact="CALL / WRITE", reward="REWARD",
                           lost_loc="LAST SEEN", found_loc="FOUND AT", date="DATE", photo="PHOTO"),
    "Urdu": dict(lost_title="گمشدہ", found_title="مل گیا", contact="رابطہ", reward="انعام",
                 lost_loc="آخری بار یہاں دیکھا", found_loc="یہاں سے ملا", date="تاریخ", photo="تصویر"),
}


# ----------------------------- FONT HELPERS -----------------------------
@st.cache_resource(show_spinner=False)
def resolve_font(key):
    name, url = FONT_SOURCES[key]
    os.makedirs(FONT_DIR, exist_ok=True)
    path = os.path.join(FONT_DIR, name)
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return path
    try:
        urllib.request.urlretrieve(url, path)
        if os.path.getsize(path) > 10_000:
            return path
    except Exception:
        pass
    for p in SYSTEM_FALLBACKS:
        if os.path.exists(p):
            return p
    return None


def load_font(key, size):
    path = resolve_font(key)
    try:
        if path:
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    return ImageFont.load_default(size=size)


def shape(text, rtl):
    if rtl and RTL_OK:
        return get_display(arabic_reshaper.reshape(text), base_dir="R")
    return text


def text_w(draw, s, font):
    b = draw.textbbox((0, 0), s, font=font)
    return b[2] - b[0]


def wrap_lines(draw, text, font, max_w, rtl):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(draw, shape(trial, rtl), font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, font_key, max_w, max_h, max_size, min_size, rtl, max_lines, spacing=1.3):
    """Shrink the font until the wrapped text fits the box."""
    font, lines = None, []
    for size in range(max_size, min_size - 1, -2):
        font = load_font(font_key, size)
        lines = wrap_lines(draw, text, font, max_w, rtl)
        if len(lines) <= max_lines and len(lines) * size * spacing <= max_h:
            break
    return font, lines


def draw_centered(draw, lines, font, cx, y, fill, rtl, spacing=1.3):
    for line in lines:
        draw.text((cx, y), shape(line, rtl), font=font, fill=fill, anchor="ma")
        y += int(font.size * spacing)
    return y


# ----------------------------- DRAWING HELPERS -----------------------------
def wave_points(y0, amp, period, phase):
    pts = [(x, y0 + amp * math.sin(2 * math.pi * x / period + phase)) for x in range(0, W + 8, 8)]
    return pts


def sparkle(draw, cx, cy, r, fill):
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rad = r if i % 2 == 0 else r * 0.28
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def make_photo(photo_bytes, size, item_name, label, fill_color, text_color):
    w, h = size
    if photo_bytes:
        img = Image.open(io.BytesIO(photo_bytes))
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageOps.fit(img, size, method=Image.LANCZOS, centering=(0.5, 0.5))
    else:
        img = Image.new("RGB", size, fill_color)
        d = ImageDraw.Draw(img)
        f = load_font("title", 90)
        d.text((w / 2, h / 2 - 20), label, font=f, fill=text_color, anchor="mm")
    return img


def build_poster(data, theme_name, photo_bytes, language):
    theme = THEMES[theme_name]
    L = LABELS[language]
    rtl = language == "Urdu"
    is_lost = data["notice_type"] == "Lost"
    cx = W // 2

    img = Image.new("RGB", (W, H), theme["bg"])
    d = ImageDraw.Draw(img)

    # Waves: yellow band, then lavender base
    top_wave = wave_points(560, 38, 700, 0.6) + [(W, H), (0, H)]
    d.polygon(top_wave, fill=theme["wave"])
    base_wave = wave_points(805, 34, 760, 2.4) + [(W, H), (0, H)]
    d.polygon(base_wave, fill=theme["base"])

    # Sparkles on the yellow wave
    for sx, sy, sr in [(90, 640, 14), (160, 720, 9), (960, 610, 12), (1010, 700, 8), (60, 560, 8)]:
        sparkle(d, sx, sy, sr, "#FFFFFF")

    hand_key = "urdu" if rtl else "hand"
    title_key = "urdu" if rtl else "title"
    body_key = "urdu" if rtl else "body"
    up = (lambda s: s) if rtl else (lambda s: s.upper())

    # Kicker (small cyan text)
    f, lines = fit_text(d, up(data["kicker"]), hand_key, 940, 70, 56, 28, rtl, 1)
    draw_centered(d, lines, f, cx, 38, theme["cyan"], rtl)

    # Big title
    title = L["lost_title"] if is_lost else L["found_title"]
    f, lines = fit_text(d, title, title_key, 940, 180, 190, 90, rtl, 1, 1.0)
    d.text((cx, 175), shape(lines[0], rtl), font=f, fill="#FFFFFF", anchor="mm")

    # Item name
    f, lines = fit_text(d, up(data["item_name"]), hand_key, 900, 60, 52, 26, rtl, 1)
    draw_centered(d, lines, f, cx, 262, theme["cyan"], rtl)

    # Photo with white rounded frame
    pw, ph = 620, 440
    px, py = (W - pw) // 2 - 40, 335
    border = 14
    d.rounded_rectangle((px - border, py - border, px + pw + border, py + ph + border),
                        radius=64, fill="#FFFFFF")
    photo = make_photo(photo_bytes, (pw, ph), data["item_name"], L["photo"], theme["base"], theme["text"])
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw, ph), radius=52, fill=255)
    img.paste(photo, (px, py), mask)

    # Speech blob (bottom right of photo)
    bx0, by0, bx1, by1 = px + pw - 190, py + ph - 40, px + pw + 240, py + ph + 100
    d.ellipse((bx0, by0, bx1, by1), fill=theme["bg"])
    d.ellipse((bx0 + 70, by0 - 40, bx1 - 40, by1 - 30), fill=theme["bg"])
    blob_w, blob_h = bx1 - bx0, by1 - by0
    layer = Image.new("RGBA", (blob_w, blob_h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    bf, blines = fit_text(ld, up(data["blob"]), hand_key, blob_w - 90, blob_h - 40, 44, 22, rtl, 2, 1.15)
    total_h = len(blines) * int(bf.size * 1.15)
    draw_centered(ld, blines, bf, blob_w // 2, (blob_h - total_h) // 2 - 6, "#FFFFFF", rtl, 1.15)
    layer = layer.rotate(10, expand=True, resample=Image.BICUBIC)
    img.paste(layer, ((bx0 + bx1) // 2 - layer.width // 2, (by0 + by1) // 2 - layer.height // 2 - 8), layer)
    d = ImageDraw.Draw(img)

    # Body text
    f, lines = fit_text(d, data["body"], body_key, 900, 170, 40, 24, rtl, 5)
    y = draw_centered(d, lines, f, cx, 905, theme["text"], rtl)

    # Location + date line
    loc_label = L["lost_loc"] if is_lost else L["found_loc"]
    detail = f'{loc_label}: {data["location"]}   |   {L["date"]}: {data["item_date"]}'
    f2, l2 = fit_text(d, detail, body_key, 940, 80, 30, 20, rtl, 2, 1.25)
    draw_centered(d, l2, f2, cx, max(y + 8, 1058), theme["text"], rtl, 1.25)

    # Cyan contact banner
    d.rectangle((60, 1150, W - 60, 1305), fill=theme["cyan"])
    contact_line = f'{L["contact"]}: {data["contact"]}'
    if data["reward"]:
        f3, l3 = fit_text(d, contact_line, body_key, 920, 60, 46, 22, rtl, 1, 1.1)
        draw_centered(d, l3, f3, cx, 1170, theme["text"], rtl, 1.1)
        reward_line = f'{L["reward"]}: {data["reward"]}'
        f4, l4 = fit_text(d, reward_line, body_key, 920, 50, 34, 20, rtl, 1, 1.1)
        draw_centered(d, l4, f4, cx, 1240, theme["text"], rtl, 1.1)
    else:
        f3, l3 = fit_text(d, contact_line, body_key, 920, 120, 50, 22, rtl, 2, 1.15)
        total = len(l3) * int(f3.size * 1.15)
        draw_centered(d, l3, f3, cx, 1150 + (155 - total) // 2, theme["text"], rtl, 1.15)

    return img


def to_jpg_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, subsampling=0, optimize=True)
    return buf.getvalue()


# ----------------------------- AI -----------------------------
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def local_fallback(notice_type, item_name, description, language):
    if language == "Urdu":
        return dict(
            kicker="کچھ گم ہو گیا؟" if notice_type == "Lost" else "کچھ ملا ہے؟",
            blob="مدد کریں!" if notice_type == "Lost" else "مالک کو ڈھونڈیں!",
            body=description,
        )
    if notice_type == "Lost":
        return dict(kicker="Have you seen this?", blob="Help me come home!", body=description)
    return dict(kicker="Found something?", blob="Help me find my owner!", body=description)


def generate_copy(api_key, model, notice_type, item_name, description, location,
                  item_date, reward, language, tone):
    client = Groq(api_key=api_key)
    prompt = f"""
Write short wording for a LOST AND FOUND poster. Language: {language}. Tone: {tone}.
Notice type: {notice_type}
Item / pet / person: {item_name}
Details from the user: {description}
Location: {location}
Date: {item_date}
Reward: {reward or "none"}

Return ONLY a JSON object with exactly these keys:
- "kicker": a short hook line, max 6 words (example: "Missing something? Check this")
- "blob": a short speech-bubble line, max 5 words (example: "Help me find my owner!")
- "body": 2 short sentences (max 35 words) describing the item and asking people to help.

Rules: do NOT invent facts. Do NOT include phone numbers, emails, addresses or dates in any field
(they are added separately). Use only the details given above. No markdown.
"""
    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise public-notice copywriter. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_completion_tokens=2000,  # reasoning models need room, 450 was too small
    )
    if "gpt-oss" in model:
        kwargs["reasoning_effort"] = "low"
    try:
        resp = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
    except Exception:
        resp = client.chat.completions.create(**kwargs)

    raw = (resp.choices[0].message.content or "").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return JSON.")
    obj = json.loads(raw[start:end + 1])
    return dict(
        kicker=str(obj.get("kicker", "")).strip() or "Have you seen this?",
        blob=str(obj.get("blob", "")).strip() or "Please help!",
        body=str(obj.get("body", "")).strip() or description,
    )


# ----------------------------- SIDEBAR -----------------------------
with st.sidebar:
    st.markdown("## 🔎 Poster Studio")
    model = st.text_input(
        "Groq model",
        value=os.getenv("GROQ_MODEL", get_secret("GROQ_MODEL", "openai/gpt-oss-120b")),
        help="Any chat model enabled in your Groq account, e.g. llama-3.3-70b-versatile",
    )
    key_input = st.text_input("Groq API key (optional)", type="password",
                              help="Leave empty if GROQ_API_KEY is set in Streamlit Secrets.")
    theme_name = st.selectbox("Poster colors", list(THEMES.keys()))
    st.caption("Never upload your API key to GitHub.")

# ----------------------------- HEADER -----------------------------
st.title("🔎 Lost & Found Poster Maker")
st.write("Fill in the details, add a photo, and download a ready-to-print **JPG poster**.")

left, right = st.columns([1, 1], gap="large")

with left:
    with st.form("poster_form"):
        notice_type = st.selectbox("Notice type *", ["Lost", "Found"])
        item_name = st.text_input("What is lost or found? *", placeholder="e.g. Black wallet, brown dog")
        description = st.text_area("Description and identifying details *", height=110,
                                   placeholder="Colour, size, marks, what makes it recognisable...")
        c1, c2 = st.columns(2)
        with c1:
            location = st.text_input("Location *", placeholder="Area, street or landmark")
        with c2:
            item_date = st.date_input("Date *", value=date.today(), max_value=date.today())
        contact = st.text_input("Contact information *", placeholder="Phone number or email")
        reward = st.text_input("Reward (optional)")
        photo_file = st.file_uploader("Photo of the item (optional)", type=["jpg", "jpeg", "png", "webp"])
        language = st.selectbox("Poster language", ["English", "Simple English", "Urdu"])
        tone = st.selectbox("Writing style", ["Professional and clear",
                                              "Friendly and community-focused", "Short and urgent"])
        submitted = st.form_submit_button("✨ Generate poster", use_container_width=True)

    if submitted:
        if not all([item_name.strip(), description.strip(), location.strip(), contact.strip()]):
            st.error("Please complete all required fields.")
        elif language == "Urdu" and not RTL_OK:
            st.error("Urdu needs `arabic-reshaper` and `python-bidi` in requirements.txt.")
        else:
            api_key = key_input.strip() or get_secret("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")
            with st.spinner("Writing the wording and designing your poster..."):
                try:
                    if not api_key:
                        raise RuntimeError("No Groq API key found.")
                    copy = generate_copy(api_key, model.strip(), notice_type, item_name.strip(),
                                         description.strip(), location.strip(), item_date.isoformat(),
                                         reward.strip(), language, tone)
                except Exception as exc:
                    st.warning(f"AI wording failed, using your own text instead. ({exc})")
                    copy = local_fallback(notice_type, item_name.strip(), description.strip(), language)

                st.session_state["poster"] = dict(
                    notice_type=notice_type,
                    item_name=item_name.strip(),
                    location=location.strip(),
                    item_date=item_date.strftime("%d %b %Y"),
                    contact=contact.strip(),
                    reward=reward.strip(),
                    language=language,
                    photo=photo_file.getvalue() if photo_file else None,
                    **copy,
                )

with right:
    st.subheader("Poster preview")
    data = st.session_state.get("poster")
    if data:
        poster = build_poster(data, theme_name, data["photo"], data["language"])
        st.image(poster, use_container_width=True)
        st.download_button("⬇️ Download poster (JPG)", data=to_jpg_bytes(poster),
                           file_name="lost_found_poster.jpg", mime="image/jpeg",
                           use_container_width=True)
        st.caption("Tip: change the colors in the sidebar and the poster updates instantly.")
    else:
        st.info("Your poster will appear here after you click **Generate poster**.")
