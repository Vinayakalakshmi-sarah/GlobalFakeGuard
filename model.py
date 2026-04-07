from transformers import pipeline
import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt

@st.cache_resource
def load_model():
    return pipeline(
        "zero-shot-classification",
        model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device=-1
    )

classifier = load_model()

def predict(text):
    labels = ["fake news", "real news"]

    result = classifier(
        text,
        candidate_labels=labels,
        multi_label=False
    )

    fake_score = result["scores"][result["labels"].index("fake news")]
    real_score = result["scores"][result["labels"].index("real news")]

    # 🔥 Strong decision logic
    if fake_score > 0.60 and fake_score > real_score:
        return "FAKE ❌", round(fake_score * 100, 2)

    elif real_score > 0.60 and real_score > fake_score:
        return "REAL ✅", round(real_score * 100, 2)

    else:
        return "UNCERTAIN ⚠️", round(max(fake_score, real_score) * 100, 2)
def generate_wordcloud(text):
    wc = WordCloud(width=800, height=400, background_color='black').generate(text)
    fig, ax = plt.subplots()
    ax.imshow(wc)
    ax.axis("off")
    return fig