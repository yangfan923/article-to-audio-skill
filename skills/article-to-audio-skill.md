# Article to Audio Converter Skill

将Excel中的文章列表转换为配音音频（带背景音乐）

## 功能

1. 从Excel读取文章信息（标题、链接等）
2. 抓取微信文章正文内容
3. 彻底清理元数据（责编、审核、访谈手记等）
4. 生成高质量配音（Edge TTS）
5. 添加背景音乐（30%音量，自动循环）
6. 输出完整音频文件

## 使用方法

### 准备工作

1. 准备Excel文件，包含列：
   - 序号
   - 图文名称（文章标题）
   - 图文链接（微信文章URL）
   
2. 准备背景音乐文件（MP3格式），放在 `素材/` 文件夹

### 命令使用

```bash
# 完整流程（推荐）
python skills/article_to_audio_complete.py your_file.xlsx

# 只生成配音（不添加BGM）
python skills/article_to_audio_complete.py your_file.xlsx --no-bgm

# 处理指定范围
python skills/article_to_audio_complete.py your_file.xlsx --range 1-10

# 测试模式（前3篇）
python skills/article_to_audio_complete.py your_file.xlsx --test
```

## 配置选项

在脚本中修改 `CONFIG` 字典：

```python
CONFIG = {
    # TTS语音选择
    'voice': 'zh-CN-XiaoxiaoNeural',  # 女声晓晓（推荐）
    # 'voice': 'zh-CN-YunxiNeural',      # 男声云希
    
    # 文章分段大小（超过此字数自动分段）
    'segment_max_chars': 3000,
    
    # 背景音乐音量（0.0-1.0）
    'bgm_volume': 0.3,  # 30%音量
    
    # 渐出时长（秒）
    'fade_out_duration': 3,
    
    # 处理延迟（避免被限制）
    'delay_between_articles': 5,
    'batch_size': 5,
    'delay_between_batches': 30,
}
```

## 可用语音列表

### 女声
- `zh-CN-XiaoxiaoNeural` - 晓晓（标准，推荐）
- `zh-CN-XiaohanNeural` - 晓涵
- `zh-CN-XiaochenNeural` - 晓晨
- `zh-CN-XiaomengNeural` - 晓梦
- `zh-CN-XiaomoNeural` - 晓墨
- `zh-CN-XiaoqiuNeural` - 晓秋
- `zh-CN-XiaoruiNeural` - 晓瑞
- `zh-CN-XiaoshuangNeural` - 晓双（双胞胎）
- `zh-CN-XiaoxuanNeural` - 晓璇
- `zh-CN-XiaoyanNeural` - 晓燕
- `zh-CN-XiaoyouNeural` - 晓悠（儿童）
- `zh-CN-XiaozhenNeural` - 晓榛

### 男声
- `zh-CN-YunxiNeural` - 云希
- `zh-CN-YunjianNeural` - 云健（新闻风格）
- `zh-CN-YunhaoNeural` - 云浩
- `zh-CN-YunjieNeural` - 云杰
- `zh-CN-YunxiaNeural` - 云霞
- `zh-CN-YunyangNeural` - 扬扬
- `zh-CN-YunfengNeural` - 云峰（讲故事）
- `zh-CN-YunzeNeural` - 云泽

## 输出文件

### 文件结构
```
audio_output/              # 纯配音
articles_for_review/       # 文章文本
audio_with_bgm/            # 最终成品（配音+BGM）
```

### 文件命名
- 纯配音：`序号_标题.mp3`
- 带BGM：`序号_标题_with_bgm_音乐编号.mp3`

## 自动清理的内容

以下内容会自动从文章中删除：

### 人员信息
- 责编：xxx
- 审核：xxx
- 策划：xxx
- 访谈作者：xxx
- 值班编委：xxx
- 编辑：xxx
- 口述：xxx
- 监制：xxx
- 出品：xxx
- 执行：xxx

### 声明信息
- 来源：xxx
- 转载请注明
- 微信公众号
- 投稿邮箱
- 欢迎您的来稿
- 特别鸣谢

### 其他内容
- 访谈手记
- 文中观点
- 相关阅读推荐
- 素材（末尾单字）

## 系统要求

### 必需软件
- Python 3.7+
- ffmpeg（音频处理）

### Python包
```bash
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml
```

### 安装ffmpeg
- **Windows**: 下载并添加到PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

## 处理能力

### 文章长度
- 短文章（<3000字）：直接生成
- 长文章（>3000字）：自动分段+合并
- 最长支持：无限制（自动分段）

### 批量处理
- 支持大批量处理（数百篇）
- 自动延迟避免被限制
- 失败重试机制

## 故障排除

### 常见问题

**Q: 抓取文章失败？**
A: 微信有反爬虫限制，已添加延迟机制。如仍失败，等待几分钟后重试。

**Q: TTS生成失败？**
A: 检查网络连接，Edge TTS需要联网。确保没有防火墙限制。

**Q: BGM混合失败？**
A: 检查ffmpeg是否正确安装：`ffmpeg -version`

**Q: 音频有杂音？**
A: 检查网络质量，重新生成该篇音频。

## 技术支持

- 创建时间：2025-01-29
- 版本：v1.0
- 技术栈：Python + Edge TTS + ffmpeg

---

**快速开始**：
```bash
python skills/article_to_audio_complete.py your_file.xlsx
```
