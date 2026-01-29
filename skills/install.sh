#!/bin/bash
# 文章转音频工具 - 安装脚本

echo "================================================"
echo " 文章转音频工具 - 环境检查与安装"
echo "================================================"
echo ""

# 检查Python版本
echo "[1/5] 检查Python版本..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "  当前版本: $python_version"

if ! python -c "import sys" 2>/dev/null; then
    echo "  [!] Python未安装"
    echo "  请先安装Python 3.7或更高版本"
    exit 1
fi
echo "  [OK] Python已安装"
echo ""

# 安装Python包
echo "[2/5] 安装Python依赖包..."
echo "  正在安装: pandas, openpyxl, edge-tts, requests, beautifulsoup4, lxml"
pip install pandas openpyxl edge-tts requests beautifulsoup4 lxml -q
echo "  [OK] Python包安装完成"
echo ""

# 检查ffmpeg
echo "[3/5] 检查ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1)
    echo "  $ffmpeg_version"
    echo "  [OK] ffmpeg已安装"
else
    echo "  [!] ffmpeg未安装"
    echo ""
    echo "  请安装ffmpeg："
    echo "  - macOS:   brew install ffmpeg"
    echo "  - Ubuntu:  sudo apt install ffmpeg"
    echo "  - Windows: 从 https://ffmpeg.org/download.html 下载"
    echo ""
    read -p "  是否继续安装？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ffmpeg
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt update && sudo apt install -y ffmpeg
        else
            echo "  [!] 请手动安装ffmpeg"
            echo "  下载地址: https://ffmpeg.org/download.html"
        fi
    else
        echo "  [!] 跳过ffmpeg安装"
        echo "  [!] 注意：没有ffmpeg，BGM混合功能将无法使用"
    fi
fi
echo ""

# 创建必要的文件夹
echo "[4/5] 创建输出文件夹..."
mkdir -p audio_output
mkdir -p articles_for_review
mkdir -p audio_with_bgm
mkdir -p 素材
echo "  [OK] 文件夹创建完成"
echo ""

# 检查背景音乐
echo "[5/5] 检查背景音乐..."
bgm_count=$(ls -1 素材/*.mp3 2>/dev/null | wc -l)
if [ $bgm_count -eq 0 ]; then
    echo "  [!] 素材/ 文件夹中没有背景音乐"
    echo "  [!] 请将MP3格式的背景音乐放入 素材/ 文件夹"
    echo "  [!] 提示：至少需要1个BGM文件"
else
    echo "  [OK] 找到 $bgm_count 个背景音乐文件"
    ls -lh 素材/*.mp3 | head -3
fi
echo ""

# 总结
echo "================================================"
echo " 环境检查完成！"
echo "================================================"
echo ""
echo "快速开始："
echo "  python skills/article_to_audio_complete.py 你的文件.xlsx"
echo ""
echo "测试模式："
echo "  python skills/article_to_audio_complete.py 你的文件.xlsx --test"
echo ""
echo "更多帮助："
echo "  查看 skills/QUICK_START.md"
echo "================================================"
