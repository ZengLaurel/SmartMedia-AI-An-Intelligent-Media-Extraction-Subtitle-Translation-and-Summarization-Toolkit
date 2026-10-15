# SmartMedia-AI

智能音视频处理与字幕摘要工具。详细需求见 `specification.md`，开发顺序见 `roadmap.md`。

## 环境要求

**本项目统一使用 conda 环境 `smart`（Python 3.10），不要用系统/base Python 运行本项目。**

依赖已在该环境安装验证，包括：

- `openai-whisper` 20250625（ASR 语音转写）
- `torch` 2.14（CPU 版）
- `pytest` 9.x
- `python-dotenv`

还需要系统安装 **FFmpeg**（音频提取/转换）并保证其在 PATH 中可用。

## 环境搭建

### 1. 创建/激活 conda 环境

```bash
conda create -n smart python=3.10
conda activate smart
```

如果 `smart` 环境已经存在（本项目开发时使用的环境），直接激活：

```bash
conda activate smart
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 FFmpeg

从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载对应平台的构建版本，解压后将其 `bin` 目录加入系统 PATH。验证：

```bash
ffmpeg -version
ffprobe -version
```

### 4. 配置 API 密钥（可选，视后续功能而定）

复制 `.env.example`（如有）或手动创建 `.env` 文件于项目根目录，内容示例：

```
ASR_API_KEY=
TRANSLATION_API_KEY=
SUMMARIZATION_API_KEY=
OUTPUT_DIR=output
TEMP_DIR=temp
```

`.env` 已被 `.gitignore` 排除，不会被提交到版本库。当前阶段的语音转写使用本地 Whisper 模型，不需要 API 密钥；密钥用于后续接入的翻译/摘要云服务。

## 运行

### CLI

```bash
python main.py --file <本地媒体文件路径>
```

当前支持的媒体扩展名：`.mp4 .mkv .mov .avi .webm .mp3 .wav .m4a`

成功时打印 `File accepted: <path>` 并返回退出码 0；文件不存在或扩展名不支持时打印清晰错误信息并返回非零退出码。

`--url` 参数已占位，URL 下载功能将在后续开发步骤中实现。

## 测试

```bash
pytest tests -v
```

所有外部依赖（FFmpeg 子进程、Whisper 模型）在单元测试中均通过 mock 隔离，无需真实网络连接或真实模型权重即可运行测试套件。

## 项目结构

| 文件 | 职责 |
|---|---|
| `main.py` | 程序入口 |
| `cli_main.py` | 命令行接口 |
| `downloader.py` | 本地文件导入 / URL 下载 |
| `media_processor.py` | FFmpeg 音频提取与格式转换 |
| `ai_engine.py` | 语音转写（ASR）、翻译 |
| `subtitle_generator.py` | 双语字幕生成（.srt / .vtt） |
| `summarizer.py` | 摘要与关键词提取 |
| `config.py` | 环境变量 / API 密钥配置 |
| `utils.py` | 通用工具函数 |
| `tests/` | 单元测试（pytest） |

## 开发进度

详见 `roadmap.md`。当前已完成：

- 阶段 0：仓库脚手架、配置管理、CI
- 阶段 1 第 1 步：本地文件导入校验
- 阶段 1 第 2 步：FFmpeg 音频提取（16kHz 单声道 WAV）
- 阶段 1 第 3 步：语音转写（Whisper，带时间戳，自动语言检测）
