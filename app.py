import os
import html
from datetime import date

import streamlit as st
from groq import Groq

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(
    page_title="Lost & Found Poster Maker",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- CUSTOM DESIGN -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #172033;
        --muted: #697386;
        --line: #e7eaf1;
        --purple: #6558e8;
        --purple-dark: #5145cf;
        --surface: #ffffff;
        --soft: #f5f6fb;
    }
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    .stApp {
        background:
          radial-gradient(circle at 80% 0%, rgba(101,88,232,.10), transparent 28rem),
          #f7f8fc;
        color: var(--ink);
    }
    [data-testid="stSidebar"] {
        background: #151b2d;
        border-right: 1px solid rgba(255,255,255,.08);
    }
    [data-testid="stSidebar"] * { color: #edf0ff !important; }
    [data-testid="stSidebar"] .stCaption { color: #aeb7d0 !important; }
    .hero {
        padding: 2.1rem 2.2rem;
        border-radius: 24px;
        color: white;
        background: linear-gradient(118deg, #252d4c 0%, #5145cf 58%, #8177f5 100%);
        box-shadow: 0 18px 45px rgba(48, 43, 120, .18);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero:after {
        content: "✦";
        position: absolute;
        right: 5%;
        top: -35px;
        font-size: 170px;
        opacity: .12;
    }
    .eyebrow {
        text-transform: uppercase;
        letter-spacing: .16em;
        font-size: .72rem;
        font-weight: 800;
        opacity: .78;
    }
    .hero h1 {
        font-family: 'Manrope', sans-serif;
        font-size: clamp(2rem, 4vw, 3rem);
        line-height: 1.1;
        margin: .55rem 0 .65rem;
        font-weight: 800;
        color: white;
    }
    .hero p { color: #ecebff; font-size: 1.02rem; max-width: 650px; margin: 0; }
    .section-heading {
        font-family: 'Manrope', sans-serif;
        font-size: 1.16rem;
        font-weight: 800;
        color: #202942;
        margin: .2rem 0 .25rem;
    }
    .section-sub { color: #788196; font-size: .9rem; margin-bottom: 1rem; }
    div[data-testid="stForm"] {
        background: white;
        border: 1px solid var(--line);
        padding: 1.35rem 1.4rem 1rem;
        border-radius: 20px;
        box-shadow: 0 8px 28px rgba(29, 39, 70, .045);
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label {
        font-weight: 700;
        color: #303b55;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 11px !important;
    }
    .stButton > button, .stFormSubmitButton > button {
        border: 0;
        border-radius: 12px;
        padding: .72rem 1.15rem;
        font-weight: 800;
        color: white;
        background: linear-gradient(110deg, #6558e8, #8177f5);
        box-shadow: 0 8px 18px rgba(101,88,232,.20);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 11px 22px rgba(101,88,232,.27);
    }
    .poster {
        background: #fff;
        border: 1px solid #e6e8f0;
        border-radius: 22px;
        padding: 2rem;
        box-shadow: 0 14px 38px rgba(29,39,70,.08);
        color: #172033;
        max-width: 760px;
        margin: .3rem auto 1rem;
    }
    .poster-top {
        text-align: center;
        padding: 1.3rem 1rem;
        border-radius: 16px;
        color: white;
        background: linear-gradient(125deg, #252d4c, #6558e8);
        margin-bottom: 1.2rem;
    }
    .poster-kicker { letter-spacing: .2em; font-size: .72rem; font-weight: 800; opacity: .8; }
    .poster-title { font-family: 'Manrope', sans-serif; font-size: 2.5rem; line-height: 1.05; font-weight: 900; margin: .45rem 0; }
    .poster-type { font-size: .92rem; font-weight: 700; opacity: .92; }
    .poster-item { font-family: 'Manrope', sans-serif; font-size: 1.8rem; font-weight: 800; text-align: center; margin: .8rem 0; color: #252d4c; }
    .poster-description { color: #515b70; text-align: center; line-height: 1.65; margin: .4rem auto 1.3rem; max-width: 570px; }
    .poster-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: .7rem;
        margin: 1.2rem 0;
    }
    .poster-detail { background: #f5f6fb; border-radius: 12px; padding: .85rem; }
    .poster-detail small { display: block; color: #7b8497; font-size: .7rem; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }
    .poster-detail strong { display: block; color: #252d4c; margin-top: .25rem; overflow-wrap: anywhere; }
    .poster-call { text-align: center; border: 2px dashed #c8c4ff; border-radius: 14px; padding: 1rem; margin-top: 1rem; }
    .poster-call strong { color: #5145cf; font-size: 1.15rem; }
    .poster-footer { color: #8991a2; font-size: .72rem; text-align: center; margin-top: 1rem; }
    .tip {
        border: 1px solid #e6e4ff;
        background: #f1f0ff;
        color: #5145a8;
        border-radius: 14px;
        padding: .9rem 1rem;
        font-size: .88rem;
    }
    .small-stat {
        background: white; border: 1px solid var(--line); border-radius: 14px;
        padding: .85rem 1rem; text-align: center;
    }
    .small-stat b { display: block; font-size: 1.1rem; color: #5145cf; }
    .small-stat span { font-size: .75rem; color: #7b8497; }
    footer { visibility: hidden; }
    @media print {
        .stApp { background: white !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- HELPERS -----------------------------
def get_api_key():
    """Read the key from Streamlit secrets first, then environment variables."""
    try:
        secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("GROQ_API_KEY", "")


def generate_poster_copy(api_key, model, item_type, item_name, description,
                         location, item_date, contact, reward, language, tone):
    client = Groq(api_key=api_key)
    prompt = f"""
Create concise, clear, community-friendly wording for a LOST AND FOUND notice.
The user will place the generated wording inside a poster design.
Write in {language}. Tone: {tone}.
Notice type: {item_type}
Item/person/pet name or short label: {item_name}
Details supplied by the user: {description}
Last seen / found location: {location}
Date: {item_date}
Contact information: {contact}
Reward information: {reward if reward else "No reward mentioned"}

Rules:
- Do not invent facts, phone numbers, addresses, dates, rewards, or identifying details.
- Keep the wording respectful, easy to scan, and suitable for a public notice.
- Use a strong short headline, a short description, and a clear call to action.
- Do not add markdown tables or code fences.
- Do not claim that an item/person/pet has been verified or recovered.
- Include only information provided above.
Return the poster wording only.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a professional public-notice copywriter. Be accurate, calm, concise, and helpful.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.55,
        max_completion_tokens=450,
    )
    return response.choices[0].message.content.strip()


def build_poster_html(item_type, item_name, description, location, item_date,
                      contact, reward, generated_copy, accent):
    safe = lambda value: html.escape(str(value or "Not provided")).replace("\n", "<br>")
    label = "LOST" if item_type == "Lost" else "FOUND"
    reward_html = ""
    if reward:
        reward_html = f'<div class="detail"><small>REWARD</small><b>{safe(reward)}</b></div>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label} - {safe(item_name)}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;padding:28px;background:#f2f3f8;font-family:Arial,sans-serif;color:#172033}}
.poster{{max-width:760px;margin:0 auto;background:white;padding:34px;border-radius:22px;box-shadow:0 12px 36px #17203318}}
.top{{background:{accent};color:white;text-align:center;padding:30px 18px;border-radius:16px}}
.kicker{{font-size:12px;letter-spacing:4px;font-weight:bold;opacity:.85}}
h1{{font-size:54px;margin:12px 0 5px}} .type{{font-size:15px;font-weight:bold}}
h2{{font-size:30px;text-align:center;margin:26px 0 10px}}
.copy{{white-space:pre-wrap;text-align:center;line-height:1.6;color:#515b70;font-size:16px}}
.details{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:24px 0}}
.detail{{background:#f5f6fb;padding:15px;border-radius:12px;overflow-wrap:anywhere}}
small{{display:block;color:#7b8497;font-size:11px;font-weight:bold;letter-spacing:1px;margin-bottom:6px}}
.call{{border:2px dashed {accent};padding:20px;border-radius:14px;text-align:center;margin-top:18px}}
.call b{{font-size:22px;color:{accent}}}.foot{{text-align:center;color:#8991a2;font-size:11px;margin-top:20px}}
@media(max-width:560px){{.poster{{padding:18px}}h1{{font-size:42px}}.details{{grid-template-columns:1fr}}}}
@media print{{body{{background:white;padding:0}}.poster{{box-shadow:none}}}}
</style></head><body><main class="poster">
<div class="top"><div class="kicker">COMMUNITY NOTICE</div><h1>{label}</h1><div class="type">HELP SPREAD THE WORD</div></div>
<h2>{safe(item_name)}</h2><div class="copy">{safe(generated_copy or description)}</div>
<div class="details">
<div class="detail"><small>LOCATION</small><b>{safe(location)}</b></div>
<div class="detail"><small>DATE</small><b>{safe(item_date)}</b></div>
{reward_html}
</div>
<div class="call"><small>PLEASE CONTACT</small><b>{safe(contact)}</b></div>
<div class="foot">Please share responsibly. Verify details directly with the contact before handing over an item.</div>
</main></body></html>"""


# ----------------------------- SIDEBAR -----------------------------
with st.sidebar:
    st.markdown("## 🔎 Poster Studio")
    st.caption("A simple AI-powered tool for clear community notices.")
    st.markdown("---")
    st.markdown("### ⚙️ AI settings")
    model = st.text_input(
        "Groq model",
        value=os.getenv("GROQ_MODEL", st.secrets.get("GROQ_MODEL", "openai/gpt-oss-120b")),
        help="Use a model ID currently enabled in your Groq account. You can also set GROQ_MODEL in Streamlit Secrets.",
    )
    st.markdown("---")
    st.markdown("### ✨ How it works")
    st.markdown(
        "1. Add the notice details\n"
        "2. Generate clear wording with AI\n"
        "3. Preview your poster\n"
        "4. Download it as an HTML file"
    )
    st.markdown("---")
    st.caption("Keep your Groq API key private. Never upload it to GitHub.")

# ----------------------------- HEADER -----------------------------
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">AI-POWERED COMMUNITY TOOL</div>
      <h1>Lost & Found<br>Poster Maker</h1>
      <p>Create a clear, professional notice in seconds. Add the details, let AI improve the wording, and prepare a poster that is easy to share.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.03, .97], gap="large")

with left:
    st.markdown('<div class="section-heading">Create your notice</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Fill in the details below. Fields marked with * are required.</div>', unsafe_allow_html=True)

    with st.form("poster_form", clear_on_submit=False):
        notice_type = st.selectbox("Notice type *", ["Lost", "Found"])
        item_name = st.text_input(
            "What is lost or found? *",
            placeholder="e.g. Black wallet, brown dog, school bag",
        )
        description = st.text_area(
            "Description and identifying details *",
            placeholder="Describe the item, pet, or other relevant details...",
            height=115,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            location = st.text_input("Location *", placeholder="Area, street, or landmark")
        with col_b:
            item_date = st.date_input("Date *", value=date.today(), max_value=date.today())
        contact = st.text_input(
            "Contact information *",
            placeholder="Phone number or email",
            help="Use a contact method you are comfortable sharing publicly.",
        )
        reward = st.text_input("Reward (optional)", placeholder="e.g. Reward offered / No reward")
        st.markdown("---")
        language = st.selectbox("Poster language", ["English", "Urdu", "Simple English"])
        tone = st.selectbox("Writing style", ["Professional and clear", "Friendly and community-focused", "Short and urgent"])
        submitted = st.form_submit_button("✨ Generate poster wording", use_container_width=True)

    if submitted:
        if not all([item_name.strip(), description.strip(), location.strip(), contact.strip()]):
            st.error("Please complete all required fields before generating your poster.")
        else:
            api_key = get_api_key()
            if not api_key:
                st.error("Groq API key not found. Add GROQ_API_KEY to Streamlit Secrets or your environment variables.")
            elif not model.strip():
                st.error("Please enter a Groq model name in the sidebar.")
            else:
                with st.spinner("Creating your poster wording..."):
                    try:
                        result = generate_poster_copy(
                            api_key, model.strip(), notice_type, item_name.strip(),
                            description.strip(), location.strip(), item_date.isoformat(),
                            contact.strip(), reward.strip(), language, tone,
                        )
                        st.session_state["poster_result"] = {
                            "notice_type": notice_type,
                            "item_name": item_name.strip(),
                            "description": description.strip(),
                            "location": location.strip(),
                            "item_date": item_date.isoformat(),
                            "contact": contact.strip(),
                            "reward": reward.strip(),
                            "copy": result,
                        }
                        st.success("Your poster wording is ready!")
                    except Exception as exc:
                        st.error(f"Could not generate wording. Please check your API key, model name, and internet connection. Details: {exc}")

with right:
    st.markdown('<div class="section-heading">Live poster preview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Your generated notice will appear here.</div>', unsafe_allow_html=True)

    data = st.session_state.get("poster_result")
    if data:
        accent = "#6558e8" if data["notice_type"] == "Lost" else "#16866a"
        label = "LOST" if data["notice_type"] == "Lost" else "FOUND"
        reward_block = ""
        if data["reward"]:
            reward_block = f"""
            <div class="poster-detail"><small>REWARD</small><strong>{html.escape(data['reward'])}</strong></div>
            """
        st.markdown(
            f"""
            <div class="poster">
              <div class="poster-top" style="background:linear-gradient(125deg,#252d4c,{accent})">
                <div class="poster-kicker">COMMUNITY NOTICE</div>
                <div class="poster-title">{label}</div>
                <div class="poster-type">HELP SPREAD THE WORD</div>
              </div>
              <div class="poster-item">{html.escape(data['item_name'])}</div>
              <div class="poster-description">{html.escape(data['copy']).replace(chr(10), '<br>')}</div>
              <div class="poster-details">
                <div class="poster-detail"><small>LOCATION</small><strong>{html.escape(data['location'])}</strong></div>
                <div class="poster-detail"><small>DATE</small><strong>{html.escape(data['item_date'])}</strong></div>
                {reward_block}
              </div>
              <div class="poster-call"><small>PLEASE CONTACT</small><strong>{html.escape(data['contact'])}</strong></div>
              <div class="poster-footer">Please share responsibly. Verify details directly with the contact.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download poster (HTML)",
            data=build_poster_html(
                data["notice_type"], data["item_name"], data["description"],
                data["location"], data["item_date"], data["contact"],
                data["reward"], data["copy"], accent,
            ),
            file_name="lost_found_poster.html",
            mime="text/html",
            use_container_width=True,
        )
        text_version = (
            f"{label} NOTICE\n{data['item_name']}\n\n{data['copy']}\n\n"
            f"Location: {data['location']}\nDate: {data['item_date']}\n"
            f"Contact: {data['contact']}\n"
            + (f"Reward: {data['reward']}\n" if data["reward"] else "")
        )
        st.download_button(
            "📄 Download wording (TXT)",
            data=text_version,
            file_name="lost_found_notice.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.markdown(
            """
            <div class="poster">
              <div class="poster-top">
                <div class="poster-kicker">COMMUNITY NOTICE</div>
                <div class="poster-title">LOST / FOUND</div>
                <div class="poster-type">HELP SPREAD THE WORD</div>
              </div>
              <div class="poster-item">Your item title goes here</div>
              <div class="poster-description">Your AI-generated notice will appear here after you complete the form and click Generate poster wording.</div>
              <div class="poster-details">
                <div class="poster-detail"><small>LOCATION</small><strong>Area or landmark</strong></div>
                <div class="poster-detail"><small>DATE</small><strong>Date of incident</strong></div>
              </div>
              <div class="poster-call"><small>PLEASE CONTACT</small><strong>Your contact details</strong></div>
              <div class="poster-footer">A little information can help bring things back home.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="tip">💡 <b>Tip:</b> Add clear details, but avoid sharing private information such as a full home address.</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#8991a2;font-size:.8rem;padding:.4rem'>Built with Streamlit + Groq · Lost & Found Poster Maker</div>",
    unsafe_allow_html=True,
)
