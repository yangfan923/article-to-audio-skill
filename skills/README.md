# 🎧 文章转音频 Skill

将Excel中的文章列表一键转换为专业配音音频（带背景音乐）

## ⚡ 快速开始

```bash
# 1. 安装依赖
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml

# 2. 准备Excel和背景音乐
#    - Excel包含：序号、图文名称、图文链接
#    - 背景音乐放入：素材/ 文件夹

# 3. 一键转换
python skills/article_to_audio_complete.py 你的文件.xlsx
```

**就这么简单！** 🚀

---

## 📋 功能特性

### ✨ 核心功能
- ✅ 自动抓取微信文章正文
- ✅ 彻底清理元数据（责编、审核、访谈手记等）
- ✅ 高质量AI配音（Edge TTS，22种语音可选）
- ✅ 智能分段（长文章自动分段+无缝合并）
- ✅ 背景音乐混合（30%音量，自动循环）
- ✅ 批量处理（支持数百篇文章）

### 🎯 智能清理
自动删除所有非正文内容：
- ❌ 责编、审核、策划、编辑
- ❌ 访谈作者、值班编委
- ❌ 访谈手记、文中观点
- ❌ 来源、转载声明、微信公众号
- ❌ 投稿邮箱、特别鸣谢
- ❌ 口述、素材等末尾关键词

### 🎵 音频特点
- **音质**：192 kbps 高保真
- **语音**：22种中文语音可选
- **BGM**：随机选择，自动循环
- **渐出**：结尾3秒自然过渡
- **音量**：配音100%，BGM 30%

---

## 📖 使用文档

### 基础用法

```bash
# 处理所有文章
python skills/article_to_audio_complete.py articles.xlsx

# 测试模式（前3篇）
python skills/article_to_audio_complete.py articles.xlsx --test

# 处理指定范围
python skills/article_to_audio_complete.py articles.xlsx --range 1-10

# 只生成配音，不添加BGM
python skills/article_to_audio_complete.py articles.xlsx --no-bgm
```

### Excel文件格式

| 列名 | 必填 | 说明 |
|------|------|------|
| 序号 | ✅ | 文章编号 |
| 图文名称 | ✅ | 文章标题 |
| 图文链接 | ✅ | 微信文章URL |

### 输出文件

```
audio_output/              # 纯配音
articles_for_review/       # 文章文本
audio_with_bgm/            # 最终成品（配音+BGM）← 使用这些
```

---

## ⚙️ 配置选项

### 修改语音

编辑 `skills/article_to_audio_complete.py` 中的 CONFIG：

```python
CONFIG = {
    # 女声（推荐）
    'voice': 'zh-CN-XiaoxiaoNeural',

    # 男声
    # 'voice': 'zh-CN-YunxiNeural',

    # 其他配置...
}
```

### 可用语音

**女声**（推荐）：
- 晓晓（标准）- `zh-CN-XiaoxiaoNeural`
- 晓涵 - `zh-CN-XiaohanNeural`
- 晓晨 - `zh-CN-XiaochenNeural`

**男声**：
- 云希 - `zh-CN-YunxiNeural`
- 云浩 - `zh-CN-YunhaoNeural`
- 云健（新闻）- `zh-CN-YunjianNeural`

[完整列表](skills/article-to-audio-skill.md#可用语音列表)

### 调整参数

```python
CONFIG = {
    'segment_max_chars': 3000,      # 分段大小
    'bgm_volume': 0.3,               # BGM音量（0.0-1.0）
    'fade_out_duration': 3,          # 渐出时长（秒）
    'delay_between_articles': 5,     # 文章间延迟
    'batch_size': 5,                 # 每批数量
    'delay_between_batches': 30,     # 批次间延迟
}
```

---

## 🛠️ 安装

### 自动安装（推荐）

```bash
# 运行安装脚本
bash skills/install.sh
```

### 手动安装

```bash
# 1. 安装Python包
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml

# 2. 安装ffmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows: 从 https://ffmpeg.org/download.html 下载
```

---

## 📊 处理能力

| 项目 | 能力 |
|------|------|
| 文章数量 | 无限制（已测试22篇） |
| 单篇字数 | 无限制（自动分段） |
| 批量处理 | 支持数百篇 |
| 处理速度 | 约2-3分钟/篇 |
| 音频格式 | MP3 (192 kbps) |

---

## 🎯 使用场景

### 适用场景
✅ 微信公众号文章转配音
✅ 批量内容生产
✅ 播客音频制作
✅ 有声读物生成
✅ 知识分享音频

### 文章类型
- 访谈文章
- 科普文章
- 新闻报道
- 深度解读
- 人物故事

---

## 📂 文件结构

```
skills/
├── article_to_audio_complete.py    # 主脚本
├── article-to-audio-skill.md        # 详细文档
├── QUICK_START.md                   # 快速开始
└── README.md                        # 本文件

素材/                                 # 背景音乐
├── 2.mp3
├── 3.mp3
└── 4.mp3
```

---

## 💡 常见问题

### Q: 如何批量处理多个Excel文件？
A: 分别运行脚本，或合并Excel后统一处理

### Q: 可以只用指定的BGM吗？
A: 可以，将不需要的BGM移出 `素材/` 文件夹

### Q: 能调整BGM音量吗？
A: 可以，修改CONFIG中的 `bgm_volume` 参数（0.0-1.0）

### Q: 能换其他语音吗？
A: 可以，修改CONFIG中的 `voice` 参数

### Q: 长文章会被截断吗？
A: 不会，超过3000字自动分段，生成完整音频

### Q: 微信抓取失败怎么办？
A: 等待几分钟后重试，或检查网络连接

---

## 🎊 成功案例

### 已完成项目
- **项目**: 22篇科协文章转音频
- **结果**: 100%成功，全部带BGM
- **时长**: 约200分钟（3.3小时）
- **音质**: 专业级192 kbps

---

## 📞 技术支持

- **版本**: v1.0
- **创建**: 2025-01-29
- **技术栈**: Python + Edge TTS + ffmpeg

---

## 🚀 立即开始

```bash
# 1. 安装依赖
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml

# 2. 运行脚本
python skills/article_to_audio_complete.py 你的文件.xlsx

# 3. 查看结果
# 音频在 audio_with_bgm/ 文件夹
```

**就这么简单！** ✨

---

**更多帮助**：查看 [QUICK_START.md](skills/QUICK_START.md)
