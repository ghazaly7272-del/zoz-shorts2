import streamlit as st
import tempfile, os
from pathlib import Path
from processing import download_video, process_video

st.set_page_config(page_title="ZOZ.Shorts", page_icon="🎬", layout="centered")

st.markdown("""
<div style="text-align:center;padding:20px 0 10px">
  <h1 style="font-size:2.5rem;margin:0">🎬 ZOZ.Shorts</h1>
  <p style="color:#888;font-size:1rem">Turn long videos into viral-ready short clips</p>
</div>
""", unsafe_allow_html=True)

st.divider()

tab_link, tab_upload = st.tabs(["🔗 Paste Link", "📁 Upload File"])

with tab_link:
    url = st.text_input("Video URL (YouTube, Twitter, etc.)",
                        placeholder="https://youtube.com/watch?v=...")
    go_url = st.button("🚀 Get Clips", key="btn_url", use_container_width=True)

with tab_upload:
    uploaded = st.file_uploader("Upload a video file", type=["mp4","mov","avi","mkv","webm"])
    go_file = st.button("🚀 Get Clips", key="btn_file", use_container_width=True)

def run_pipeline(source_path, work_dir):
    with st.status("Processing your video...", expanded=True) as status:
        st.write("🔍 Analyzing audio energy...")
        clips = process_video(source_path, work_dir)
        status.update(label="Done! Your clips are ready.", state="complete")
    return clips

def show_clips(clips):
    st.divider()
    st.subheader(f"🎬 {len(clips)} Clips Gene
