import streamlit as st
import subprocess
import platform
from pathlib import Path
import tempfile
import time

# 页面配置
st.set_page_config(
    page_title="MP3 Extract",
    page_icon="🎵",
    layout="centered",
)

# 自定义样式
st.markdown("""
<style>
.uploadedFile { padding: 20px; border-radius: 5px; background: #c0c9d9;  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.preview-area { margin-top: 1rem; }
.download-btn { background: #25d366 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

system = platform.system()

if system == "Windows":
    ffmpeg_path = "D:\\zc\\ZC\\My_New_bot\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe"  # Windows路径
elif system == "Darwin":
    ffmpeg_path = "/usr/local/bin/ffmpeg"         # macOS路径
else:
    ffmpeg_path = "/usr/bin/ffmpeg"               # Linux路径

def main():
    st.title("🎬 MP3 Extract")
    st.markdown("---")
    
    # 文件上传区域
    uploaded_file = st.file_uploader(
        "拖放或选择视频文件: ",
        type=["mp4", "avi", "mkv", "mov", "flv", "webm", "mpeg4"], 
        key="uploader",
        help="支持常见视频格式"
    )
    
    # 参数设置侧边栏
    with st.sidebar:
        st.header("⚙️ 转换参数")
        bitrate = st.select_slider(
            "音频比特率",
            options=["320k", "256k", "192k"],
            value="320k",
            help="更高的比特率意味着更好的音质和更大的文件大小"
        )
        st.markdown("---")
        st.info("""
        **Tips：**
        1. 上传视频文件
        2. 调整转换参数
        3. 开始转换
        4. 下载MP3
        """)

    if uploaded_file:
        # 文件预览区域
        with st.expander("🎥 视频预览", expanded=True):
            st.video(uploaded_file)
            file_info = f"""📄 文件名称: <span class="ellipsis" title="{uploaded_file.name}">{uploaded_file.name}</span><br/>
                        📏 文件大小: {uploaded_file.size/1024/1024:.2f} MB<br/>
                        🕒 上传时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
                        """
            st.markdown(f'<div class="uploadedFile">{file_info}</div>', unsafe_allow_html=True)
            st.markdown("---")

        # 转换按钮
        if st.button("🚀 开始转换", use_container_width=True):
            with st.spinner("⏳ 正在转换，请稍候..."):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    try:
                        # 保存上传文件
                        input_path = Path(tmp_dir) / uploaded_file.name
                        input_path.write_bytes(uploaded_file.getbuffer())

                        # 生成输出路径
                        output_path = input_path.with_suffix(".mp3")

                        # 构建FFmpeg命令
                        cmd = [
                            ffmpeg_path,
                            "-y", "-v", "error",
                            "-i", str(input_path),
                            "-vn",  # 忽略视频流
                            "-acodec", "libmp3lame",
                            "-b:a", bitrate,
                            "-q:a", "0",  # 最高质量
                            "-threads", "0",  # 自动线程
                            str(output_path)
                        ]

                        # 执行转换
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode != 0:
                            raise RuntimeError(result.stderr)

                        # 准备下载文件
                        mp3_data = output_path.read_bytes()
                        file_size = len(mp3_data) / 1024 / 1024

                        # 显示结果
                        st.success(f"✅ 转换完成！文件大小: {file_size:.2f} MB")
                        st.balloons()

                        # 下载按钮
                        st.download_button(
                            label="⬇️ 下载MP3文件",
                            data=mp3_data,
                            file_name=output_path.name,
                            mime="audio/mpeg",
                            use_container_width=True,
                            key="download-btn"
                        )

                    except Exception as e:
                        st.error(f"❌ 转换失败:  {str(e)}")
                        # st.write(system)

if __name__ == "__main__":
    main()