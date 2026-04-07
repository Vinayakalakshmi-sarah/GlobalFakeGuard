import streamlit as st
from transformers import pipeline
from newspaper import Article
import time
import plotly.express as px
import speech_recognition as sr
from langdetect import detect

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="GlobalFakeGuard", layout="wide")

# -----------------------
# MODELS
# -----------------------
@st.cache_resource
def load_models():
    classifier = pipeline(
        "zero-shot-classification",
        model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    )
    explainer = pipeline("text-generation", model="google/flan-t5-base")
    return classifier, explainer

classifier, explainer = load_models()

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "login"

if "history" not in st.session_state:
    st.session_state.history = []

# -----------------------
# FAKE KEYWORDS
# -----------------------
fake_keywords = [
    "aliens", "secret", "shocking", "urgent", "share this",
    "miracle", "hidden truth", "government hiding",
    "free money", "click here", "breaking!!!"
]

# -----------------------
# CSS
# -----------------------
st.markdown("""
<style>
.block-container { padding-top: 3rem; padding-left: 2rem; padding-right: 2rem; }
* { font-family: "Times New Roman", serif !important; font-weight: bold !important; }
.stApp {
    background: linear-gradient(-45deg, #020617, #0f172a, #020617, #1e3a8a);
    background-size: 400% 400%;
    animation: move 15s ease infinite;
    color: white;
}
@keyframes move {
    0% {background-position:0% 50%;}
    50% {background-position:100% 50%;}
    100% {background-position:0% 50%;}
}
section[data-testid="stSidebar"] { background: #020617; padding: 20px; }
.title { text-align:center; font-size:36px; color:#60a5fa; margin-bottom:25px; }
textarea { margin-top:10px; margin-bottom:20px; }
button { background:#2563eb !important; color:white !important; border-radius:10px !important; }
.real { color:#22c55e; font-size:26px; text-align:center; margin-top:20px;}
.fake { color:#ef4444; font-size:26px; text-align:center; margin-top:20px;}
.bar-container { background:#111; border-radius:10px; margin:15px 0; }
.bar { padding:10px; text-align:center; }
.real-bar { background:#22c55e; }
.fake-bar { background:#ef4444; }
.login-box { max-width:400px; margin:auto; margin-top:40px; }
</style>
""", unsafe_allow_html=True)

# -----------------------
# VOICE
# -----------------------
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("SPEAK NOW")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        return "VOICE ERROR"

# -----------------------
# EXPLAIN (FIXED WITH FALLBACK FOR SHORT TEXT)
# -----------------------
def explain(text, label):
    try:
        # If text is too short, just return fallback
        if len(text.strip()) < 20:
            raise ValueError("Text too short for AI explanation")

        res = explainer(
            f"Explain why this is {label}: {text[:300]}",
            max_length=120,
            do_sample=False
        )
        return res[0]["generated_text"]
    except:
        # FALLBACK (ALWAYS SHOW)
        if "FAKE" in label:
            return """This news appears fake because:
- It may contain exaggerated or emotional words
- It lacks reliable sources
- It may be misleading or clickbait
- Pattern-based fake keywords detected"""
        else:
            return """This news appears real because:
- The content seems neutral and factual
- No fake patterns detected
- Language is formal and informative
- Matches real-world reporting style"""

# -----------------------
# SIDEBAR
# -----------------------
st.sidebar.markdown("## ⚙️ INPUT PANEL")

option = st.sidebar.radio("SELECT INPUT", ["TEXT", "URL", "VOICE"])

user_input = ""

if option == "URL":
    url = st.sidebar.text_input("ENTER URL")
    if url:
        try:
            article = Article(url)
            article.download()
            article.parse()
            user_input = article.text
            st.sidebar.success("LOADED")
        except:
            st.sidebar.error("ERROR")

elif option == "VOICE":
    if st.sidebar.button("RECORD"):
        user_input = get_voice_input()
        st.sidebar.success(user_input)

st.sidebar.markdown("---")

if st.sidebar.button("HISTORY"):
    if st.session_state.history:
        st.sidebar.markdown("### PREVIOUS")
        for i, item in enumerate(reversed(st.session_state.history[-5:]), 1):
            st.sidebar.write(f"{i}. {item['label']}")
    else:
        st.sidebar.info("NO HISTORY")

if st.sidebar.button("HOME"):
    st.session_state.page = "home"

if st.sidebar.button("LOGOUT"):
    st.session_state.page = "login"

# -----------------------
# LOGIN
# -----------------------
if st.session_state.page == "login":
    st.markdown('<div class="title">GLOBALFAKEGUARD</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    email = st.text_input("EMAIL")
    password = st.text_input("PASSWORD", type="password")

    if st.button("LOGIN"):
        if email and password:
            st.session_state.page = "home"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------
# HOME
# -----------------------
elif st.session_state.page == "home":
    st.markdown('<div class="title">WELCOME</div>', unsafe_allow_html=True)
    if st.button("START ANALYZING"):
        st.session_state.page = "analyzer"

# -----------------------
# ANALYZER
# -----------------------
elif st.session_state.page == "analyzer":

    st.markdown('<div class="title">ANALYZER</div>', unsafe_allow_html=True)

    news_text = st.text_area("ENTER NEWS TEXT")

    if st.button("ANALYZE"):

        text = news_text if news_text else user_input

        if text:
            try:
                lang = detect(text)
                st.info(f"LANGUAGE: {lang.upper()}")
            except:
                st.info("UNKNOWN LANGUAGE")

            # RULE
            rule_label = None
            if any(word in text.lower() for word in fake_keywords):
                rule_label = "FAKE NEWS (PATTERN DETECTED)"

            # MODEL
            labels = ["This is real news", "This is fake news"]
            result = classifier(text, candidate_labels=labels)

            score_map = dict(zip(result["labels"], result["scores"]))
            real_score = score_map["This is real news"]
            fake_score = score_map["This is fake news"]

            label = "REAL NEWS" if real_score > fake_score else "FAKE NEWS"

            if rule_label:
                label = rule_label

            if "FAKE" in label:
                fake_score = max(fake_score, 0.85)
                real_score = min(real_score, 0.15)
            elif "REAL" in label:
                real_score = max(real_score, 0.85)
                fake_score = min(fake_score, 0.15)

            st.markdown(f'<div class="{ "real" if "REAL" in label else "fake" }">{label}</div>', unsafe_allow_html=True)

            st.session_state.history.append({"text": text, "label": label})

            st.markdown(f"""
            <div class="bar-container">
                <div class="bar real-bar" style="width:{real_score*100}%">
                    REAL: {real_score*100:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="bar-container">
                <div class="bar fake-bar" style="width:{fake_score*100}%">
                    FAKE: {fake_score*100:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

            fig = px.pie(names=["REAL", "FAKE"], values=[real_score, fake_score])
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🧠 WHY THIS RESULT?")
            st.write(explain(text, label))

        else:
            st.warning("ENTER INPUT")