# 🎧 文章转音频工具

> 一键将Excel中的文章列表转换为专业配音音频（带背景音乐）

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)]
[![License](https://img.shields.io/badge/License-MIT-green.svg)]
![Stars](https://img.shields.io/github/stars/yangfan923/article-to-audio-skill?style=social)](https://github.com/yangfan923/article-to-audio-skill)

## ✨ 特性

- 🚀 **一键转换** - 从Excel到完整音频，只需一个命令
- 🧹 **智能清理** - 自动删除责编、审核、访谈手记等元数据
- 🎙️ **AI配音** - 使用Edge TTS生成高质量中文配音
- 🎵 **背景音乐** - 自动混合背景音乐（30%音量，自动循环）
- 📦 **批量处理** - 支持数百篇文章批量转换
- 🔄 **自动分段** - 长文章自动分段+无缝合并

---

## 🎯 快速开始

```bash
# 1. 安装依赖
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml

# 2. 一键转换
python skills/article_to_audio_complete.py 你的文件.xlsx

# 3. 查看结果
# 音频文件在 audio_with_bgm/ 文件夹
```

**就这么简单！** 🎉

---

## 📖 功能说明

### 核心功能

1. **从Excel读取文章列表**
   - 支持标准Excel格式（.xlsx, .xls）
   - 自动提取：序号、标题、链接

2. **抓取微信文章正文**
   - 自动从微信公众号链接抓取正文
   - 智能清理HTML标签和格式

3. **彻底清理元数据**
   - 自动删除：责编、审核、策划、编辑
   - 自动删除：访谈手记、来源声明
   - 自动删除：微信公众号、投稿邮箱
   - 自动删除：口述、素材等末尾关键词

4. **生成高质量配音**
   - 使用Microsoft Edge TTS
   - 22种中文语音可选
   - 自然流畅的AI朗读

5. **添加背景音乐**
   - 随机选择背景音乐
   - 自动循环直到配音结束
   - 结尾3秒渐出效果

6. **批量处理支持**
   - 支持数百篇文章
   - 自动延迟避免被限制
   - 失败重试机制

---

## 📋 要求

### 系统要求
- Python 3.7+
- ffmpeg（音频处理）
- 网络连接（Edge TTS和抓取文章需要）

### Python依赖
```bash
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml
```

### 安装ffmpeg
- **Windows**: 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

---

## 🚀 使用方法

### 基础用法

```bash
# 处理所有文章
python skills/article_to_audio_complete.py 你的文件.xlsx
```

### 高级选项

```bash
# 测试模式（只处理前3篇）
python skills/article_to_audio_complete.py 你的文件.xlsx --test

# 处理指定范围
python skills/article_to_audio_complete.py 你的文件.xlsx --range 1-10

# 只生成配音，不添加BGM
python skills/article_to_audio_complete.py 你的文件.xlsx --no-bgm
```

---

## 📂 Excel文件格式

你的Excel需要包含以下列：

| 列名 | 必填 | 说明 |
|------|:----:|:------|
| 序号 | ✅ | 文章编号 |
| 图文名称 | ✅ | 文章标题 |
| 图文链接 | ✅ | 微信文章URL |

### Excel示例

```
| 序号 | 图文名称 | 图文链接 |
|------|----------|----------|
| 1 | 独家访谈 | https://mp.weixin.qq.com/s/xxxxx |
| 2 | 深读文章 | https://mp.weixin.qq.com/s/yyyyy |
```

---

## 🎵 输出文件

### 文件结构

```
audio_output/              # 纯配音
articles_for_review/       # 文章文本
audio_with_bgm/            # 最终成品（配音+BGM）← 使用这些
```

### 文件命名格式

- 纯配音：`序号_标题.mp3`
- 带BGM：`序号_标题_with_bgm_音乐编号.mp3`

### 音频参数

- **格式**：MP3
- **音质**：192 kbps
- **采样率**：24 kHz
- **声道**：单声道
- **配音音量**：100%
- **BGM音量**：30%

---

## ⚙️ 配置选项

编辑 `skills/article_to_audio_complete.py` 中的 `CONFIG` 字典：

```python
CONFIG = {
    # TTS语音选择
    'voice': 'zh-CN-XiaoxiaoNeural',  # 女声晓晓（推荐）

    # 文章分段大小（超过此字数自动分段）
    'segment_max_chars': 3000,

    # 背景音乐音量（0.0-1.0）
    'bgm_volume': 0.3,  # 30%音量

    # 渐出时长（秒）
    'fade_out_duration': 3,

    # 处理延迟
    'delay_between_articles': 5,
    'batch_size': 5,
    'delay_between_batches': 30,
}
```

---

## 🎙️ 可用语音

### 女声（推荐）

| 语音代码 | 名称 | 特点 |
|---------|------|------|
| `zh-CN-XiaoxiaoNeural` | 晓晓 | 标准，自然流畅 |
| `zh-CN-XiaohanNeural` | 晓涵 | 温柔亲切 |
| `zh-CN-XiaochenNeural` | 晓晨 | 清晰明亮 |

### 男声

| 语音代码 | 名称 | 特点 |
|---------|------|------|
| `zh-CN-YunxiNeural` | 云希 | 温和磁性 |
| `zh-CN-YunhaoNeural` | 云浩 | 活力热情 |
| `zh-CN-YunjianNeural` | 云健 | 新闻风格 |

> 💡 **提示**：可在脚本中修改 `voice` 参数切换语音

---

## 📊 处理能力

| 项目 | 能力 |
|------|------|
| 文章数量 | 无限制 |
| 单篇字数 | 无限制（自动分段） |
| 批量处理 | 支持数百篇 |
| 处理速度 | 约2-3分钟/篇 |
| 音频格式 | MP3 (192 kbps) |

---

## 🔧 故障排除

### Q: 抓取文章失败？

**A**: 微信有反爬虫限制
- 等待几分钟后重试
- 检查网络连接
- 确认微信链接有效

### Q: TTS生成失败？

**A**: 检查网络和配置
- Edge TTS需要联网
- 确保没有防火墙限制
- 尝试更换语音

### Q: BGM混合失败？

**A**: 检查ffmpeg安装
```bash
ffmpeg -version
```
- Windows: 下载并添加到PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### Q: 音频有杂音？

**A**: 检查网络质量
- 重新生成该篇音频
- 更换语音试试

---

## 📂 项目结构

```
article-to-audio-skill/
├── skills/                         # 核心脚本
│   ├── article_to_audio_complete.py
│   ├── install.sh
│   ├── README.md
│   └── QUICK_START.md
├── 素材/                            # 背景音乐
├── audio_output/                     # 纯配音
├── articles_for_review/              # 文章文本
└── audio_with_bgm/                   # 最终成品
```

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

## 📝 更新日志

### v1.0 (2025-01-29)

**✨ 首次发布**

- ✅ 微信文章自动抓取
- ✅ 智能元数据清理
- ✅ Edge TTS配音生成
- ✅ 背景音乐混合
- ✅ 批量处理支持
- ✅ 完整文档

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系

- **作者**: yangfan923
- **邮箱**: sifinsho@gmail.com
- **GitHub**: https://github.com/yangfan923/article-to-audio-skill

---

## 🌟 Star History

如果这个项目对你有帮助，请给个 Star ⭐

[![Star History Chart](https://api.star-history.com/repos/yangfan923/article-to-audio-skill?type=star)](https://github.com/yangfan923/article-to-audio-skill/stargazers)

---

**🎉 一键转换，高效便捷！**
