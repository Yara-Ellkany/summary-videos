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
 
tab1, tab2, tab3 = st.tabs([" نص", " فيديو أو صوت", " ملف"])
 
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

with tab3:
    doc_file = st.file_uploader("ارفع ملفاً نصياً", type=["txt", "pdf", "docx"], key="doc_uploader")

    if doc_file:
        if doc_file.size / 1024**2 > 10:
            st.error("الملف أكبر من 10 MB!")
        elif st.button("استخرج النص ولخّصه!", key="doc_btn"):

            with st.spinner("جاري قراءة الملف..."):
                ext = os.path.splitext(doc_file.name)[-1].lower()

                if ext == ".txt":
                    extracted = doc_file.read().decode("utf-8", errors="ignore")

                elif ext == ".pdf":
                    import pypdf
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(doc_file.read())
                        path = tmp.name
                    reader = pypdf.PdfReader(path)
                    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
                    os.unlink(path)

                elif ext == ".docx":
                    import docx
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                        tmp.write(doc_file.read())
                        path = tmp.name
                    doc = docx.Document(path)
                    extracted = "\n".join(p.text for p in doc.paragraphs)
                    os.unlink(path)

            if not extracted or len(extracted.strip()) < 10:
                st.error("لم يتم العثور على نص في الملف!")
            else:
                with st.expander(" النص المستخرج"):
                    st.write(extracted)
                with st.spinner("جاري التلخيص..."):
                    st.success(summarize(extracted))
