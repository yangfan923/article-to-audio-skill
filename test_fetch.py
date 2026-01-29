"""
测试微信文章抓取
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def fetch_wechat_article(url):
    """抓取微信文章正文 - 改进版"""

    # 更完整的请求头，模拟真实浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        # 禁用SSL警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # 尝试多种方法
        for method in ['GET', 'POST']:
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=15, verify=False)
                else:
                    response = requests.post(url, headers=headers, timeout=15, verify=False)

                response.encoding = 'utf-8'

                # 检查是否成功
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')

                # 微信文章的正文通常在 rich_media_content
                content_div = soup.find('div', class_='rich_media_content')

                if not content_div:
                    # 尝试其他可能的选择器
                    content_div = soup.find('div', id='js_content')

                if content_div:
                    # 清理脚本和样式
                    for tag in content_div.find_all(['script', 'style', 'iframe']):
                        tag.decompose()

                    # 获取文本
                    text = content_div.get_text(separator='\n', strip=True)

                    # 清理多余空行
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    text = re.sub(r' {2,}', ' ', text)  # 多余空格

                    return text.strip()

            except Exception as e:
                print(f"  {method} 方法失败: {e}")
                continue

        print("  ❌ 所有方法都失败了")
        return None

    except Exception as e:
        print(f"  ❌ 抓取异常: {e}")
        return None


# 测试第一个链接
if __name__ == '__main__':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Reading Excel...")
    df = pd.read_excel('科协之声-用作转音频.xlsx')

    first_row = df.iloc[0]
    title = first_row['图文名称']
    url = first_row['图文链接']

    print(f"\nArticle: {title}")
    print(f"URL: {url}")
    print("\nFetching...")

    content = fetch_wechat_article(url)

    if content:
        print(f"\nSuccess!")
        print(f"Content length: {len(content)} chars")
        print(f"\nPreview (first 500 chars):")
        print("="*50)
        print(content[:500])
        print("="*50)

        # 保存到文件
        with open('test_article.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nSaved to: test_article.txt")
    else:
        print("\nFailed")
