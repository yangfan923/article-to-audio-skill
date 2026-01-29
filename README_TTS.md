# Excel文章转音频工具

## 功能说明

自动从Excel读取微信公众号文章链接，抓取正文内容，并转换为语音文件（MP3格式）。

## 环境要求

- Python 3.7+
- 需要的依赖包：
  ```bash
  pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml
  ```

## 使用方法

### 1. 测试模式（处理前3篇）

```bash
python excel_to_audio.py --test
```

### 2. 处理全部文章

```bash
python excel_to_audio.py
```

### 3. 指定Excel文件

```bash
python excel_to_audio.py "你的文件.xlsx"
```

### 4. 查看可用语音

```bash
python excel_to_audio.py --voices
```

## 配置选项

在 `excel_to_audio.py` 的 `CONFIG` 字典中可以修改：

```python
CONFIG = {
    # 使用的语音
    'voice': 'zh-CN-XiaoxiaoNeural',  # 默认女声

    # 单篇文章最大字数
    'max_chars': 10000,  # 超过会截断

    # 是否启用详细日志
    'verbose': True,
}
```

## 常用语音推荐

- **zh-CN-XiaoxiaoNeural** - 女声晓晓（标准，推荐）
- **zh-CN-YunxiNeural** - 男声云希
- **zh-CN-YunjianNeural** - 男声云健（新闻风格）
- **zh-CN-XiaohanNeural** - 女声晓涵
- **zh-CN-YunyangNeural** - 男声扬扬

## 输出结果

处理完成后，音频文件保存在 `audio_output/` 目录：

```
audio_output/
├── 001_独家访谈_何夕_科幻最后战场_何去何从_.mp3
├── 002_深读_实验室到生产线_最后一公里_谁来破_.mp3
├── 003_他们丈量山河_却错过孩子第一声呼唤.mp3
└── ...
```

## 处理流程

1. **读取Excel** - 从Excel文件读取文章信息
2. **抓取文章** - 从微信链接抓取文章正文（跳过图片）
3. **转换语音** - 使用Edge TTS转换为MP3音频
4. **保存文件** - 以序号和标题命名保存

## 注意事项

1. **网络连接** - 需要联网才能抓取文章和使用TTS
2. **文章长度** - 默认单篇文章最多10000字，超过会被截断
3. **处理时间** - 每篇文章需要30-60秒，取决于文章长度
4. **微信限制** - 频繁请求可能被限制，建议分批处理

## 故障排除

### 抓取失败
- 检查网络连接
- 确认微信链接有效
- 部分文章可能有防爬虫保护

### TTS失败
- 检查网络连接
- 尝试更换语音
- 减少单次处理文章数量

## 进阶功能

### 分批处理

将Excel分成多个文件，分别处理：

```bash
python excel_to_audio.py part1.xlsx
python excel_to_audio.py part2.xlsx
```

### 自定义语音

修改脚本中的 `CONFIG['voice']`：

```python
CONFIG = {
    'voice': 'zh-CN-YunxiNeural',  # 改为男声
    ...
}
```

## 示例输出

```
======================================================================
 Excel Article to Audio Converter v1.0
======================================================================

[1/4] Reading Excel: 科协之声-用作转音频.xlsx
  Total articles: 167

[2/4] Output directory: D:\...\audio_output
      Voice: zh-CN-XiaoxiaoNeural
      Max chars per article: 10000

[3/4] Processing articles...
======================================================================

[1/3] Article 1: 独家访谈 | 何夕：科幻"最后战场"，何去何从？...
  URL: https://mp.weixin.qq.com/s/2pCtcZwXlj9jiDXUszqTdQ
  [1/3] Fetching article content...
  [✓] Content length: 3773 chars
  [2/3] Converting to speech (this may take a while)...
  [✓] Audio saved: 001_独家访谈_何夕_科幻最后战场_何去何从_.mp3 (1250.5 KB)
  [3/3] Done!

...

======================================================================
[4/4] SUMMARY
======================================================================
  Total processed: 3
  Successful:      3
  Failed:          0
  Time elapsed:    95.3 seconds
  Output folder:   D:\...\audio_output
======================================================================
```
