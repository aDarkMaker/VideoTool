import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import time

# 页面配置
st.set_page_config(
    page_title="Video Fixer",
    page_icon="🔧",
    layout="centered",
)

# 自定义样式
st.markdown("""
<style>
.uploadedFile { padding: 20px; border-radius: 5px; background: #c0c9d9; overflow: hidden; }
.error-box { padding: 15px; background: #fee2e2; border-radius: 5px; margin: 10px 0; }
.fix-btn { background: #4CAF50 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

ERROR_MAPPING = {
    "moov atom not found": {
        "description": "视频元数据损坏（moov原子缺失）",
        "solution": "使用快速启动模式重新封装视频"
    },
    "invalid data": {
        "description": "无效的视频数据",
        "solution": "尝试重新编码视频流"
    },
    "corrupt": {
        "description": "文件损坏",
        "solution": "尝试修复容器格式"
    }
}

def detect_errors(input_path):
    """使用ffmpeg检测视频错误"""
    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", str(input_path),
        "-f", "null",
        "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stderr.splitlines()

def fix_moov(input_path, output_path):
    """修复moov原子缺失问题"""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-c", "copy",
        "-movflags", "faststart",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

def main():
    st.title("Fix Videos ⚙️")
    st.markdown("---")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传损坏的视频文件",
        type=["mp4", "avi", "mkv", "mov", "flv", "webm", "mpeg4"], 
        help="支持常见视频格式"
    )
    
    # 参数设置侧边栏
    with st.sidebar:
        st.header("🪛​ 修复建议")
        st.markdown("  ")
        st.info("""
        **Tips：**
        1. 上传损坏文件
        2. 解析错误原因
        3. 尝试修复
        4. 修复完成
        """)
    
    # 初始化session状态
    if 'detected_errors' not in st.session_state:
        st.session_state.detected_errors = []
    
    if uploaded_file:
        # 文件信息展示
        with st.expander("📁 文件信息", expanded=True):
            file_info = f"""
            📄 文件名: {uploaded_file.name}<br>
            📏 大小: {uploaded_file.size/1024/1024:.2f} MB<br>
            🕒 上传时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
            """
            st.markdown(f'<div class="uploadedFile">{file_info}</div>', unsafe_allow_html=True)
            st.markdown("  ")
        
        # 检测按钮
        if st.button("🔍 开始检测", use_container_width=True):
            with st.spinner("正在分析视频文件..."):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    try:
                        # 保存临时文件
                        input_path = Path(tmp_dir) / uploaded_file.name
                        input_path.write_bytes(uploaded_file.getbuffer())
                        
                        # 执行检测
                        raw_errors = detect_errors(input_path)
                        processed_errors = []
                        
                        # 错误分类处理
                        for err in raw_errors:
                            for key in ERROR_MAPPING:
                                if key in err.lower():
                                    processed_errors.append({
                                        "error": err.strip(),
                                        "type": key,
                                        "info": ERROR_MAPPING[key]
                                    })
                                    break
                            else:
                                processed_errors.append({
                                    "error": err.strip(),
                                    "type": "unknown",
                                    "info": {"description": "未知错误", "solution": "建议重新录制或获取源文件"}
                                })
                        
                        st.session_state.detected_errors = processed_errors
                        
                    except Exception as e:
                        st.error(f"检测失败: {str(e)}")
        
        # 显示检测结果
        if st.session_state.detected_errors:
            st.markdown("---")
            st.subheader("📝 检测报告")
            
            for idx, error in enumerate(st.session_state.detected_errors, 1):
                with st.container():
                    st.markdown(f"""
                    <div class="error-box">
                        <b>错误 #{idx}</b><br>
                        🚨 类型: {error['info']['description']}<br>
                        📋 详情: {error['error']}<br>
                        💡 建议解决方案: {error['info']['solution']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 修复按钮
            if st.button("⚡ 一键修复", type="primary", use_container_width=True):
                with st.spinner("正在施展魔法修复..."):
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        try:
                            input_path = Path(tmp_dir) / uploaded_file.name
                            input_path.write_bytes(uploaded_file.getbuffer())
                            
                            output_path = input_path.with_name(f"fixed_{input_path.name}")
                            
                            # 根据错误类型执行修复
                            for error in st.session_state.detected_errors:
                                if error['type'] == "moov atom not found":
                                    fix_moov(input_path, output_path)
                                    break  # 暂时只处理moov错误
                            
                            # 验证修复结果
                            verify_errors = detect_errors(output_path)
                            if len(verify_errors) < len(st.session_state.detected_errors):
                                st.success("🎉 修复成功！")
                                st.balloons()
                                
                                # 生成下载按钮
                                fixed_data = output_path.read_bytes()
                                st.download_button(
                                    label="⬇️ 下载修复后的视频",
                                    data=fixed_data,
                                    file_name=output_path.name,
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                            else:
                                st.warning("⚠️ 部分问题未能完全修复")
                            
                        except Exception as e:
                            st.error(f"修复失败: {str(e)}")
                            
        else:
            st.info("🤔 未检测到错误，无需修复~")

if __name__ == "__main__":
    main()