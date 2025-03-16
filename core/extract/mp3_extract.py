import subprocess
import os
from pathlib import Path

def main():
    # ==================== 用户配置区域 ====================
    # 输入文件路径（支持绝对路径或相对路径）
    input_video = "../testmp4.mp4"  # 替换为你的MP4文件路径
    
    # 输出文件路径（可选设置）
    # output_audio = "../testmp3.mp3"  # 指定完整路径
    # 或自动生成路径（与输入文件同目录）
    output_audio = Path(input_video).with_suffix('.mp3')  
    
    audio_bitrate = '320k'  # 可选：192k, 256k, 320k
    # ==================== 配置结束 ====================

    # 输入文件验证
    if not os.path.isfile(input_video):
        print(f"错误：输入文件不存在 - {input_video}")
        return

    # 自动创建输出目录（如果不存在）
    output_dir = os.path.dirname(output_audio)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"已自动创建输出目录：{output_dir}")

    # FFmpeg转换命令
    command = [
        'ffmpeg',
        '-y',                     # 覆盖已存在文件
        '-i', input_video,
        '-vn',                    # 忽略视频流
        '-acodec', 'libmp3lame',  # 使用LAME编码器
        '-b:a', audio_bitrate,    # 设置比特率
        '-q:a', '0',              # 最高质量（VBR模式）
        '-threads', '0',          # 自动多线程
        '-loglevel', 'error',     # 仅显示错误信息
        output_audio
    ]

    try:
        print(f"开始转换^_^~")
        subprocess.run(command, check=True)
        print("转换成功！")
        print(f"输出文件大小：{os.path.getsize(output_audio)/1024/1024:.2f} MB")
    except subprocess.CalledProcessError as e:
        print(f"转换失败：{e.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"发生未知错误：{str(e)}")

if __name__ == "__main__":
    main()