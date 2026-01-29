# 🎧 文章转音频 Skill - 快速开始

## 一键安装

```bash
# 安装依赖
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml

# 检查ffmpeg
ffmpeg -version
```

如果ffmpeg未安装：
- **Windows**: 下载 https://ffmpeg.org/download.html
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

## 使用方法

### 最简单的方式
```bash
python skills/article_to_audio_complete.py 你的文件.xlsx
```

就这么简单！会自动完成：
1. ✅ 抓取文章
2. ✅ 清理内容
3. ✅ 生成配音
4. ✅ 添加BGM

### 其他选项

```bash
# 测试模式（只处理前3篇）
python skills/article_to_audio_complete.py 文件.xlsx --test

# 处理指定范围
python skills/article_to_audio_complete.py 文件.xlsx --range 1-10

# 只生成配音，不添加BGM
python skills/article_to_audio_complete.py 文件.xlsx --no-bgm
```

## Excel文件格式

你的Excel需要包含这些列：
- **序号** - 文章编号
- **图文名称** - 文章标题
- **图文链接** - 微信文章链接

## 输出结果

处理完成后，在 `audio_with_bgm/` 文件夹会得到：
- 22个完整的音频文件
- 格式：MP3（192 kbps高音质）
- 已配音+已混合背景音乐

## 修改设置

编辑 `skills/article_to_audio_complete.py` 中的 `CONFIG` 部分：

```python
CONFIG = {
    'voice': 'zh-CN-XiaoxiaoNeural',  # 换成其他语音
    'bgm_volume': 0.3,               # 调整BGM音量
    'segment_max_chars': 3000,       # 调整分段大小
    # ...更多配置
}
```

## 常用语音

**女声（推荐）**：
- `zh-CN-XiaoxiaoNeural` - 晓晓
- `zh-CN-XiaohanNeural` - 晓涵
- `zh-CN-XiaochenNeural` - 晓晨

**男声**：
- `zh-CN-YunxiNeural` - 云希
- `zh-CN-YunhaoNeural` - 云浩
- `zh-CN-YunjianNeural` - 云健（新闻）

查看完整语音列表：
```bash
python skills/article_to_audio_complete.py 文件.xlsx --voices
```

## 故障排除

**Q: 抓取失败？**
A: 微信有限制，等待几分钟后重试

**Q: TTS失败？**
A: 检查网络连接，Edge TTS需要联网

**Q: BGM混合失败？**
A: 检查ffmpeg是否安装：`ffmpeg -version`

**Q: 想换语音？**
A: 修改CONFIG中的voice参数

---

**就这么简单！一键完成所有工作！** 🚀
