import streamlit as st
from groq import Groq
import tempfile, os, subprocess, json, re
 
st.title("استخراج النص")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
 
def transcribe_audio_file(path):
    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(os.path.basename(path), f),
            response_format="text"
        )
    return transcript
 
def parse_json3_subtitles(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    lines = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            word = seg.get("utf8", "").strip()
            if word and word != "\n":
                lines.append(word)
    full_text = " ".join(lines)
    return re.sub(r'\s+', ' ', full_text).strip()
 
def get_youtube_transcript(url):
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, "subs")
 
    for lang in ["ar", "en", ""]:
        cmd = [
            "yt-dlp", "--no-playlist", "--skip-download",
            "--write-subs", "--write-auto-subs",
            "--sub-format", "json3",
            "-o", output_path,
        ]
        if lang:
            cmd += ["--sub-langs", lang]
        cmd.append(url)
 
        subprocess.run(cmd, capture_output=True, text=True)
 
        for f in os.listdir(tmp_dir):
            if f.endswith(".json3"):
                sub_path = os.path.join(tmp_dir, f)
                text = parse_json3_subtitles(sub_path)
                for file in os.listdir(tmp_dir):
                    try:
                        os.unlink(os.path.join(tmp_dir, file))
                    except:
                        pass
                if text.strip():
                    return text
 
    raise ValueError("لا توجد ترجمة (Captions) متاحة لهذا الفيديو.\nجرّب فيديو آخر أو تأكد أن الفيديو يحتوي على ترجمة.")
 
 
# ── رفع ملف ──
st.markdown("###  رفع ملف فيديو أو صوت")
uploaded = st.file_uploader("ارفع فيديو أو ملف صوتي", type=["mp4", "mp3", "wav", "m4a", "ogg", "webm"])
 
if uploaded:
    if uploaded.size / 1024**2 > 25:
        st.error("الملف أكبر من 25 MB!")
    elif st.button("استخرج النص!", key="file_btn"):
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
            st.subheader(" النص المستخرج")
            st.write(transcript)
            st.download_button(" تحميل النص", transcript, file_name="transcript.txt")
 
st.markdown("---")
 
# ── رابط يوتيوب ──
st.markdown("###  رابط يوتيوب")
st.caption("يستخرج النص مباشرة من الترجمة الموجودة في الفيديو — بدون تحميل الصوت")
 
yt_url = st.text_input(" رابط يوتيوب", placeholder="https://www.youtube.com/watch?v=...")
 
if yt_url:
    if st.button("استخرج النص!", key="yt_btn"):
        if "youtube.com" not in yt_url and "youtu.be" not in yt_url:
            st.error("الرابط لا يبدو صحيحاً! تأكد أنه رابط يوتيوب.")
        else:
            try:
                with st.spinner("جاري استخراج النص من الترجمة... "):
                    transcript = get_youtube_transcript(yt_url)
                st.subheader(" النص المستخرج")
                st.write(transcript)
                st.download_button(" تحميل النص", transcript, file_name="transcript.txt")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
