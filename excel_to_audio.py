"""
Excel文章转音频工具 v1.0
功能：从Excel读取微信文章链接，抓取正文，转换为语音
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

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================
# 配置区
# ============================================
CONFIG = {
    # 使用的语音（可用语音列表见 --voices 参数）
    'voice': 'zh-CN-XiaoxiaoNeural',

    # 单篇文章最大字数（超过会截断）
    'max_chars': 10000,

    # 是否启用详细日志
    'verbose': True,

    # 每篇文章之间的延迟（秒）- 避免被微信限制
    'delay_between_articles': 5,

    # 每批处理的文章数量
    'batch_size': 5,

    # 批次之间的延迟（秒）
    'delay_between_batches': 30,
}

# ============================================
# 辅助函数
# ============================================
def clean_article_tail(text):
    """清理文章结尾的微信公众号信息"""

    # 常见的结尾标记模式
    patterns = [
        r'策\s*划\s*[:：].+',  # "策划："
        r'责\s*编\s*[:：].+',  # "责编："
        r'审\s*核\s*[:：].+',  # "审核："
        r'来\s*源\s*.+',       # "来源 xxx"
        r'转\s*载请注明',      # "转载请注明"
        r'微\s*信公\s*众号',   # "微信公众号"
        r'独\s*家访\s*谈\s*\|', # "独家访谈 |"（出现在结尾时）
        r'文\s*中观点',        # "文中观点"
        r'访谈手记',           # "访谈手记"
    ]

    # 找到第一个匹配位置
    earliest_pos = len(text)

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            pos = match.start()
            # 向前查找段落开头，保留完整段落
            paragraph_start = text.rfind('\n\n', 0, pos)
            if paragraph_start != -1:
                pos = paragraph_start
            else:
                # 找不到段落开头，从当前行开头删除
                line_start = text.rfind('\n', 0, pos)
                if line_start != -1:
                    pos = line_start

            if pos < earliest_pos:
                earliest_pos = pos

    # 删除找到的位置之后的内容
    if earliest_pos < len(text):
        cleaned = text[:earliest_pos].strip()
        # 去除末尾多余的空行
        cleaned = re.sub(r'\n+$', '', cleaned)
        return cleaned

    return text


def fix_text_formatting(text):
    """修复文本格式问题，避免TTS停顿"""

    # 1. 移除所有换行符，保留段落分隔
    text = re.sub(r'(?<!\n)\n(?!\n)', '', text)

    # 2. 修复被截断的中文词语（例："效\n果" -> "效果"）
    # 中文字符范围内：\u4e00-\u9fff
    text = re.sub(r'([\u4e00-\u9fff])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 3. 修复标点符号前的换行（例：，\n某某 -> ，某某）
    text = re.sub(r'([，。！？；：])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 4. 标点后的换行改为空格（TTS会自然停顿）
    text = re.sub(r'\n+', '，', text)

    # 5. 清理多余空格
    text = re.sub(r' +', '，', text)

    # 6. 确保段落之间有停顿
    text = re.sub(r'，{3,}', '\n\n', text)

    # 7. 最后再次清理换行，保持段落分隔
    text = re.sub(r'([。！？])\s*\n\s*', r'\1\n\n', text)

    return text.strip()


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

                    # 删除"策划"及之后的微信公众号结尾信息
                    text = clean_article_tail(text)

                    # 修复文本格式，避免TTS不自然停顿
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
# 文本转音频
# ============================================
async def text_to_speech(text, output_path, voice=None):
    """使用Edge TTS转换文本为语音"""

    if voice is None:
        voice = CONFIG['voice']

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True

    except Exception as e:
        if CONFIG['verbose']:
            print(f"    TTS Error: {e}")
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
    print(f"  URL: {url}")

    # 1. 抓取文章正文
    print(f"  [1/3] Fetching article content...")

    content = fetch_wechat_article(url)

    if not content:
        print(f"  [✗] Failed to fetch - SKIPPED")
        return False

    content_len = len(content)
    print(f"  [✓] Content length: {content_len} chars")

    # 2. 检查长度
    if content_len > CONFIG['max_chars']:
        content = content[:CONFIG['max_chars']] + "..."
        print(f"  [!] Content truncated to {CONFIG['max_chars']} chars")

    # 3. 转换为音频
    print(f"  [2/3] Converting to speech (this may take a while)...")

    # 安全文件名
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:50]
    output_path = output_dir / f"{idx:03d}_{safe_title}.mp3"

    success = await text_to_speech(content, output_path)

    if success:
        file_size = output_path.stat().st_size / 1024  # KB
        print(f"  [✓] Audio saved: {output_path.name} ({file_size:.1f} KB)")
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
    print(" Excel Article to Audio Converter v1.1")
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
        # 处理指定范围
        if end_index is None:
            end_index = total
        df = df.iloc[start_index-1:end_index]
        total = len(df)
        print(f"  RANGE MODE: Processing articles {start_index}-{end_index}")
    else:
        print(f"  Total articles: {total}")

    print(f"\n[2/5] Output directory: {output_dir.absolute()}")
    print(f"      Voice: {CONFIG['voice']}")
    print(f"      Max chars per article: {CONFIG['max_chars']}")
    print(f"      Delay between articles: {CONFIG['delay_between_articles']}s")
    print(f"      Batch size: {CONFIG['batch_size']}")
    print(f"      Delay between batches: {CONFIG['delay_between_batches']}s")

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

        # 处理当前批次
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

            # 文章之间的延迟
            if i < batch_end - 1:  # 不是批次最后一篇
                if CONFIG['delay_between_articles'] > 0:
                    print(f"  [⏳] Waiting {CONFIG['delay_between_articles']}s before next article...")
                    await asyncio.sleep(CONFIG['delay_between_articles'])

        # 批次之间的延迟
        if batch_end < total:  # 不是最后一批
            batch_delay = CONFIG['delay_between_batches']
            print(f"\n>>> Batch completed. Waiting {batch_delay}s before next batch to avoid rate limiting...")
            print(f"    This is a good time to take a break! ☕")
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

    # 失败的文章列表
    if failed_count > 0:
        print(f"\n[5/5] Failed articles (can retry later):")
        # 这里可以添加失败列表的记录
        print("  (Check logs above for details)")

    print("="*70)


# ============================================
# 语音列表
# ============================================
def list_voices():
    """列出可用的中文语音"""

    voices = [
        ('zh-CN-XiaoxiaoNeural', 'Female - Xiaoxiao (Standard)'),
        ('zh-CN-YunxiNeural', 'Male - Yunxi'),
        ('zh-CN-YunjianNeural', 'Male - Yunjian (News style)'),
        ('zh-CN-XiaoyiNeural', 'Female - Xiaoyi (Child)'),
        ('zh-CN-YangyangNeural', 'Male - Yangyang'),
        ('zh-CN-XiaochenNeural', 'Female - Xiaochen'),
        ('zh-CN-XiaohanNeural', 'Female - Xiaohan'),
        ('zh-CN-XiaomengNeural', 'Female - Xiaomeng'),
        ('zh-CN-XiaomoNeural', 'Female - Xiaomo'),
        ('zh-CN-XiaoqiuNeural', 'Female - Xiaoqiu'),
        ('zh-CN-XiaoruiNeural', 'Female - Xiaorui'),
        ('zh-CN-XiaoshuangNeural', 'Female twins - Xiaoshuang'),
        ('zh-CN-XiaoxuanNeural', 'Female - Xiaoxuan'),
        ('zh-CN-XiaoyanNeural', 'Female - Xiaoyan'),
        ('zh-CN-XiaoyouNeural', 'Female - Xiaoyou (Child)'),
        ('zh-CN-XiaozhenNeural', 'Female - Xiaozhen'),
        ('zh-CN-YunfengNeural', 'Male - Yunfeng (Storytelling)'),
        ('zh-CN-YunhaoNeural', 'Male - Yunhao'),
        ('zh-CN-YunjieNeural', 'Male - Yunjie'),
        ('zh-CN-YunxiaNeural', 'Male - Yunxia'),
        ('zh-CN-YunyangNeural', 'Male - Yunyang'),
        ('zh-CN-YunzeNeural', 'Male - Yunze'),
        ('zh-TW-HsiaoChenNeural', 'Taiwan - Female - HsiaoChen'),
        ('zh-TW-HsiaoYuNeural', 'Taiwan - Female - HsiaoYu'),
        ('zh-TW-YunJheNeural', 'Taiwan - Male - YunJhe'),
        ('zh-HK-HiuMaanNeural', 'Hong Kong - Female - HiuMaan'),
        ('zh-HK-WanLungNeural', 'Hong Kong - Male - WanLung'),
    ]

    print("\n" + "="*70)
    print(" Available Chinese Voices (Edge TTS)")
    print("="*70)

    for voice_id, desc in voices:
        marker = " <-- DEFAULT" if voice_id == CONFIG['voice'] else ""
        print(f"  {voice_id:40s} - {desc}{marker}")

    print("\nUsage: Set CONFIG['voice'] in the script")
    print("="*70)


# ============================================
# 命令行入口
# ============================================
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Excel articles to audio converter')
    parser.add_argument('excel', nargs='?', default='科协之声-用作转音频.xlsx', help='Excel file path')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode (first 3 articles only)')
    parser.add_argument('--voices', '-v', action='store_true', help='List available voices')
    parser.add_argument('--range', '-r', type=str, help='Process range (e.g., "2-10" for articles 2-10)')
    parser.add_argument('--start', '-s', type=int, help='Start from article number')
    parser.add_argument('--end', '-e', type=int, help='End at article number')

    args = parser.parse_args()

    if args.voices:
        list_voices()
    else:
        # 处理范围参数
        start_index = 1
        end_index = None

        if args.range:
            try:
                parts = args.range.split('-')
                start_index = int(parts[0])
                end_index = int(parts[1]) if len(parts) > 1 else None
            except:
                print("Invalid range format. Use: --range START-END (e.g., --range 2-10)")
                exit(1)
        elif args.start or args.end:
            start_index = args.start or 1
            end_index = args.end

        asyncio.run(main(args.excel, args.test, start_index, end_index))
