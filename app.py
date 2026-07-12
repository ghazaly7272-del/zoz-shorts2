import streamlit as st
import tempfile, os
from pathlib import Path
from processing import download_video, process_video

st.set_page_config(page_title="ZOZ.Shorts", page_icon="🎬", layout="centered")

# --- Header ---
st.markdown("""
<div style="text-align:center;padding:20px 0 10px">
  <h1 style="font-size:2.5rem;margin:0">🎬 ZOZ.Shorts</h1>
  <p style="color:#888;font-size:1rem">Turn long videos into viral-ready short clips</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Input ---
tab_link, tab_upload = st.tabs(["🔗 Paste Link", "📁 Upload File"])

with tab_link:
    url = st.text_input("Video URL (YouTube, Twitter, etc.)",
                        placeholder="https://youtube.com/watch?v=...")
    go_url = st.button("🚀 Get Clips", key="btn_url", use_container_width=True)

with tab_upload:
    uploaded = st.file_uploader("Upload a video file", type=["mp4","mov","avi","mkv","webm"])
    go_file = st.button("🚀 Get Clips", key="btn_file", use_container_width=True)

# --- Processing ---
def run_pipeline(source_path, work_dir):
    with st.status("Processing your video...", expanded=True) as status:
        st.write("🔍 Analyzing audio energy...")
        clips = process_video(source_path, work_dir)
        status.update(label="Done! Your clips are ready.", state="complete")
    return clips

def show_clips(clips):
    st.divider()
    st.subheader(f"🎬 {len(clips)} Clips Generated")
    cols = st.columns(min(len(clips), 3))
    for i, clip in enumerate(clips):
        with cols[i % 3]:
            st.video(clip["path"])
            st.markdown(f"**{clip['title']}** · {clip['duration']}")
            st.progress(clip["score"], text=f"Virality: {clip['score']}%")
            with open(clip["path"], "rb") as f:
                st.download_button(
                    f"⬇️ Download {clip['title']}",
                    f.read(),
                    file_name=f"{clip['title']}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

# Handle URL
if go_url and url:
    work_dir = tempfile.mkdtemp()
    try:
        with st.spinner("Downloading video..."):
            source = download_video(url, work_dir)
        clips = run_pipeline(source, work_dir)
        show_clips(clips)
    except Exception as e:
        st.error(f"Error: {e}")

# Handle Upload
if go_file and uploaded:
    work_dir = tempfile.mkdtemp()
    source = os.path.join(work_dir, uploaded.name)
    with open(source, "wb") as f:
        f.write(uploaded.read())
    try:
        clips = run_pipeline(source, work_dir)
        show_clips(clips)
    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center;color:#666;font-size:0.8rem'>ZOZ.Shorts MVP · Powered by FFmpeg + yt-dlp</p>", unsafe_allow_html=True)
