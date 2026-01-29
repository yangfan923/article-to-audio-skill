"""
音频混合脚本 v2.0：配音 + 背景音乐
- 背景音乐音量30%
- 音乐循环直到配音结束
- 结尾渐出3秒
- 支持批量处理
"""

import subprocess
import random
import os
import sys
import io
from pathlib import Path

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_audio_duration(file_path):
    """获取音频时长（秒）"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def mix_voice_with_bgm(voice_file, bgm_file, output_file, bgm_volume=0.3, fade_out_duration=3):
    """
    混合配音和背景音乐
    """
    print(f"[*] Processing: {Path(voice_file).name}")

    # 获取配音时长
    voice_duration = get_audio_duration(voice_file)
    print(f"    Voice duration: {voice_duration:.2f}s ({voice_duration/60:.1f} minutes)")

    # 获取背景音乐时长
    bgm_duration = get_audio_duration(bgm_file)
    print(f"    BGM duration: {bgm_duration:.2f}s")

    # 计算循环次数
    loop_count = int(voice_duration / bgm_duration) + 1
    print(f"    BGM will loop {loop_count} times")

    # 构建ffmpeg滤波器
    filter_complex = f"[1:a]aloop=loop=-1:size=2e+09[bgm_loop];"
    filter_complex += f"[bgm_loop]atrim=0:{voice_duration}[bgm_trim];"
    filter_complex += f"[bgm_trim]volume={bgm_volume}[bgm_vol];"
    filter_complex += f"[bgm_vol]afade=t=out:st={voice_duration-fade_out_duration}:d={fade_out_duration}[bgm_out];"
    filter_complex += "[0:a][bgm_out]amix=inputs=2:duration=first:dropout_transition=2[outa]"

    # ffmpeg命令
    cmd = [
        'ffmpeg', '-y',
        '-i', str(voice_file),
        '-i', str(bgm_file),
        '-filter_complex', filter_complex,
        '-map', '[outa]',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_file)
    ]

    print(f"    Mixing with BGM at {bgm_volume*100}% volume...")
    print(f"    Fade out: {fade_out_duration}s at the end")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    [!] Error: {result.stderr[:200]}")
        return False

    # 获取输出文件大小
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"    [OK] Output: {size_mb:.2f} MB")

    return True

def batch_process():
    """批量处理所有文章"""

    print("="*70)
    print(" Batch Audio Mixer: Voice + BGM")
    print("="*70)
    print()

    # 配置
    voice_folder = Path("audio_output")
    bgm_folder = Path("素材")
    output_folder = Path("audio_with_bgm")
    output_folder.mkdir(exist_ok=True)

    # 获取所有配音文件
    voice_files = sorted(voice_folder.glob("*.mp3"))

    # 过滤掉已经有bgm的文件
    voice_files = [vf for vf in voice_files if "with_bgm" not in vf.name]

    if not voice_files:
        print("[!] No voice audio files found")
        return

    print(f"[*] Found {len(voice_files)} voice audio files")

    # 获取所有背景音乐
    bgm_files = list(bgm_folder.glob("*.mp3"))

    if not bgm_files:
        print("[!] No BGM files found")
        return

    print(f"[*] Found {len(bgm_files)} BGM files")
    print("="*70)
    print()

    # 批量处理
    success_count = 0
    failed_count = 0

    for i, voice_file in enumerate(voice_files, 1):
        # 随机选择BGM
        bgm_file = random.choice(bgm_files)

        # 输出文件
        output_file = output_folder / f"{voice_file.stem}_with_bgm_{bgm_file.stem}.mp3"

        print(f"[{i}/{len(voice_files)}] {voice_file.name}")

        # 混合
        success = mix_voice_with_bgm(
            voice_file=voice_file,
            bgm_file=bgm_file,
            output_file=output_file,
            bgm_volume=0.3,
            fade_out_duration=3
        )

        if success:
            success_count += 1
        else:
            failed_count += 1

        print()

    # 总结
    print("="*70)
    print(f"SUMMARY")
    print("="*70)
    print(f"  Total:      {len(voice_files)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed:     {failed_count}")
    print(f"  Output:     {output_folder.absolute()}")
    print("="*70)

def single_process(article_num="001"):
    """单篇测试"""

    print("="*70)
    print(" Single Audio Mixer Test")
    print("="*70)
    print()

    # 配置
    voice_folder = Path("audio_output")
    bgm_folder = Path("素材")
    output_folder = Path("audio_with_bgm")
    output_folder.mkdir(exist_ok=True)

    # 查找配音文件
    voice_files = list(voice_folder.glob(f"{article_num}_*.mp3"))
    voice_files = [vf for vf in voice_files if "with_bgm" not in vf.name]

    if not voice_files:
        print(f"[!] No voice audio found for article {article_num}")
        return

    # 优先使用格式已修复的版本
    voice_file = voice_files[0]
    for vf in voice_files:
        if "格式" in vf.name or "fixed" in vf.name:
            voice_file = vf
            break

    # 获取背景音乐
    bgm_files = list(bgm_folder.glob("*.mp3"))

    if not bgm_files:
        print("[!] No BGM files found")
        return

    # 随机选择
    bgm_file = random.choice(bgm_files)

    print(f"[*] Voice: {voice_file.name}")
    print(f"[*] BGM: {bgm_file.name}")
    print("="*70)
    print()

    # 输出文件
    output_file = output_folder / f"{voice_file.stem}_with_bgm_{bgm_file.stem}.mp3"

    # 混合
    success = mix_voice_with_bgm(
        voice_file=voice_file,
        bgm_file=bgm_file,
        output_file=output_file,
        bgm_volume=0.3,
        fade_out_duration=3
    )

    if success:
        print()
        print("="*70)
        print("[OK] Mixed audio saved:")
        print(f"     {output_file.absolute()}")
        print("="*70)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Audio mixer: voice + BGM')
    parser.add_argument('--batch', '-b', action='store_true', help='Batch process all articles')
    parser.add_argument('--article', '-a', type=str, default='001', help='Article number (default: 001)')

    args = parser.parse_args()

    if args.batch:
        batch_process()
    else:
        single_process(args.article)
