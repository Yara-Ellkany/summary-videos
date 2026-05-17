import streamlit as st
from groq import Groq
import tempfile, os, subprocess

st.title("Summarize")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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

def transcribe_audio_file(path):
    """استخراج النص من ملف صوتي باستخدام Whisper"""
    ext = os.path.splitext(path)[-1].lower()
    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(os.path.basename(path), f),
            response_format="text"
        )
    return transcript

def download_youtube_audio(url):
    """
    تحميل الصوت من يوتيوب باستخدام yt-dlp
    يُرجع مسار ملف الصوت المؤقت
    """
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, "audio.%(ext)s")

    result = subprocess.run(
        [
            "yt-dlp",
            "--no-playlist",
            "-x",                          # استخراج الصوت فقط
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_path,
            url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp error:\n{result.stderr}")

    # إيجاد الملف الذي تم تحميله
    for f in os.listdir(tmp_dir):
        if f.startswith("audio"):
            return os.path.join(tmp_dir, f)

    raise FileNotFoundError("لم يتم إيجاد ملف الصوت بعد التحميل")


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
    st.markdown(" رفع ملف فيديو أو صوت")
    uploaded = st.file_uploader(
        "ارفع فيديو أو ملف صوتي",
        type=["mp4", "mp3", "wav", "m4a", "ogg", "webm"]
    )

    if uploaded:
        if uploaded.size / 1024**2 > 25:
            st.error("الملف أكبر من 25 MB!")
        elif st.button("استخرج النص ولخّصه!", key="file_btn"):
            with st.spinner("جاري استخراج النص..."):
                ext = os.path.splitext(uploaded.name)[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(uploaded.read())
                    path = tmp.name
                try:
                    transcript = transcribe_audio_file(path)
                finally:
                    os.unlink(path)

            if not transcript or len(transcript.strip()) < 5:
                st.error("لم يتم استخراج أي نص من الملف!")
            else:
                with st.expander(" النص المستخرج"):
                    st.write(transcript)
                with st.spinner("جاري التلخيص..."):
                    st.success(summarize(transcript))

    st.markdown("---")
    st.markdown(" رابط يوتيوب")
    st.caption("ادخل رابط فيديو يوتيوب وسيتم استخراج النص منه تلقائياً")

    yt_url = st.text_input(" رابط يوتيوب", placeholder="https://www.youtube.com/watch?v=...")

    if yt_url:
        if st.button("استخرج النص من يوتيوب ولخّصه!", key="yt_btn"):
            # التحقق من أن الرابط يبدو صحيحاً
            if "youtube.com" not in yt_url and "youtu.be" not in yt_url:
                st.error("الرابط لا يبدو صحيحاً! تأكد أنه رابط يوتيوب.")
            else:
                audio_path = None
                try:
                    with st.spinner("جاري تحميل الصوت من يوتيوب... "):
                        audio_path = download_youtube_audio(yt_url)

                    with st.spinner("جاري استخراج النص بـ Whisper..."):
                        transcript = transcribe_audio_file(audio_path)

                    if not transcript or len(transcript.strip()) < 5:
                        st.error("لم يتم استخراج أي نص من الفيديو!")
                    else:
                        with st.expander("📄 النص المستخرج"):
                            st.write(transcript)
                        with st.spinner("جاري التلخيص..."):
                            st.success(summarize(transcript))

                except RuntimeError as e:
                    st.error(f"فشل تحميل الفيديو: {e}")
                except Exception as e:
                    st.error(f"حدث خطأ غير متوقع: {e}")
                finally:
                    if audio_path and os.path.exists(audio_path):
                        os.unlink(audio_path)

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
