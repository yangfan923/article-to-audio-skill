"""
音频混合脚本：配音 + 背景音乐
- 背景音乐音量30%
- 音乐循环直到配音结束
- 结尾渐出3秒
"""

import subprocess
import random
import os
from pathlib import Path

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

    参数:
        voice_file: 配音文件路径
        bgm_file: 背景音乐文件路径
        output_file: 输出文件路径
        bgm_volume: 背景音乐音量 (0.0-1.0)
        fade_out_duration: 渐出时长（秒）
    """

    print(f"[*] Processing: {Path(voice_file).name}")
    print(f"    Voice: {voice_file}")
    print(f"    BGM: {bgm_file}")
    print(f"    Output: {output_file}")
    print()

    # 获取配音时长
    voice_duration = get_audio_duration(voice_file)
    print(f"[1/4] Voice duration: {voice_duration:.2f} seconds")

    # 获取背景音乐时长
    bgm_duration = get_audio_duration(bgm_file)
    print(f"[2/4] BGM duration: {bgm_duration:.2f} seconds")

    # 计算需要循环的次数
    loop_count = int(voice_duration / bgm_duration) + 1
    print(f"[3/4] BGM will loop {loop_count} times to match voice")

    # 构建ffmpeg命令
    # 步骤：
    # 1. 循环背景音乐到配音长度
    # 2. 调整背景音乐音量为30%
    # 3. 在结尾添加渐出效果
    # 4. 混合配音和背景音乐

    # 方案：使用ffmpeg复杂滤波器
    filter_complex = []

    # 输入0：配音（不做处理）
    # 输入1：背景音乐

    # 背景音乐处理：循环 + 音量调整 + 渐出
    # 使用stream循环来实现无限循环，然后trim到配音长度
    bgm_filter = f"[1:a]aloop=loop=-1:size=2e+09[bgm_loop];"
    bgm_filter += f"[bgm_loop]atrim=0:{voice_duration}[bgm_trim];"
    bgm_filter += f"[bgm_trim]volume={bgm_volume}[bgm_vol];"
    bgm_filter += f"[bgm_vol]afade=t=out:st={voice_duration-fade_out_duration}:d={fade_out_duration}[bgm_out]"

    filter_complex.append(bgm_filter)

    # 混合
    filter_complex.append("[0:a][bgm_out]amix=inputs=2:duration=first:dropout_transition=2[outa]")

    # 组合所有滤波器
    filter_string = ";".join(filter_complex)

    # ffmpeg命令
    cmd = [
        'ffmpeg', '-y',
        '-i', str(voice_file),
        '-i', str(bgm_file),
        '-filter_complex', filter_string,
        '-map', '[outa]',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_file)
    ]

    print(f"[4/4] Mixing audio with BGM at {bgm_volume*100}% volume...")
    print(f"    Fade out: {fade_out_duration}s at the end")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"\n[!] Error during mixing:")
        print(result.stderr)
        return False

    print(f"\n[✓] Successfully mixed!")
    print(f"    Output: {output_file}")

    # 获取输出文件大小
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"    Size: {size_mb:.2f} MB")

    return True

def main():
    """主函数"""

    print("="*70)
    print(" Audio Mixer: Voice + Background Music")
    print("="*70)
    print()

    # 配置
    bgm_folder = Path("素材")
    output_folder = Path("audio_with_bgm")
    output_folder.mkdir(exist_ok=True)

    # 查找第一篇配音
    voice_audios = list(Path("audio_output").glob("001_*.mp3"))

    if not voice_audios:
        print("[!] No voice audio found for article 001")
        return

    voice_audio = voice_audios[0]

    # 优先使用格式已修复的版本
    for va in voice_audios:
        if "格式已修复" in va.name or "格式" in va.name:
            voice_audio = va
            break

    print(f"[*] Voice audio: {voice_audio.name}")

    # 获取所有背景音乐
    bgm_files = list(bgm_folder.glob("*.mp3"))

    if not bgm_files:
        print("[!] No BGM files found in 素材 folder")
        return

    print(f"[*] Found {len(bgm_files)} BGM files:")
    for i, bgm in enumerate(bgm_files, 1):
        size_mb = bgm.stat().st_size / (1024 * 1024)
        print(f"    {i}. {bgm.name} ({size_mb:.1f} MB)")

    # 随机选择一个
    selected_bgm = random.choice(bgm_files)
    print(f"\n[*] Randomly selected: {selected_bgm.name}")
    print("="*70)
    print()

    # 输出文件
    output_file = output_folder / f"001_with_bgm_{selected_bgm.stem}.mp3"

    # 混合
    success = mix_voice_with_bgm(
        voice_file=voice_audio,
        bgm_file=selected_bgm,
        output_file=output_file,
        bgm_volume=0.3,  # 30% 音量
        fade_out_duration=3  # 3秒渐出
    )

    if success:
        print()
        print("="*70)
        print("[✓] Done! You can play the mixed audio:")
        print(f"    {output_file.absolute()}")
        print("="*70)

if __name__ == '__main__':
    main()
