import streamlit as st
from groq import Groq
import tempfile, os
 
st.title("Summarize")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
 
# ── كشف اللغة ──
def detect_language(text):
    arabic_letters = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return "العربية" if arabic_letters > 5 else "الإنجليزية"
 
def summarize(text):
    language = detect_language(text)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"You are a helpful assistant for kids. Summarize the text in 3-4 simple sentences. You MUST respond in {language} only."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content
 
tab1, tab2 = st.tabs([" نص", " فيديو أو صوت"])
 
with tab1:
    text = st.text_area("اكتب النص هنا...", height=200)
    if st.button("لخّص!"):
        if len(text.split()) < 10:
            st.warning("النص قصير جداً!")
        else:
            with st.spinner("جاري التلخيص..."):
                st.success(summarize(text))
 
with tab2:
    uploaded = st.file_uploader("ارفع فيديو أو ملف صوتي", type=["mp4","mp3","wav","m4a","ogg","webm"])
 
    if uploaded:
        if uploaded.size / 1024**2 > 25:
            st.error("الملف أكبر من 25 MB!")
        elif st.button("استخرج النص ولخّصه!"):
 
            # استخراج النص بـ Whisper
            with st.spinner("جاري استخراج النص..."):
                ext = os.path.splitext(uploaded.name)[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(uploaded.read())
                    path = tmp.name
                with open(path, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=(os.path.basename(path), f),
                        response_format="text"
                    )
                os.unlink(path)
 
            if not transcript or len(transcript.strip()) < 5:
                st.error("Error!")
            else:
                with st.expander(" النص المستخرج"):
                    st.write(transcript)
                with st.spinner("جاري التلخيص..."):
                    st.success(summarize(transcript))
