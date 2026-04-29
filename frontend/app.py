import streamlit as st
import requests
import random
import re

st.set_page_config(
    page_title="Emily Grammar Checker AI",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================
# Session State
# ======================================

if "history" not in st.session_state:
    st.session_state.history = []
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "last_result" not in st.session_state:
    st.session_state.last_result = None

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ======================================
# Theme Colors
# ======================================

def get_theme():
    if st.session_state.dark_mode:
        return {
            "bg":           "#0A0A0F",
            "bg2":          "#111118",
            "bg_grad":      "linear-gradient(135deg, #0A0A0F 0%, #12101E 100%)",
            "border":       "#222235",
            "text":         "#E0E0FF",
            "text_muted":   "#6B6B8E",
            "primary":      "#6C63FF",
            "success":      "#00C9A7",
            "danger":       "#FF6B6B",
            "warning":      "#FFB347",
            "info":         "#5BC0EB",
            "input_bg":     "#0D0D15",
            "input_text":   "#E0E0FF",
            "diff_bg":      "#0A0A0F",
            "gemini_bg":    "#0D0D15",
            "card_hover":   "#1A1A28",
        }
    else:
        return {
            "bg":           "#F5F5FF",
            "bg2":          "#FFFFFF",
            "bg_grad":      "linear-gradient(135deg, #F0F0FF 0%, #E8E8FF 100%)",
            "border":       "#D0D0E0",
            "text":         "#1E1E3E",
            "text_muted":   "#6B6B8E",
            "primary":      "#5A52D5",
            "success":      "#00A888",
            "danger":       "#E05555",
            "warning":      "#E09000",
            "info":         "#4A9EC5",
            "input_bg":     "#FFFFFF",
            "input_text":   "#1E1E3E",
            "diff_bg":      "#F0F0FF",
            "gemini_bg":    "#F8F8FF",
            "card_hover":   "#ECECFF",
        }

# ======================================
# CSS
# ======================================

def inject_css(t: dict):
    st.markdown(f"""
    <style>
        /* Background */
        .stApp {{
            background: {t['bg_grad']};
        }}

        /* ✅ ซ่อน toolbar/header/menu */
        #MainMenu, footer {{ visibility: hidden; }}
        [data-testid="stHeader"],
        header[data-testid="stHeader"],
        .stAppToolbar,
        div[class*="stAppToolbar"] {{
            display: none !important;
            height: 0 !important;
        }}

        /* ✅ ซ่อนปุ่ม collapse sidebar */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"] {{
            display: none !important;
        }}

        /* ✅ Sidebar ฟิกตลอด */
        [data-testid="stSidebar"] {{
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            transform: translateX(0) !important;
            visibility: visible !important;
            background: {t['bg2']} !important;
            border-right: 1px solid {t['border']} !important;
        }}
        [data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] > div {{
            background: {t['bg2']} !important;
            width: 280px !important;
        }}

        /* ✅ Sidebar text */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label {{
            color: {t['text']} !important;
        }}

        /* Title */
        .main-title {{
            text-align: center;
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, {t['primary']}, {t['success']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }}
        .sub-title {{
            text-align: center;
            color: {t['text_muted']};
            font-size: 1rem;
            margin-bottom: 2rem;
        }}

        /* Text Area */
        .stTextArea textarea {{
            background: {t['input_bg']} !important;
            color: {t['input_text']} !important;
            border: 2px solid {t['border']} !important;
            border-radius: 12px !important;
            font-size: 1.1rem !important;
            padding: 16px !important;
            transition: border-color 0.3s;
        }}
        .stTextArea textarea:focus {{
            border-color: {t['primary']} !important;
            box-shadow: 0 0 0 3px {t['primary']}33 !important;
        }}
        .stTextArea textarea::placeholder {{
            color: {t['text_muted']} !important;
        }}

        /* Buttons */
        .stButton > button {{
            width: 100%;
            background: linear-gradient(
                135deg, {t['primary']}, {t['primary']}CC
            ) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s !important;
            box-shadow: 0 4px 15px {t['primary']}44 !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px {t['primary']}66 !important;
        }}

        /* Cards */
        .card {{
            background: {t['bg2']};
            border-radius: 16px;
            padding: 1.5rem;
            margin: 0.8rem 0;
            border: 1px solid {t['border']};
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}
        .card-success {{ border-left: 4px solid {t['success']}; }}
        .card-error   {{ border-left: 4px solid {t['danger']}; }}
        .card-info    {{ border-left: 4px solid {t['primary']}; }}

        /* Diff Box */
        .diff-box {{
            background: {t['diff_bg']};
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            font-size: 1.15rem;
            line-height: 2.4;
            border: 1px solid {t['border']};
        }}
        .w-ok {{ color: {t['text']}; margin: 0 2px; }}
        .w-del {{
            background: {t['danger']}33; color: {t['danger']};
            padding: 2px 8px; border-radius: 6px;
            text-decoration: line-through;
            font-weight: 600; margin: 0 2px;
        }}
        .w-add {{
            background: {t['success']}33; color: {t['success']};
            padding: 2px 8px; border-radius: 6px;
            font-weight: 600; margin: 0 2px;
        }}
        .w-removed {{
            background: {t['warning']}33; color: {t['warning']};
            padding: 2px 8px; border-radius: 6px;
            text-decoration: line-through;
            font-weight: 600; margin: 0 2px;
        }}

        /* Corrected Text */
        .corrected-text {{
            color: {t['success']};
            font-size: 1.25rem;
            font-weight: 600;
            padding: 1rem 1.2rem;
            background: {t['success']}18;
            border-radius: 10px;
            border-left: 3px solid {t['success']};
            margin: 0.5rem 0;
        }}

        /* Gemini Box */
        .gemini-box {{
            background: {t['gemini_bg']};
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            border: 1px solid {t['border']};
            color: {t['text']};
            line-height: 1.9;
            font-size: 0.95rem;
        }}

        /* Change Arrow */
        .change-arrow {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0.8rem 1rem;
            background: {t['bg']};
            border-radius: 10px;
            margin-bottom: 0.8rem;
            border: 1px solid {t['border']};
        }}

        /* Ensemble Badge */
        .ensemble-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
        }}
        .badge-high {{
            background: {t['success']}22;
            color: {t['success']};
            border: 1px solid {t['success']}44;
        }}
        .badge-medium {{
            background: {t['warning']}22;
            color: {t['warning']};
            border: 1px solid {t['warning']}44;
        }}
        .model-tag {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.78rem;
            font-weight: 600;
            margin: 0 3px;
            background: {t['primary']}22;
            color: {t['primary']};
            border: 1px solid {t['primary']}44;
        }}

        /* Expander */
        .streamlit-expanderHeader,
        [data-testid="stExpander"] {{
            background: {t['bg2']} !important;
            border-radius: 10px !important;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: {t['bg']}; }}
        ::-webkit-scrollbar-thumb {{
            background: {t['border']}; border-radius: 3px;
        }}
    </style>
    """, unsafe_allow_html=True)

# ======================================
# Helper Functions
# ======================================

def call_api(text: str):
    """เรียก Backend API /check"""
    try:
        res = requests.post(
            f"{API_BASE_URL}/check",
            json={"text": text},
            timeout=60
        )
        if res.status_code == 200:
            return res.json()
        st.error(f"❌ API Error: {res.json().get('detail')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ ไม่สามารถเชื่อมต่อ Backend ได้\n\n"
            "รัน: `python main.py` ใน terminal ก่อน"
        )
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout — ลองใหม่อีกครั้ง")
        return None


def get_examples():
    """ดึงตัวอย่างประโยคจาก API"""
    try:
        res = requests.get(f"{API_BASE_URL}/examples", timeout=5)
        if res.status_code == 200:
            return res.json().get("examples", [])
    except:
        pass
    return [
        {"text": "She go to school yesterday",  "category": "Past Tense"},
        {"text": "He don't like pizza",          "category": "Subject-Verb Agreement"},
        {"text": "I am very boring in class",    "category": "Word Choice"},
        {"text": "They was playing football",    "category": "Tense"},
        {"text": "I have went to Paris",         "category": "Perfect Tense"},
        {"text": "She is more taller than me",   "category": "Comparative"},
        {"text": "He goed to the store",         "category": "Irregular Verb"},
        {"text": "I has a apple",                "category": "Article + Verb"},
    ]


def sanitize(text: str) -> str:
    """ป้องกัน HTML injection"""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# ✅ แก้ใหม่: สร้าง diff view จาก original + differences (position-based)
def render_diff(original: str, differences: list, t: dict) -> str:
    """
    สร้าง HTML diff highlight
    ใช้ original text + differences (position-based) จาก Backend ใหม่
    """
    words = original.split()
    diff_map = {}

    for d in differences:
        pos = d.get("position", -1)
        if pos >= 0:
            diff_map[pos] = d

    parts = []
    for i, word in enumerate(words):
        if i in diff_map:
            d = diff_map[i]
            orig = d.get("original", "")
            corr = d.get("corrected", "")

            if orig and corr:
                # เปลี่ยนคำ
                parts.append(
                    f'<span class="w-del">{sanitize(orig)}</span>'
                )
                parts.append(
                    f'<span class="w-add">{sanitize(corr)}</span>'
                )
            elif orig and not corr:
                # ลบคำ
                parts.append(
                    f'<span class="w-removed">{sanitize(orig)}</span>'
                )
            elif not orig and corr:
                # เพิ่มคำ
                parts.append(
                    f'<span class="w-ok">{sanitize(word)}</span>'
                )
                parts.append(
                    f'<span class="w-add">{sanitize(corr)}</span>'
                )
            else:
                parts.append(
                    f'<span class="w-ok">{sanitize(word)}</span>'
                )
        else:
            parts.append(
                f'<span class="w-ok">{sanitize(word)}</span>'
            )

    return f'<div class="diff-box">{" ".join(parts)}</div>'


def format_gemini(text: str, t: dict) -> str:
    """Format Gemini explanation (Markdown → HTML)"""
    text = re.sub(
        r'\*\*(.*?)\*\*',
        rf'<strong style="color:{t["success"]}">\1</strong>',
        text
    )
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    text = text.replace('\n', '<br>')
    return text


# ✅ แก้ใหม่: map error type → label + icon
def get_error_label(error_type: str) -> str:
    """แปลง error type จาก Backend → label ภาษาไทย"""
    label_map = {
        "spelling":       "📝 สะกดผิด",
        "verb_form":      "🔄 รูปกริยา",
        "grammar":        "🔧 ไวยากรณ์",
        "capitalization":  "🔠 ตัวพิมพ์ใหญ่-เล็ก",
        "contraction":    "✂️ คำย่อ",
        "article":        "📎 Article (a/an/the)",
        "missing_word":   "➕ เพิ่มคำ",
        "extra_word":     "🗑️ ลบคำ",
        # backward compatibility (เผื่อ Backend เดิม)
        "replaced":       "🔄 เปลี่ยนคำ",
        "deleted":        "🗑️ ลบคำ",
        "inserted":       "➕ เพิ่มคำ",
    }
    return label_map.get(error_type, "🔧 แก้ไข")


# ✅ แก้ใหม่: แสดง ensemble info
def render_ensemble_info(result: dict, t: dict):
    """แสดงข้อมูล Ensemble (Gramformer + HappyTransformer)"""
    ensemble = result.get("ensemble", {})
    models_used = result.get("models_used", [])

    if not ensemble:
        return

    source = ensemble.get("source", "unknown")
    confidence = ensemble.get("confidence", "medium")
    gram_result = ensemble.get("gramformer_result", "")
    happy_result = ensemble.get("happy_result", "")

    # Confidence badge
    badge_class = "badge-high" if confidence == "high" else "badge-medium"
    confidence_text = (
        "🟢 ความมั่นใจสูง" if confidence == "high"
        else "🟡 ความมั่นใจปานกลาง"
    )

    # Source description
    source_map = {
        "both_agree":         "ทั้ง 2 models เห็นตรงกัน ✅",
        "gramformer_primary": "ใช้ Gramformer เป็นหลัก",
        "gramformer_only":    "เฉพาะ Gramformer แก้ไข",
        "happy_only":         "เฉพาะ HappyTransformer แก้ไข",
        "no_change":          "ไม่มี model ไหนแก้ไข",
    }
    source_text = source_map.get(source, source)

    # Models used tags
    model_tags = ""
    for m in models_used:
        model_tags += f'<span class="model-tag">{m}</span>'

    st.markdown(
        f"""
        <div class="card card-info">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                flex-wrap:wrap;
                gap:8px;
            ">
                <div>
                    <span style="color:{t['text']};font-weight:600">
                        🤖 AI Models
                    </span>
                    <span style="margin-left:8px">{model_tags}</span>
                </div>
                <span class="ensemble-badge {badge_class}">
                    {confidence_text}
                </span>
            </div>
            <p style="
                color:{t['text_muted']};
                font-size:0.85rem;
                margin:0.5rem 0 0;
            ">
                📊 {source_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Expander: ดูผลแต่ละ model
    with st.expander("🔍 ดูผลจากแต่ละ Model", expanded=False):
        col_g, col_h = st.columns(2)
        with col_g:
            gram_changed = (
                gram_result.lower().strip()
                != result["original"].lower().strip()
            )
            icon = "🔧" if gram_changed else "✅"
            st.markdown(
                f"""
                <div style="
                    background:{t['bg']};
                    border:1px solid {t['border']};
                    border-radius:10px;
                    padding:0.8rem;
                ">
                    <p style="
                        color:{t['primary']};
                        font-weight:600;
                        margin:0 0 0.3rem;
                        font-size:0.9rem;
                    ">
                        {icon} Gramformer
                    </p>
                    <p style="
                        color:{t['text']};
                        margin:0;
                        font-style:italic;
                        font-size:0.95rem;
                    ">
                        "{sanitize(gram_result)}"
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_h:
            happy_changed = (
                happy_result.lower().strip()
                != result["original"].lower().strip()
            )
            icon = "🔧" if happy_changed else "✅"
            st.markdown(
                f"""
                <div style="
                    background:{t['bg']};
                    border:1px solid {t['border']};
                    border-radius:10px;
                    padding:0.8rem;
                ">
                    <p style="
                        color:{t['primary']};
                        font-weight:600;
                        margin:0 0 0.3rem;
                        font-size:0.9rem;
                    ">
                        {icon} HappyTransformer
                    </p>
                    <p style="
                        color:{t['text']};
                        margin:0;
                        font-style:italic;
                        font-size:0.95rem;
                    ">
                        "{sanitize(happy_result)}"
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )


# ======================================
# Show Result
# ======================================

def show_result(result: dict, t: dict):
    st.markdown(
        f'<hr style="border-color:{t["border"]}">',
        unsafe_allow_html=True
    )

    # ✅ ถูกต้อง
    if result["is_correct"]:
        st.markdown(
            f"""
            <div style="
                background: {t['success']}15;
                border: 2px solid {t['success']};
                border-radius: 20px;
                padding: 2.5rem;
                text-align: center;
                margin: 1.5rem 0;
            ">
                <div style="font-size:3.5rem;margin-bottom:0.5rem">
                    🎉
                </div>
                <h2 style="
                    color:{t['success']};margin:0 0 0.5rem 0;
                    font-size:1.8rem;
                ">
                    ไม่มีจุดที่ผิดพลาด!
                </h2>
                <p style="color:{t['text_muted']};margin:0 0 1rem 0;">
                    ประโยคของคุณถูกต้องสมบูรณ์แล้ว ✅
                </p>
                <div style="
                    display:inline-block;
                    background:{t['bg2']};
                    border:1px solid {t['border']};
                    border-radius:12px;
                    padding:0.8rem 1.5rem;
                    color:{t['text']};
                    font-size:1.1rem;
                    font-style:italic;
                ">
                    "{sanitize(result['original'])}"
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ✅ แสดง ensemble info แม้ถูกต้อง
        if "ensemble" in result:
            render_ensemble_info(result, t)

        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            if st.button(
                "🔄 ตรวจประโยคใหม่",
                use_container_width=True,
                key="btn_new_correct"
            ):
                st.session_state.input_text = ""
                st.session_state.last_result = None
                st.rerun()

    # ❌ ผิด
    else:
        changes = len(result.get("differences", []))

        st.markdown(
            f'<h2 style="color:{t["text"]}">ผลการตรวจ</h2>',
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class="card card-error">
                <h3 style="color:{t['danger']};margin:0">
                    🔧 พบ {changes} จุดที่ต้องแก้ไข
                </h3>
                <p style="color:{t['text_muted']};margin:0.5rem 0 0">
                    ดูคำอธิบายด้านล่าง ✨
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f'<p style="color:{t["text_muted"]};font-size:0.85rem">'
            f'⚡ ใช้เวลา {result.get("processing_time", "?")} วินาที</p>',
            unsafe_allow_html=True
        )

        # ✅ แสดง Ensemble Info
        if "ensemble" in result:
            render_ensemble_info(result, t)

        # Corrected Sentence
        st.markdown(
            f'<h3 style="color:{t["text"]}">✨ ประโยคที่ถูกต้อง</h3>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="corrected-text">'
            f'"{sanitize(result["corrected"])}"</div>',
            unsafe_allow_html=True
        )
        st.code(result["corrected"], language=None)

        # ✅ Diff (แก้ใหม่: ใช้ position-based)
        st.markdown(
            f'<h3 style="color:{t["text"]}">'
            f'🔍 Highlight การเปลี่ยนแปลง</h3>',
            unsafe_allow_html=True
        )
        st.markdown(
            render_diff(
                result["original"],
                result.get("differences", []),
                t
            ),
            unsafe_allow_html=True
        )

        # ✅ Explanations (แก้ใหม่: ใช้ error type ใหม่)
        explanations = result.get("explanations", [])
        if explanations:
            st.markdown(
                f'<h3 style="color:{t["text"]}">✨ คำอธิบาย</h3>',
                unsafe_allow_html=True
            )
            for exp in explanations:
                error_type = exp.get("type", "grammar")
                label = get_error_label(error_type)

                orig_display = (
                    sanitize(exp.get('original', '')) or '(none)'
                )
                corr_display = (
                    sanitize(exp.get('corrected', '')) or '(removed)'
                )

                with st.expander(
                    f"{label} : "
                    f"'{exp.get('original') or '(none)'}'"
                    f" → '{exp.get('corrected') or '(removed)'}'",
                    expanded=True
                ):
                    st.markdown(
                        f"""
                        <div class="change-arrow">
                            <span style="
                                color:{t['danger']};
                                text-decoration:line-through;
                                font-weight:600;
                                font-size:1.1rem;
                            ">
                                {orig_display}
                            </span>
                            <span style="
                                color:{t['primary']};
                                font-size:1.5rem;
                            "> → </span>
                            <span style="
                                color:{t['success']};
                                font-weight:600;
                                font-size:1.1rem;
                            ">
                                {corr_display}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    formatted = format_gemini(
                        exp.get("explanation", ""), t
                    )
                    st.markdown(
                        f'<div class="gemini-box">{formatted}</div>',
                        unsafe_allow_html=True
                    )

        # Before & After
        st.markdown(
            f'<h3 style="color:{t["text"]}">📋 Before & After</h3>',
            unsafe_allow_html=True
        )
        ca, cb = st.columns(2)
        with ca:
            st.markdown(
                f'<div style="text-align:center;color:{t["danger"]};'
                f'font-weight:600;margin-bottom:0.5rem">'
                f'❌ Original</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f"""
                <div style="
                    background:{t['danger']}18;
                    border:1px solid {t['danger']}44;
                    border-radius:12px;padding:1rem;
                    color:{t['text']};font-size:1.05rem;
                    line-height:1.7;min-height:70px;
                ">
                    "{sanitize(result['original'])}"
                </div>
                """,
                unsafe_allow_html=True
            )
        with cb:
            st.markdown(
                f'<div style="text-align:center;color:{t["success"]};'
                f'font-weight:600;margin-bottom:0.5rem">'
                f'✅ Corrected</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f"""
                <div style="
                    background:{t['success']}18;
                    border:1px solid {t['success']}44;
                    border-radius:12px;padding:1rem;
                    color:{t['text']};font-size:1.05rem;
                    line-height:1.7;min-height:70px;
                ">
                    "{sanitize(result['corrected'])}"
                </div>
                """,
                unsafe_allow_html=True
            )

        # Action Buttons
        st.markdown(
            f'<hr style="border-color:{t["border"]}">',
            unsafe_allow_html=True
        )
        r1, r2, r3 = st.columns(3)
        with r1:
            if st.button(
                "🔄 ตรวจใหม่",
                use_container_width=True,
                key="btn_new"
            ):
                st.session_state.input_text = ""
                st.session_state.last_result = None
                st.rerun()
        with r2:
            if st.button(
                "📋 ใช้ประโยคที่แก้แล้ว",
                use_container_width=True,
                key="btn_use"
            ):
                st.session_state.input_text = result["corrected"]
                st.session_state.last_result = None
                st.rerun()
        with r3:
            if st.button(
                "💡 ลองตัวอย่างอื่น",
                use_container_width=True,
                key="btn_example"
            ):
                st.session_state.input_text = random.choice(
                    st.session_state.get("examples", get_examples())
                )["text"]
                st.session_state.last_result = None
                st.rerun()


# ======================================
# Main App
# ======================================

t = get_theme()
inject_css(t)

# ======================================
# Sidebar
# ======================================

with st.sidebar:
    st.markdown(
        '<h2 class="main-title">✏️ Emily Grammar Checker</h2>',
        unsafe_allow_html=True
    )

    # Theme Toggle
    st.markdown(
        f'<h3 style="color:{t["text"]}">Theme</h3>',
        unsafe_allow_html=True
    )
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button(
            "🌙 Dark", use_container_width=True, key="btn_dark"
        ):
            st.session_state.dark_mode = True
            st.rerun()
    with col_t2:
        if st.button(
            "☀️ Light", use_container_width=True, key="btn_light"
        ):
            st.session_state.dark_mode = False
            st.rerun()

    st.markdown(
        f'<hr style="border-color:{t["border"]}">',
        unsafe_allow_html=True
    )

    # History
    st.markdown(
        f'<h3 style="color:{t["text"]}">📝 History</h3>',
        unsafe_allow_html=True
    )
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            icon = "✅" if item["is_correct"] else "🔧"
            label = (
                item["original"][:26] + "..."
                if len(item["original"]) > 26
                else item["original"]
            )
            with st.expander(f"{icon} {label}"):
                if not item["is_correct"]:
                    st.markdown(
                        f'<p style="color:{t["success"]};'
                        f'font-style:italic">'
                        f'✏️ {item["corrected"]}</p>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<p style="color:{t["success"]}">'
                        f'✅ ถูกต้องแล้ว</p>',
                        unsafe_allow_html=True
                    )

        if st.button(
            "🗑️ Clear History",
            use_container_width=True,
            key="btn_clear_history"
        ):
            st.session_state.history = []
            st.rerun()
    else:
        st.markdown(
            f'<p style="color:{t["text_muted"]};font-size:0.9rem">'
            f'ยังไม่มี history</p>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<hr style="border-color:{t["border"]}">',
        unsafe_allow_html=True
    )

    # Color Guide
    st.markdown(
        f'<h3 style="color:{t["text"]}">🎨 Color Guide</h3>',
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div style="font-size:0.9rem;line-height:2.5;color:{t['text']}">
            <span style="color:{t['danger']}">■</span> คำที่ผิด<br>
            <span style="color:{t['success']}">■</span> คำที่แก้แล้ว<br>
            <span style="color:{t['warning']}">■</span> คำที่ถูกลบ<br>
            <span style="color:{t['text']}">■</span> คำที่ถูกต้อง
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f'<hr style="border-color:{t["border"]}">',
        unsafe_allow_html=True
    )

    # ✅ อัปเดต footer
    st.markdown(
        f'<p style="color:{t["text_muted"]};font-size:0.8rem;'
        f'text-align:center">'
        f'Powered by Gramformer, HappyTransformer & Gemini</p>',
        unsafe_allow_html=True
    )

# ======================================
# Main Content
# ======================================

st.markdown(
    '<h1 class="main-title">✏️ Emily Grammar Checker AI</h1>',
    unsafe_allow_html=True
)
st.markdown(
    f'<p class="sub-title">'
    f'✨ Emily พร้อมช่วยคุณ'
    f'</p>',
    unsafe_allow_html=True
)
st.markdown(
    f'<p style="color:{t["text"]};font-weight:600;font-size:1.05rem">'
    f'📝  พิมพ์ประโยคภาษาอังกฤษ</p>',
    unsafe_allow_html=True
)

# ✅ เซฟ examples ไว้ใน session_state
if "examples" not in st.session_state:
    st.session_state.examples = get_examples()
examples = st.session_state.examples

input_text = st.text_area(
    label="input",
    value=st.session_state.input_text,
    height=130,
    placeholder='เช่น "She go to school yesterday"',
    label_visibility="collapsed"
)

char_count = len(input_text)
char_color = (
    t["danger"] if char_count > 450
    else t["primary"] if char_count > 0
    else t["text_muted"]
)
st.markdown(
    f'<p style="text-align:right;color:{char_color};font-size:0.82rem">'
    f'{char_count}/500</p>',
    unsafe_allow_html=True
)

b1, b2, b3 = st.columns([3, 1, 1])
with b1:
    check_btn = st.button(
        "🔍 Check Grammar",
        use_container_width=True,
        key="btn_check"
    )
with b2:
    if st.button(
        "🗑️ Clear", use_container_width=True, key="btn_clear"
    ):
        st.session_state.input_text = ""
        st.session_state.last_result = None
        st.rerun()
with b3:
    if st.button(
        "🔀 Random", use_container_width=True, key="btn_random"
    ):
        st.session_state.input_text = random.choice(examples)["text"]
        st.session_state.last_result = None
        st.rerun()

# ======================================
# Check Button Logic
# ======================================

if check_btn and input_text.strip():
    with st.spinner("กำลังตรวจน้าาา..."):
        result = call_api(input_text.strip())
    if result:
        st.session_state.last_result = result
        st.session_state.history.append({
            "original":   result["original"],
            "corrected":  result["corrected"],
            "is_correct": result["is_correct"]
        })
elif check_btn and not input_text.strip():
    st.warning("⚠️ กรุณาพิมพ์ประโยคก่อนกด Check!")

# ======================================
# แสดงผล (จาก session_state)
# ======================================

if st.session_state.last_result:
    show_result(st.session_state.last_result, t)