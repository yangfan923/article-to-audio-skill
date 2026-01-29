"""
Excel文章转音频工具 v2.0
功能：从Excel读取微信文章链接，抓取正文，转换为语音
改进：彻底清理非正文内容 + 支持长文章分段生成
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
from pathlib import Path
from datetime import datetime
import subprocess

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================
# 配置区
# ============================================
CONFIG = {
    # 使用的语音
    'voice': 'zh-CN-XiaoxiaoNeural',

    # 单段最大字数（超过会分段生成）
    'segment_max_chars': 3000,

    # 是否启用详细日志
    'verbose': True,

    # 每篇文章之间的延迟（秒）
    'delay_between_articles': 5,

    # 每批处理的文章数量
    'batch_size': 5,

    # 批次之间的延迟（秒）
    'delay_between_batches': 30,
}

# ============================================
# 辅助函数 - 彻底清理非正文内容
# ============================================
def clean_article_content(text):
    """彻底清理文章内容，只保留正文"""

    # 定义停止标记（按优先级排序）
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
            # 找到标记所在段落的开始
            paragraph_start = text.rfind('\n\n', 0, pos)

            if paragraph_start != -1:
                # 检查这个段落是否只包含元数据
                paragraph_end = text.find('\n\n', paragraph_start + 2)
                if paragraph_end == -1:
                    paragraph_end = len(text)

                paragraph = text[paragraph_start:paragraph_end]

                # 如果段落包含停止标记且长度<200字，删除整个段落
                if len(paragraph) < 200 and any(m in paragraph for m in stop_markers):
                    earliest_pos = paragraph_start
                else:
                    # 否则只删除从标记开始
                    earliest_pos = pos
            else:
                earliest_pos = pos

    # 截断
    if earliest_pos < len(text):
        text = text[:earliest_pos].strip()

    return text


def fix_text_formatting(text):
    """修复文本格式问题，避免TTS停顿"""

    # 1. 移除所有换行符，保留段落分隔
    text = re.sub(r'(?<!\n)\n(?!\n)', '', text)

    # 2. 修复被截断的中文词语
    text = re.sub(r'([\u4e00-\u9fff])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 3. 修复标点符号前的换行
    text = re.sub(r'([，。！？；：])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 4. 标点后的换行改为停顿标记
    text = re.sub(r'\n+', '，', text)

    # 5. 清理多余空格
    text = re.sub(r' +', '，', text)

    # 6. 确保段落之间有停顿
    text = re.sub(r'，{3,}', '\n\n', text)

    # 7. 最后再次清理换行，保持段落分隔
    text = re.sub(r'([。！？])\s*\n\s*', r'\1\n\n', text)

    return text.strip()


def split_text_into_segments(text, max_chars=3000):
    """将长文本分段，每段不超过max_chars字"""

    # 如果文本不长，不需要分段
    if len(text) <= max_chars:
        return [text]

    segments = []
    current_segment = ""

    # 按段落分割
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 如果单个段落就超过限制，强制在句子边界分割
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
            # 检查添加这个段落是否会超限
            if len(current_segment) + len(para) + 2 <= max_chars:
                current_segment += para + '\n\n'
            else:
                # 保存当前段
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = para + '\n\n'

    # 添加最后一段
    if current_segment:
        segments.append(current_segment.strip())

    return segments


# ============================================
# 微信文章抓取
# ============================================
def fetch_wechat_article(url):
    """抓取微信文章正文"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
                    # 清理脚本、样式、iframe等
                    for tag in content_div.find_all(['script', 'style', 'iframe', 'noscript']):
                        tag.decompose()

                    text = content_div.get_text(separator='\n', strip=True)

                    # 彻底清理非正文内容
                    text = clean_article_content(text)

                    # 修复文本格式
                    text = fix_text_formatting(text)

                    return text.strip()

            except Exception as e:
                if CONFIG['verbose']:
                    print(f"    [{method}] Failed: {e}")
                continue

        return None

    except Exception as e:
        if CONFIG['verbose']:
            print(f"    Error: {e}")
        return None


# ============================================
# 文本转音频（支持分段）
# ============================================
async def text_to_speech(text, output_path, voice=None):
    """使用Edge TTS转换文本为语音"""

    if voice is None:
        voice = CONFIG['voice']

    # 检查是否需要分段
    segments = split_text_into_segments(text, CONFIG['segment_max_chars'])

    if len(segments) == 1:
        # 不需要分段，直接生成
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            if CONFIG['verbose']:
                print(f"    TTS Error: {e}")
            return False
    else:
        # 需要分段生成，然后合并
        print(f"    [!] Long article ({len(text)} chars), splitting into {len(segments)} segments...")

        segment_files = []
        temp_dir = output_path.parent / '.temp_segments'
        temp_dir.mkdir(exist_ok=True)

        try:
            # 生成每个段落
            for i, segment in enumerate(segments):
                seg_path = temp_dir / f"{output_path.stem}_part{i+1}.mp3"
                print(f"      [{i+1}/{len(segments)}] Generating segment {len(segment)} chars...")

                communicate = edge_tts.Communicate(segment, voice)
                await communicate.save(str(seg_path))
                segment_files.append(seg_path)

            # 合并音频文件
            print(f"      [*] Merging {len(segment_files)} segments...")
            merge_audio_files(segment_files, output_path)

            # 清理临时文件
            for sf in segment_files:
                sf.unlink()
            try:
                temp_dir.rmdir()
            except:
                pass

            return True

        except Exception as e:
            if CONFIG['verbose']:
                print(f"    TTS Error: {e}")
            # 清理临时文件
            for sf in segment_files:
                if sf.exists():
                    sf.unlink()
            return False


def merge_audio_files(input_files, output_path):
    """合并多个MP3文件"""

    try:
        # 使用 ffmpeg 合并
        # 创建文件列表
        list_file = output_path.parent / 'file_list.txt'
        with open(list_file, 'w', encoding='utf-8') as f:
            for input_file in input_files:
                f.write(f"file '{input_file.absolute()}'\n")

        # 使用 ffmpeg concat 协议合并
        result = subprocess.run(
            [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', str(list_file),
                '-c', 'copy',
                str(output_path)
            ],
            capture_output=True,
            text=True
        )

        # 清理列表文件
        list_file.unlink()

        if result.returncode != 0:
            print(f"      [!] ffmpeg warning: {result.stderr}")

        return result.returncode == 0

    except FileNotFoundError:
        # ffmpeg 不可用，简单复制第一个文件
        print(f"      [!] ffmpeg not found, using first segment only")
        import shutil
        shutil.copy(input_files[0], output_path)
        return True
    except Exception as e:
        print(f"      [!] Merge error: {e}")
        return False


# ============================================
# 处理单篇文章
# ============================================
async def process_article(row, output_dir, index, total):
    """处理单篇文章"""

    idx = row['序号']
    title = row['图文名称']
    url = row['图文链接']

    print(f"\n[{index}/{total}] Article {idx}: {title[:60]}...")

    # 1. 抓取文章正文
    print(f"  [1/3] Fetching article content...")

    content = fetch_wechat_article(url)

    if not content:
        print(f"  [✗] Failed to fetch - SKIPPED")
        return False

    content_len = len(content)
    print(f"  [✓] Content length: {content_len} chars")

    # 2. 检查长度
    segments_needed = (content_len + CONFIG['segment_max_chars'] - 1) // CONFIG['segment_max_chars']
    if segments_needed > 1:
        print(f"  [!] Will split into {segments_needed} segments for complete audio")

    # 3. 转换为音频
    print(f"  [2/3] Converting to speech...")

    # 安全文件名
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:50]
    output_path = output_dir / f"{idx:03d}_{safe_title}.mp3"

    success = await text_to_speech(content, output_path)

    if success:
        file_size = output_path.stat().st_size / 1024  # KB
        print(f"  [✓] Audio saved: {output_path.name} ({file_size/1024:.2f} MB)")
        print(f"  [3/3] Done!")
        return True
    else:
        print(f"  [✗] TTS conversion failed")
        return False


# ============================================
# 主函数
# ============================================
async def main(excel_path, test_mode=False, start_index=1, end_index=None):
    """主函数"""

    print("="*70)
    print(" Excel Article to Audio Converter v2.0")
    print(" Improvements: Better cleaning + Long article support")
    print("="*70)

    # 创建输出目录
    output_dir = Path('audio_output')
    output_dir.mkdir(exist_ok=True)

    # 读取Excel
    print(f"\n[1/5] Reading Excel: {excel_path}")
    df = pd.read_excel(excel_path)

    total = len(df)

    # 处理范围
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

    print(f"\n[2/5] Output directory: {output_dir.absolute()}")
    print(f"      Voice: {CONFIG['voice']}")
    print(f"      Segment size: {CONFIG['segment_max_chars']} chars")
    print(f"      Delay between articles: {CONFIG['delay_between_articles']}s")
    print(f"      Batch size: {CONFIG['batch_size']}")

    # 开始处理
    print(f"\n[3/5] Processing articles...")
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
                success = await process_article(row, output_dir, index, start_index + total - 1)

                if success:
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"  [✗] Exception: {e}")
                failed_count += 1

            # 延迟
            if i < batch_end - 1:
                if CONFIG['delay_between_articles'] > 0:
                    print(f"  [⏳] Waiting {CONFIG['delay_between_articles']}s...")
                    await asyncio.sleep(CONFIG['delay_between_articles'])

        # 批次延迟
        if batch_end < total:
            batch_delay = CONFIG['delay_between_batches']
            print(f"\n>>> Batch completed. Waiting {batch_delay}s...")
            await asyncio.sleep(batch_delay)

    # 总结
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*70)
    print(f"[4/5] SUMMARY")
    print("="*70)
    print(f"  Total processed: {total}")
    print(f"  Successful:      {success_count}")
    print(f"  Failed:          {failed_count}")
    print(f"  Success rate:    {success_count/total*100:.1f}%")
    print(f"  Time elapsed:    {elapsed/60:.1f} minutes")
    print(f"  Output folder:   {output_dir.absolute()}")
    print("="*70)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Excel articles to audio converter v2.0')
    parser.add_argument('excel', nargs='?', default='科协之声-用作转音频.xlsx', help='Excel file path')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode (first 3 articles only)')
    parser.add_argument('--range', '-r', type=str, help='Process range (e.g., "2-10")')
    parser.add_argument('--start', '-s', type=int, help='Start from article number')
    parser.add_argument('--end', '-e', type=int, help='End at article number')

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

    asyncio.run(main(args.excel, args.test, start_index, end_index))
