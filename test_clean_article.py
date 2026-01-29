"""
测试文章清理功能
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def clean_article_content(text):
    """彻底清理文章内容，只保留正文"""

    # 定义需要删除的起始标记（从这些标记开始到文章末尾全部删除）
    stop_markers = [
        '文中观点为访谈者',
        '文中观点为作者',
        '文中观点仅供参考',
        '访谈作者',
        '策　　划',
        '策  划',
        '策划',
        '责　　编',
        '责  编',
        '责编',
        '审　　核',
        '审  核',
        '审核',
        '值班编委',
        '来　　源',
        '来  源',
        '来源',
        '出品',
        '监制',
        '执行',
        '编委',
        '转载请注明',
        '欢迎您的来稿',
        '投稿邮箱',
        '微信公众号',
        '相关阅读',
        '推荐阅读',
        '延伸阅读',
        '更多阅读',
        '访谈手记',
    ]

    # 查找最早出现的停止标记
    earliest_pos = len(text)

    for marker in stop_markers:
        pos = text.find(marker)
        if pos != -1:
            # 找到标记所在段落的开始
            paragraph_start = text.rfind('\n\n', 0, pos)
            if paragraph_start != -1:
                # 删除整个段落
                if paragraph_start < earliest_pos:
                    earliest_pos = paragraph_start
            else:
                # 找当前行的开始
                line_start = text.rfind('\n', 0, pos)
                if line_start != -1 and line_start < earliest_pos:
                    earliest_pos = line_start

    # 截断
    if earliest_pos < len(text):
        text = text[:earliest_pos].strip()

    return text


def fix_text_formatting(text):
    """修复文本格式"""

    # 移除句子内的换行
    text = re.sub(r'(?<!\n)\n(?!\n)', '', text)

    # 修复被截断的中文词语
    text = re.sub(r'([\u4e00-\u9fff])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 修复标点前的换行
    text = re.sub(r'([，。！？；：])\n([\u4e00-\u9fff])', r'\1\2', text)

    # 多个空格转为停顿
    text = re.sub(r' +', '，', text)

    # 段落分隔
    text = re.sub(r'，{3,}', '\n\n', text)

    # 句号后的换行保持段落停顿
    text = re.sub(r'([。！？])\s*\n\s*', r'\1\n\n', text)

    return text.strip()


def fetch_and_clean_article(url):
    """抓取并清理文章"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    import urllib3
    urllib3.disable_warnings()

    response = requests.get(url, headers=headers, timeout=15, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', class_='rich_media_content')

    if not content_div:
        content_div = soup.find('div', id='js_content')

    if content_div:
        for tag in content_div.find_all(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()

        text = content_div.get_text(separator='\n', strip=True)

        # 清理
        text = clean_article_content(text)
        text = fix_text_formatting(text)

        return text

    return None


# 测试
if __name__ == '__main__':
    # 读取Excel
    df = pd.read_excel('科协之声-用作转音频.xlsx')

    # 测试第2篇（最长的）
    article = df.iloc[1]
    url = article['图文链接']
    title = article['图文名称']

    print('='*70)
    print(f'Testing cleaning function')
    print(f'Article: {title}')
    print('='*70)

    # 抓取并清理
    print('\n[1/3] Fetching article...')
    cleaned_text = fetch_and_clean_article(url)

    if cleaned_text:
        print(f'[✓] Original length: 4648 chars')
        print(f'[✓] Cleaned length: {len(cleaned_text)} chars')
        print(f'[✓] Removed: {4648 - len(cleaned_text)} chars')

        print('\n[2/3] First 300 chars of cleaned text:')
        print('='*70)
        print(cleaned_text[:300])

        print('\n\n[3/3] Last 300 chars of cleaned text:')
        print('='*70)
        print(cleaned_text[-300:])

        # 保存到文件
        with open('test_cleaned_article.txt', 'w', encoding='utf-8') as f:
            f.write(cleaned_text)

        print('\n\n[✓] Saved to: test_cleaned_article.txt')
        print('\nPlease review the file to confirm cleaning is correct.')

        # 检查是否还有不该有的内容
        bad_patterns = ['访谈作者', '责编', '审核', '值班编委', '策划', '来源', '转载请注明', '微信公众号', '投稿邮箱']
        found_bad = []
        for pattern in bad_patterns:
            if pattern in cleaned_text:
                found_bad.append(pattern)

        if found_bad:
            print(f'\n[!] WARNING: Found patterns that should be removed: {found_bad}')
        else:
            print('\n[✓] No unwanted patterns found!')

    else:
        print('[✗] Failed to fetch article')

    print('='*70)
