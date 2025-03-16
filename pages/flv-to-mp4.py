import streamlit as st
import subprocess
import os
import json
from pathlib import Path
import tempfile

# ==================== 核心转换类 ====================
class VideoConverter:
    def __init__(self, config):
        self.config = config
        self.system_encoding = 'gbk' if os.name == 'nt' else 'utf-8'
        self.force_encoding = 'utf-8'
        
    def safe_path(self, path):
        """处理特殊字符路径"""
        return path.encode('utf-8', errors='surrogateescape').decode('utf-8')

    def get_media_info(self, input_path):
        """使用ffprobe获取媒体信息"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, check=True)
        return json.loads(result.stdout)

    def build_command(self, input_path, output_path):
        """构建FFmpeg命令"""
        media_info = self.get_media_info(input_path)
        
        if self.config['pr_compat_mode']:
            return self._build_pr_command(input_path, output_path, media_info)
        else:
            return self._build_fast_command(input_path, output_path)

    def _build_pr_command(self, input_path, output_path, media_info):
        cmd = [
            "ffmpeg",
            "-y",
            "-hwaccel", "auto",
            "-i", input_path
        ]

        # 视频处理
        video_stream = next(s for s in media_info['streams'] if s['codec_type'] == 'video')
        if video_stream['codec_name'] != 'h264':
            cmd += [
                "-c:v", "libx264",
                "-preset", self.config.get('preset', 'medium'),
                "-profile:v", "high",
                "-level", "4.2",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-g", "60",
                "-x264-params", "nal-hrd=cbr"
            ]
        else:
            cmd += ["-c:v", "copy"]

        # 音频处理
        audio_stream = next(s for s in media_info['streams'] if s['codec_type'] == 'audio')
        if audio_stream['codec_name'] != 'aac' or self.config.get('force_audio'):
            cmd += [
                "-c:a", "aac",
                "-b:a", self.config.get('audio_bitrate', '192k')
            ]
        else:
            cmd += ["-c:a", "copy"]

        cmd += [
            "-map", "0:v",
            "-map", "0:a",
            "-max_muxing_queue_size", "9999",
            output_path
        ]
        return cmd

    def _build_fast_command(self, input_path, output_path):
        return [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]

    def convert(self):
        """执行转换主逻辑"""
        input_path = self.safe_path(self.config['input_path'])
        output_path = self.safe_path(self.config['output_path'])
        
        cmd = self.build_command(input_path, output_path)
        
        with st.status("转换进行中...", expanded=True) as status:
            st.write(f"**执行的命令:** `{' '.join(cmd)}`")
            progress_bar = st.progress(0)
            log_container = st.empty()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=False
            )
            
            full_log = ""
            while True:
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                if output:
                    try:
                        decoded = output.decode(self.force_encoding)
                    except UnicodeDecodeError:
                        decoded = output.decode(self.system_encoding, errors='replace')
                    
                    full_log += decoded
                    log_container.code(full_log[-2000:], language='bash')  # 显示最后2000字符
                    progress_bar.progress(min(process.poll() or 0, 100)/100)
            
            if process.returncode == 0:
                status.update(label="转换成功!", state="complete")
                st.success("文件转换成功完成！")
                self._verify_output(output_path)
                return output_path
            else:
                status.update(label="转换失败", state="error")
                st.error(f"转换失败，错误代码: {process.returncode}")
                st.code(full_log[-2000:], language='bash')
                return None

    def _verify_output(self, output_path):
        """验证输出文件"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,profile,pix_fmt",
            "-of", "json",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            info = json.loads(result.stdout)
            video_info = info['streams'][0]
            
            verification = {
                'codec_name': video_info['codec_name'] == 'h264',
                'profile': video_info['profile'] in ['High', 'Main', 'Baseline'],
                'pix_fmt': video_info['pix_fmt'] == 'yuv420p'
            }
            
            if all(verification.values()):
                st.success("PR兼容性验证通过")
            else:
                warning = [
                    "可能存在兼容性问题:",
                    f"- 编码格式: {video_info['codec_name']} (要求H.264)",
                    f"- 配置: {video_info['profile']} (要求High/Main/Baseline)",
                    f"- 像素格式: {video_info['pix_fmt']} (要求yuv420p)"
                ]
                st.warning('\n'.join(warning))
        except Exception as e:
            st.error(f"验证失败: {str(e)}")

# ==================== Streamlit界面 ====================
def main():
    st.title("专业视频转换器")
    
    # 配置参数
    config = {
        'pr_compat_mode': st.sidebar.checkbox("启用PR兼容模式", True),
        'audio_bitrate': st.sidebar.selectbox("音频比特率", ['192k', '256k', '320k'], index=2),
        'preset': st.sidebar.selectbox("编码预设", ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium'], index=5)
    }
    
    # 文件上传
    uploaded_file = st.file_uploader("选择视频文件", type=['mp4', 'mov', 'mkv', 'flv'])
    if not uploaded_file:
        st.stop()
    
    # 生成临时文件路径
    with tempfile.NamedTemporaryFile(delete=False) as tmp_input:
        tmp_input.write(uploaded_file.getvalue())
        config['input_path'] = tmp_input.name
    
    # 自动生成输出路径
    output_ext = "_PR.mp4" if config['pr_compat_mode'] else ".mp4"
    config['output_path'] = Path(config['input_path']).with_suffix(output_ext).name
    
    # 显示配置摘要
    with st.expander("当前配置"):
        st.json({
            "输入文件": config['input_path'],
            "输出文件": config['output_path'],
            "PR兼容模式": config['pr_compat_mode'],
            "音频比特率": config['audio_bitrate'],
            "编码预设": config['preset']
        })
    
    # 开始转换
    if st.button("开始转换"):
        converter = VideoConverter(config)
        output_path = converter.convert()
        
        if output_path:
            with open(output_path, "rb") as f:
                st.download_button(
                    label="下载转换后的文件",
                    data=f,
                    file_name=Path(output_path).name,
                    mime="video/mp4"
                )
            # 清理临时文件
            os.unlink(config['input_path'])
            os.unlink(output_path)

if __name__ == "__main__":
    main()