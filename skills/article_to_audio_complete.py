"""
文章转音频完整工具 v1.0
一站式解决：抓取文章 → 清理内容 → 生成配音 → 添加BGM

功能：
1. 从Excel读取文章列表
2. 抓取微信文章正文
3. 彻底清理元数据
4. 生成配音（Edge TTS）
5. 添加背景音乐
"""

import pandas as pd
import asyncio
import edge_tts
import requests
from bs4 import BeautifulSoup
import re
import os
import sys
import io
import subprocess
import random
from pathlib import Path
from datetime import datetime

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================
# 配置区
# ============================================
CONFIG = {
    # TTS语音
    'voice': 'zh-CN-XiaoxiaoNeural',

    # 文章分段大小
    'segment_max_chars': 3000,

    # BGM设置
    'bgm_volume': 0.3,
    'fade_out_duration': 3,

    # 延迟设置
    'delay_between_articles': 5,
    'batch_size': 5,
    'delay_between_batches': 30,

    # 路径设置
    'bgm_folder': '素材',
    'output_voice_folder': 'audio_output',
    'output_text_folder': 'articles_for_review',
    'output_final_folder': 'audio_with_bgm',
}

# ============================================
# 文章清理功能
# ============================================
def clean_article_content(text):
    """彻底清理文章内容"""

    stop_markers = [
        '访谈手记',
        '*文中观点为访谈者',
        '文中观点为访谈者',
        '文中观点为作者',
        '策　　划：',
        '策  划：',
        '策划：',
        '访谈作者：',
        '责　　编：',
        '责  编：',
        '责编：',
        '审　　核：',
        '审  核：',
        '审核：',
        '值班编委：',
        '来　　源：',
        '来  源：',
        '来源：',
        '出品：',
        '监制：',
        '执行：',
        '编委：',
        '转载请注明',
        '欢迎您的来稿',
        '投稿邮箱',
        '微信公众号',
    ]

    earliest_pos = len(text)

    for marker in stop_markers:
        pos = text.find(marker)
        if pos != -1 and pos < earliest_pos:
            paragraph_start = text.rfind('\n\n', 0, pos)
            if paragraph_start != -1:
                paragraph_end = text.find('\n\n', paragraph_start + 2)
                if paragraph_end == -1:
                    paragraph_end = len(text)
                paragraph = text[paragraph_start:paragraph_end]
                if len(paragraph) < 200 and any(m in paragraph for m in stop_markers):
                    earliest_pos = paragraph_start
                else:
                    earliest_pos = pos
            else:
                earliest_pos = pos

    if earliest_pos < len(text):
        text = text[:earliest_pos].strip()

    # 额外清理：删除结尾的人员信息
    end_patterns = [
        r'编辑\s*[:：][^\n]*责编\s*[:：].*',
        r'责编\s*[:：][^\n]*',
        r'审\s*核\s*[:：][^\n]*',
        r'策\s*划\s*[:：][^\n]*',
        r'访谈作者\s*[:：][^\n]*',
        r'值班编委\s*[:：][^\n]*',
        r'特别鸣谢.*责编.*',
        r'编辑.*责编.*',
        r'口\s*，\s*，\s*，\s*述\s*[:：].*',
        r'责\s*，\s*，\s*，\s*编\s*[:：].*',
        r'审\s*，\s*，\s*，\s*核\s*[:：].*',
    ]

    for pattern in end_patterns:
        match = re.search(pattern, text)
        if match:
            pos = match.start()
            period_pos = text.rfind('。', 0, pos)
            if period_pos != -1 and period_pos > len(text) - 300:
                text = text[:period_pos + 1].strip()

    # 删除末尾关键词
    text = re.sub(r'\s*口述\s*$', '', text)
    text = re.sub(r'\s*素材\s*$', '', text)
    text = re.sub(r'\s*编辑\s*$', '', text)
    text = re.sub(r'\s*责\s*$', '', text)
    text = re.sub(r'\s*编\s*$', '', text)
    text = re.sub(r'\s*审\s*$', '', text)
    text = re.sub(r'\s*核\s*$', '', text)

    return text.strip()


def fix_text_formatting(text):
    """修复文本格式"""
    text = re.sub(r'(?<!\n)\n(?!\n)', '', text)
    text = re.sub(r'([\u4e00-\u9fff])\n([\u4e00-\u9fff])', r'\1\2', text)
    text = re.sub(r'([，。！？；：])\n([\u4e00-\u9fff])', r'\1\2', text)
    text = re.sub(r' +', '，', text)
    text = re.sub(r'，{3,}', '\n\n', text)
    text = re.sub(r'([。！？])\s*\n\s*', r'\1\n\n', text)
    return text.strip()


# ============================================
# 文章抓取
# ============================================
def fetch_wechat_article(url):
    """抓取微信文章正文"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        import urllib3
        urllib3.disable_warnings()

        for method in ['GET', 'POST']:
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=15, verify=False)
                else:
                    response = requests.post(url, headers=headers, timeout=15, verify=False)

                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', class_='rich_media_content')

                if not content_div:
                    content_div = soup.find('div', id='js_content')

                if content_div:
                    for tag in content_div.find_all(['script', 'style', 'iframe', 'noscript']):
                        tag.decompose()

                    text = content_div.get_text(separator='\n', strip=True)
                    text = clean_article_content(text)
                    text = fix_text_formatting(text)

                    return text.strip()

            except Exception:
                continue

        return None

    except Exception:
        return None


# ============================================
# 文本转音频
# ============================================
async def text_to_speech(text, output_path, voice=None):
    """使用Edge TTS转换文本为语音"""

    if voice is None:
        voice = CONFIG['voice']

    segments = split_text_into_segments(text, CONFIG['segment_max_chars'])

    if len(segments) == 1:
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            return True
        except Exception:
            return False
    else:
        segment_files = []
        temp_dir = output_path.parent / '.temp_segments'
        temp_dir.mkdir(exist_ok=True)

        try:
            for i, segment in enumerate(segments):
                seg_path = temp_dir / f"{output_path.stem}_part{i+1}.mp3"
                communicate = edge_tts.Communicate(segment, voice)
                await communicate.save(str(seg_path))
                segment_files.append(seg_path)

            merge_audio_files(segment_files, output_path)

            for sf in segment_files:
                sf.unlink()

            return True

        except Exception:
            for sf in segment_files:
                if sf.exists():
                    sf.unlink()
            return False


def split_text_into_segments(text, max_chars=3000):
    """将长文本分段"""

    if len(text) <= max_chars:
        return [text]

    segments = []
    current_segment = ""
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) > max_chars:
            sentences = re.split(r'([。！？])', para)
            para_parts = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    para_parts.append(sentences[i] + sentences[i + 1])
                else:
                    para_parts.append(sentences[i])

            for part in para_parts:
                if len(current_segment) + len(part) + 2 <= max_chars:
                    current_segment += part + '\n\n'
                else:
                    if current_segment:
                        segments.append(current_segment.strip())
                    current_segment = part + '\n\n'
        else:
            if len(current_segment) + len(para) + 2 <= max_chars:
                current_segment += para + '\n\n'
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = para + '\n\n'

    if current_segment:
        segments.append(current_segment.strip())

    return segments


def merge_audio_files(input_files, output_path):
    """合并音频文件"""

    try:
        list_file = output_path.parent / 'file_list.txt'
        with open(list_file, 'w', encoding='utf-8') as f:
            for input_file in input_files:
                f.write(f"file '{input_file.absolute()}'\n")

        result = subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
             '-i', str(list_file),
             '-c', 'copy',
             str(output_path)],
            capture_output=True,
            text=True
        )

        list_file.unlink()

        return result.returncode == 0

    except Exception:
        return False


# ============================================
# BGM混合
# ============================================
def get_audio_duration(file_path):
    """获取音频时长"""

    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def mix_voice_with_bgm(voice_file, bgm_file, output_file):
    """混合配音和背景音乐"""

    voice_duration = get_audio_duration(voice_file)
    bgm_duration = get_audio_duration(bgm_file)
    loop_count = int(voice_duration / bgm_duration) + 1

    filter_complex = f"[1:a]aloop=loop=-1:size=2e+09[bgm_loop];"
    filter_complex += f"[bgm_loop]atrim=0:{voice_duration}[bgm_trim];"
    filter_complex += f"[bgm_trim]volume={CONFIG['bgm_volume']}[bgm_vol];"
    filter_complex += f"[bgm_vol]afade=t=out:st={voice_duration-CONFIG['fade_out_duration']}:d={CONFIG['fade_out_duration']}[bgm_out];"
    filter_complex += "[0:a][bgm_out]amix=inputs=2:duration=first:dropout_transition=2[outa]"

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

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    [!] Mixing warning: {result.stderr[:100] if result.stderr else 'Unknown'}")
        return False

    return True


# ============================================
# 主处理函数
# ============================================
async def process_article(row, voice_folder, output_folder, index, total):
    """处理单篇文章"""

    idx = int(row['序号'])
    title = str(row['图文名称']) if pd.notna(row['图文名称']) else f"Article_{idx}"
    url = str(row['图文链接']) if pd.notna(row['图文链接']) else ""

    print(f"\n[{index}/{total}] Article {idx}: {title[:50]}...")

    if not url or 'http' not in url:
        print(f"  [!] No valid URL - SKIPPED")
        return False

    # 1. 抓取文章
    print(f"  [1/4] Fetching article...")
    content = fetch_wechat_article(url)

    if not content:
        print(f"  [!] Failed to fetch - SKIPPED")
        return False

    print(f"      Length: {len(content)} chars")

    # 2. 保存文本
    text_folder = Path(CONFIG['output_text_folder'])
    text_folder.mkdir(exist_ok=True)
    text_file = text_folder / f"{idx:03d}_{re.sub(r'[<>:"/\\|?*]', '_', title)[:50]}.txt"

    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 3. 生成配音
    print(f"  [2/4] Generating voice...")
    voice_file = voice_folder / f"{idx:03d}_{re.sub(r'[<>:"/\\|?*]', '_', title)[:50]}.mp3"

    success = await text_to_speech(content, voice_file)

    if not success:
        print(f"  [!] TTS failed - SKIPPED")
        return False

    file_size = voice_file.stat().st_size / 1024
    print(f"      Voice: {file_size/1024:.2f} MB")

    # 4. 添加BGM
    print(f"  [3/4] Mixing with BGM...")
    bgm_folder = Path(CONFIG['bgm_folder'])
    bgm_files = list(bgm_folder.glob("*.mp3"))

    if not bgm_files:
        print(f"      No BGM found - skipping BGM")
        return True

    bgm_file = random.choice(bgm_files)
    final_file = output_folder / f"{idx:03d}_{re.sub(r'[<>:"/\\|?*]', '_', title)[:50]}_with_bgm_{bgm_file.stem}.mp3"

    mix_success = mix_voice_with_bgm(voice_file, bgm_file, final_file)

    if mix_success:
        final_size = final_file.stat().st_size / 1024
        print(f"      Final: {final_size/1024:.2f} MB")
        print(f"  [4/4] Done!")
        return True
    else:
        print(f"  [!] BGM mixing failed - voice saved without BGM")
        return True


# ============================================
# 主函数
# ============================================
async def main(excel_path, test_mode=False, start_index=1, end_index=None, no_bgm=False):
    """主函数"""

    print("="*70)
    print(" Article to Audio Converter v1.0")
    print(" Complete Solution: Fetch → Clean → TTS → Mix")
    print("="*70)

    # 创建输出目录
    voice_folder = Path(CONFIG['output_voice_folder'])
    voice_folder.mkdir(exist_ok=True)

    output_folder = Path(CONFIG['output_final_folder'])
    output_folder.mkdir(exist_ok=True)

    # 读取Excel
    print(f"\n[1/5] Reading Excel: {excel_path}")
    df = pd.read_excel(excel_path)

    total = len(df)

    if test_mode:
        df = df.head(3)
        total = 3
        print(f"  TEST MODE: Processing first 3 articles only")
    elif start_index > 1 or end_index is not None:
        if end_index is None:
            end_index = total
        df = df.iloc[start_index-1:end_index]
        total = len(df)
        print(f"  RANGE MODE: Processing articles {start_index}-{end_index}")
    else:
        print(f"  Total articles: {total}")

    print(f"\n[2/5] Configuration:")
    print(f"      Voice: {CONFIG['voice']}")
    print(f"      Segment size: {CONFIG['segment_max_chars']} chars")
    print(f"      BGM volume: {CONFIG['bgm_volume']*100}%")
    if no_bgm:
        print(f"      BGM: DISABLED")
        CONFIG['bgm_folder'] = None

    print(f"\n[3/5] Output folders:")
    print(f"      Text:   {Path(CONFIG['output_text_folder']).absolute()}")
    print(f"      Voice:  {voice_folder.absolute()}")
    print(f"      Final:  {output_folder.absolute()}")

    # 开始处理
    print(f"\n[4/5] Processing articles...")
    print("="*70)

    success_count = 0
    failed_count = 0
    start_time = datetime.now()

    for batch_num in range(0, total, CONFIG['batch_size']):
        batch_start = batch_num
        batch_end = min(batch_num + CONFIG['batch_size'], total)

        print(f"\n>>> Batch {batch_num // CONFIG['batch_size'] + 1}: Articles {batch_start + 1}-{batch_end}")

        for i in range(batch_start, batch_end):
            index = i + 1
            row = df.iloc[i]

            try:
                success = await process_article(row, voice_folder, output_folder, index, start_index + total - 1)

                if success:
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"  [!] Exception: {e}")
                failed_count += 1

            # 延迟
            if i < batch_end - 1:
                if CONFIG['delay_between_articles'] > 0:
                    await asyncio.sleep(CONFIG['delay_between_articles'])

        # 批次延迟
        if batch_end < total:
            print(f"\n>>> Waiting {CONFIG['delay_between_batches']}s before next batch...")
            await asyncio.sleep(CONFIG['delay_between_batches'])

    # 总结
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*70)
    print(f"[5/5] SUMMARY")
    print("="*70)
    print(f"  Total processed: {total}")
    print(f"  Successful:      {success_count}")
    print(f"  Failed:          {failed_count}")
    print(f"  Success rate:    {success_count/total*100:.1f}%")
    print(f"  Time elapsed:    {elapsed/60:.1f} minutes")
    print(f"  Output folder:   {output_folder.absolute()}")
    print("="*70)


# ============================================
# 命令行入口
# ============================================
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Article to Audio Converter - Complete Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python article_to_audio_complete.py articles.xlsx              # Process all
  python article_to_audio_complete.py articles.xlsx --test       # Test first 3
  python article_to_audio_complete.py articles.xlsx --range 1-10 # Process 1-10
  python article_to_audio_complete.py articles.xlsx --no-bgm      # Skip BGM
        """
    )

    parser.add_argument('excel', help='Excel file path')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode (first 3 articles)')
    parser.add_argument('--range', '-r', type=str, help='Process range (e.g., "1-10")')
    parser.add_argument('--start', '-s', type=int, help='Start index')
    parser.add_argument('--end', '-e', type=int, help='End index')
    parser.add_argument('--no-bgm', action='store_true', help='Skip background music mixing')

    args = parser.parse_args()

    start_index = 1
    end_index = None

    if args.range:
        try:
            parts = args.range.split('-')
            start_index = int(parts[0])
            end_index = int(parts[1]) if len(parts) > 1 else None
        except:
            print("Invalid range format. Use: --range START-END")
            exit(1)
    elif args.start or args.end:
        start_index = args.start or 1
        end_index = args.end

    if args.no_bgm:
        print("BGM mixing disabled")

    asyncio.run(main(args.excel, args.test, start_index, end_index))
