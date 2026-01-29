"""
批量抓取所有文章文本（不生成音频）
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import sys
import io
from pathlib import Path
from datetime import datetime
import time

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


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
    """修复文本格式问题"""

    # 移除句子内的换行
    text = re.sub(r'(?<!\n)\n(?!\n)', '', text)

    # 修复被截断的中文词语
    text = re.sub(r'([\u4e00-\u9fff])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 修复标点前的换行
    text = re.sub(r'([，。！？；：])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 空格处理
    text = re.sub(r' +', '，', text)

    # 段落分隔
    text = re.sub(r'，{3,}', '\n\n', text)

    # 句号后换行
    text = re.sub(r'([。！？])\s*\n\s*', r'\1\n\n', text)

    return text.strip()


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
                    # 清理标签
                    for tag in content_div.find_all(['script', 'style', 'iframe', 'noscript']):
                        tag.decompose()

                    text = content_div.get_text(separator='\n', strip=True)

                    # 清理
                    text = clean_article_content(text)
                    text = fix_text_formatting(text)

                    return text.strip()

            except Exception as e:
                print(f"    [{method}] Failed: {e}")
                continue

        return None

    except Exception as e:
        print(f"    Error: {e}")
        return None


def main():
    """主函数"""

    print("="*70)
    print(" Batch Article Text Fetcher")
    print(" Fetching all articles for review (no audio generation)")
    print("="*70)

    # 创建输出目录
    output_dir = Path('articles_for_review')
    output_dir.mkdir(exist_ok=True)

    # 读取Excel
    print(f"\n[1/4] Reading Excel...")
    df = pd.read_excel('科协之声-用作转音频.xlsx')

    total = len(df)
    print(f"  Total articles: {total}")

    print(f"\n[2/4] Output directory: {output_dir.absolute()}")
    print(f"[3/4] Starting to fetch articles...")
    print("="*70)

    success_count = 0
    failed_count = 0
    failed_articles = []

    start_time = datetime.now()

    for index, row in df.iterrows():
        idx = int(row['序号'])
        title = str(row['图文名称']) if pd.notna(row['图文名称']) else f"Article_{idx}"
        url = str(row['图文链接']) if pd.notna(row['图文链接']) else ""

        print(f"\n[{idx}/{total}] Fetching: {title[:50]}...")

        # 抓取文章
        content = fetch_wechat_article(url)

        if content:
            # 保存到文件
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]
            filename = f"{idx:03d}_{safe_title}.txt"
            filepath = output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            file_size = filepath.stat().st_size / 1024  # KB
            print(f"  [✓] Saved: {filename} ({file_size:.1f} KB, {len(content)} chars)")
            success_count += 1

            # 延迟，避免被限制
            time.sleep(3)

        else:
            print(f"  [✗] Failed to fetch")
            failed_count += 1
            failed_articles.append({
                '序号': idx,
                '标题': title,
                '链接': url
            })

        # 每10篇休息一下
        if (idx) % 10 == 0:
            print(f"\n>>> Progress: {idx}/{total} articles processed")
            print(f"    Taking a 15-second break...")
            time.sleep(15)

    # 总结
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*70)
    print(f"[4/4] SUMMARY")
    print("="*70)
    print(f"  Total articles:   {total}")
    print(f"  Successful:       {success_count}")
    print(f"  Failed:           {failed_count}")
    print(f"  Success rate:     {success_count/total*100:.1f}%")
    print(f"  Time elapsed:     {elapsed/60:.1f} minutes")
    print(f"  Output folder:    {output_dir.absolute()}")
    print("="*70)

    # 保存失败列表
    if failed_articles:
        failed_file = output_dir / '_FAILED_ARTICLES.txt'
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write("Failed to fetch these articles:\n\n")
            for article in failed_articles:
                f.write(f"序号: {article['序号']}\n")
                f.write(f"标题: {article['标题']}\n")
                f.write(f"链接: {article['链接']}\n")
                f.write("-" * 70 + "\n")

        print(f"\n[!] Failed articles list saved to: {failed_file}")

    print(f"\n[✓] All done! Please review articles in: {output_dir}")
    print("="*70)


if __name__ == '__main__':
    main()
