**Project Proposal**

**SmartMedia-AI: An Intelligent Media Extraction, Subtitle Translation and Summarization Toolkit**

**1. Project Overview**

Our group proposes to develop **SmartMedia-AI**, a Python-based intelligent audio/video processing and content summarization system. The project aims to solve practical problems in cross-border meetings, online education, academic video learning, and multimedia content creation.

At present, users often need to use several different tools to download media, extract audio, convert formats, generate transcripts, translate subtitles, and summarize long videos. This process is time-consuming and technically complicated, especially when the original video does not contain subtitles.

SmartMedia-AI will provide an integrated workflow:

Media downloading → Audio extraction → Speech transcription → Bilingual subtitle generation → Key-point summarization

For example, a user can enter a legal English speech or lecture link. The system will download the media, extract the audio using FFmpeg, generate English and Chinese subtitles, and produce a concise summary of the main content.

The system will support both **Command-Line Interface (CLI)** and **Graphical User Interface (GUI)** modes. The project will be developed using modular Python components so that it can be executed in PyCharm, IntelliJ IDEA, Visual Studio Code, or a standard terminal environment.



**2. Real-World Problem**

The project addresses the following practical problems:

- International meetings may not have complete transcripts or bilingual     records.
- Students may find it difficult to understand foreign-language     lectures and online courses.
- Content creators often need to generate subtitles for videos without     captions.
- Long interviews, speeches, and lectures require a considerable amount     of time to review manually.
- Users usually need multiple independent applications to complete     downloading, conversion, transcription, translation, and summarization.

Unlike a simple video downloader, SmartMedia-AI provides a complete intelligent media-processing workflow. Its main value is not only downloading media, but also transforming unstructured audio/video content into accessible subtitles and useful written information.



**3. Project Objectives**

The objectives of this project are:

1. To design and implement a Python application with CLI and GUI     interaction modes.
2. To support legal downloading or local importing of audio/video files.
3. To use FFmpeg for audio extraction and media format conversion.
4. To use an AI speech-recognition model to convert speech into text.
5. To generate timestamped subtitle files, such as .srt or .vtt.
6. To produce bilingual subtitles, such as English-Chinese subtitles.
7. To extract key points, keywords, and summaries from the transcript.
8. To provide clear error handling for invalid links, missing files,     network interruptions, and API failures.
9. To use unit tests and CI/CD automation to improve code quality.
10. To create a portable project that can run in common Python development     environments.



**4. Main Features**

**4.1 Media Downloading and Local File Import**

Users can either provide a legal media URL or select a local audio/video file. The downloading module will support media retrieval through tools such as yt-dlp, while the local-file mode will allow users to process existing media files.

The system will also include basic file management functions, including:

- Input file validation;
- Output directory selection;
- File naming;
- Media format checking;
- Download progress display;
- Error handling for invalid or unavailable links.

Only media that users have permission to access or download will be used for demonstrations and testing.

**4.2 FFmpeg Audio Extraction and Conversion**

The system will use FFmpeg to process media files. The main functions will include:

- Extracting audio from video;
- Converting audio to WAV, MP3, or M4A;
- Converting audio to a standard format suitable for speech     recognition;
- Adjusting sampling rate and audio channels;
- Splitting long audio files into smaller segments if necessary.

For example, the system may convert an input video into a 16 kHz WAV audio file before sending it to the speech-recognition model.

**4.3 AI Speech Transcription**

The speech-recognition module will use Whisper or another suitable speech-to-text model/API to convert spoken content into text.

The module will aim to support:

- Automatic language detection;
- English and Chinese speech recognition;
- Timestamped transcription;
- Long-audio processing;
- Basic handling of different accents and speaking speeds.

The transcription results will be used by both the subtitle-generation module and the summarization module.

**4.4 Bilingual Subtitle Generation**

Based on the speech transcription and timestamps, the system will generate subtitle files in formats such as .srt or .vtt.

The subtitle workflow will include:

1. Obtaining the original-language transcript;
2. Dividing the transcript according to timestamps;
3. Translating the text into the target language;
4. Combining the original and translated text;
5. Exporting bilingual subtitles.

For example, an English speech may produce subtitles in the following format:

1

00:00:01,000 --> 00:00:04,000

Good morning, everyone.

大家早上好。

**4.5 Text Summarization and Keyword Extraction**

The system will analyze the transcript and generate:

- A concise summary;
- Main ideas;
- Key points;
- Important keywords;
- Optional chapter or topic divisions.

This feature is particularly useful for lectures, meetings, interviews, and long-form online videos.

**4.6 CLI and GUI Interaction**

The project will provide two possible interaction modes.

**CLI Mode**

Example command:

python main.py --url "https://example.com/video" --source en --target zh

The CLI will allow users to:

- Enter a media URL or local file path;
- Select the source and target languages;
- Choose the output format;
- Start the processing workflow;
- View progress messages and errors;
- Locate the generated subtitles and summary.

**GUI Mode**

The GUI may be implemented using Tkinter, PySide6, or another suitable Python framework. It may include:

- URL input box;
- Local-file selection button;
- Language selection menus;
- Start and cancel buttons;
- Progress bar;
- Processing-status display;
- Subtitle preview;
- Summary preview;
- Output-folder button.

The GUI and CLI will share the same backend modules. This means that the core processing logic will not be duplicated, which improves maintainability and demonstrates a clear software architecture.



**5. System Architecture**

The proposed project will use a modular architecture:

SmartMedia-AI/

│

├── main.py

├── cli_main.py

├── gui_app.py

├── downloader.py

├── media_processor.py

├── ai_engine.py

├── summarizer.py

├── subtitle_generator.py

├── config.py

├── utils.py

├── requirements.txt

├── README.md

├── tests/

│  ├── test_downloader.py

│  ├── test_media_processor.py

│  ├── test_subtitle_generator.py

│  └── test_utils.py

└── .github/

  └── workflows/

​    └── tests.yml

**Main Components**

- main.py: Application entry point and mode selection.
- cli_main.py: Command-line argument parsing and CLI workflow.
- gui_app.py: Graphical user interface.
- downloader.py: Media downloading and local-file handling.
- media_processor.py: FFmpeg audio extraction and conversion.
- ai_engine.py: Speech transcription and AI service integration.
- summarizer.py: Summary and keyword extraction.
- subtitle_generator.py: Timestamp processing and bilingual subtitle     output.
- config.py: API keys, language settings, and system configuration.
- tests/: Unit tests and integration tests.



**6. Team Division**

The project will be completed by six members. Each member will take primary responsibility for one module, while all members will participate in integration, debugging, documentation, and the final presentation.

| **Member** | **Main Responsibility**                                      | **Main File or Module**                            |
| ---------- | ------------------------------------------------------------ | -------------------------------------------------- |
| Member A   | System  architecture, project coordination, and CLI workflow | main.py, cli_main.py                               |
| Member B   | GUI design and  user interaction                             | gui_app.py                                         |
| Member C   | Media  downloading and file management                       | downloader.py                                      |
| Member D   | FFmpeg  processing and audio conversion                      | media_processor.py                                 |
| Member E   | AI  transcription, translation, subtitle generation, and summarization | ai_engine.py, subtitle_generator.py, summarizer.py |
| Member F   | Testing,  CI/CD, quality control, and documentation          | tests/, GitHub  Actions, README.md                 |

**Member A: System Architecture and CLI**

Responsibilities include:

- Designing the overall system architecture;
- Defining interfaces between modules;
- Implementing command-line argument parsing;
- Managing the main workflow;
- Coordinating the integration of all modules;
- Tracking project progress and preparing the final demonstration.

**Member B: GUI Development**

Responsibilities include:

- Designing the graphical interface;
- Implementing URL and local-file input;
- Adding language-selection controls;
- Displaying progress and status messages;
- Providing subtitle and summary previews;
- Connecting the GUI to the shared backend.

**Member C: Downloading and File Management**

Responsibilities include:

- Implementing media downloading using yt-dlp or a similar tool;
- Supporting local media-file import;
- Checking URLs and file formats;
- Managing output directories;
- Handling invalid links, unavailable files, and network failures.

**Member D: FFmpeg Media Processing**

Responsibilities include:

- Extracting audio from video;
- Converting audio formats;
- Preparing audio for AI processing;
- Splitting long audio files when necessary;
- Testing different input formats and audio qualities.

**Member E: AI Processing and Content Extraction**

Responsibilities include:

- Integrating Whisper or another speech-recognition model/API;
- Generating timestamped transcripts;
- Translating the transcript;
- Generating bilingual .srt or .vtt subtitles;
- Producing summaries and keywords;
- Evaluating transcription and summarization results.

**Member F: Testing, CI/CD, and Documentation**

Responsibilities include:

- Writing unit tests with pytest;
- Testing normal and abnormal cases;
- Testing failures such as network interruptions and invalid inputs;
- Configuring GitHub Actions for automated testing;
- Preparing the README file and installation guide;
- Supporting final quality control and project documentation.

Although each member has a primary responsibility, the team will jointly participate in debugging, integration testing, code review, documentation, and the final presentation.



**7. Demonstration Plan**

The proposed demonstration will take approximately 15 minutes.

**Demonstration Scenario**

We will use a legally accessible English speech, lecture, or interview without subtitles.

**Demonstration Steps**

1. Open the GUI or run the CLI program.
2. Paste the media URL or select a local video file.
3. Select English as the source language and Chinese as the target     language.
4. Start the processing workflow.
5. Display the download progress.
6. Demonstrate FFmpeg audio extraction.
7. Display the speech-transcription status.
8. Generate bilingual .srt subtitles.
9. Preview the subtitles.
10. Generate and display the key-point summary.
11. Export all results to the output folder.

**Expected Output**

The system will generate:

- Processed audio file;
- Original-language transcript;
- Bilingual .srt or .vtt subtitle file;
- Summary text file;
- Keyword list;
- Processing log.

This demonstration clearly shows that SmartMedia-AI is more than a media downloader. It is an integrated tool for converting audio/video content into subtitles and structured information.



**8. Technologies and Development Tools**

The proposed technologies include:

- **Programming language:** Python
- **Media downloading:** yt-dlp
- **Media processing:** FFmpeg and possibly ffmpeg-python
- **Speech recognition:** Whisper or another suitable speech-recognition     API/model
- **Translation:** Translation API or language model
- **Summarization:** LLM API or local language model
- **CLI:** argparse or Click
- **GUI:** Tkinter, PySide6, or Streamlit
- **Testing:** pytest
- **Version control:** Git and GitHub
- **CI/CD:** GitHub Actions
- **Configuration:** .env and environment variables

API keys will not be hard-coded into the source code. They will be stored through environment variables or a local configuration file that is excluded from version control.



**9. Error Handling and Reliability**

The system will include error handling for:

- Invalid URLs;
- Unsupported media formats;
- Download failures;
- Network interruptions;
- FFmpeg execution errors;
- Missing dependencies;
- API timeouts;
- Invalid API keys;
- Empty or low-quality audio;
- Large files and long processing times.

The CLI will display clear error messages, while the GUI will provide user-friendly status notifications or dialog boxes. The system should fail gracefully instead of terminating unexpectedly.



**10. Testing and CI/CD**

Testing will be conducted at several levels:

**Unit Testing**

Individual functions will be tested separately, including:

- URL validation;
- File validation;
- Audio-format conversion;
- Subtitle formatting;
- Timestamp conversion;
- Summary-output validation.

**Integration Testing**

The team will test whether the modules work together correctly:

Downloader → FFmpeg Processor → AI Engine → Subtitle Generator → Summarizer

**CI/CD**

GitHub Actions will automatically:

1. Install project dependencies;
2. Run unit tests;
3. Check whether the project can be imported successfully;
4. Report test failures to the team.

Generative AI tools such as Codex or GitHub Copilot may be used to assist with code generation, debugging, test writing, and refactoring. All AI-generated code will be reviewed, modified, and tested by team members. The use of AI assistance will be documented transparently in the final report if required by the course.



**11. Compatibility with Codex and Development Environments**

SmartMedia-AI will be designed as a standard Python project rather than an IDE-specific project. Therefore, it can be developed and executed in:

- PyCharm;
- IntelliJ IDEA with Python support;
- Visual Studio Code;
- A standard operating-system terminal.

The project will provide:

- requirements.txt;
- A clear README.md;
- A standard entry point such as main.py;
- Environment-variable instructions;
- Setup and execution commands;
- Optional configuration templates.

Typical installation commands will be:

python -m venv .venv

pip install -r requirements.txt

CLI execution:

python main.py --url "MEDIA_URL" --source en --target zh

GUI execution:

python main.py --gui

The exact commands may be adjusted according to the final implementation. Codex or other AI-assisted programming tools can be used within the supported IDEs, but the application itself will not depend on Codex or any specific IDE plugin to run.



**12. Project Scope and Feasibility**

The core functions will be completed first:

1. Local media import or legal media downloading;
2. FFmpeg audio extraction;
3. AI speech transcription;
4. Bilingual subtitle generation;
5. Text summarization;
6. CLI interface;
7. Unit testing and CI/CD.

The GUI, multi-threaded downloading, offline local LLM deployment, real-time multilingual translation, and automatic subtitle embedding will be treated as extension features. This approach ensures that the project remains achievable while still providing opportunities for advanced functionality.

The project is feasible because:

- Python provides suitable libraries for all major functions;
- Each module can be developed independently;
- The backend can be reused by both CLI and GUI;
- The project can use pre-trained AI models or APIs instead of training     a model from scratch;
- Testing and integration can be performed incrementally.



**13. Expected Outcomes**

At the end of the project, we expect to deliver:

- A functional Python application named SmartMedia-AI;
- CLI and, if time permits, GUI interaction;
- Media downloading or local-file importing;
- FFmpeg-based audio processing;
- AI-generated transcripts;
- Bilingual subtitle files;
- Automated summaries and keyword extraction;
- Error handling and logging;
- Unit tests and GitHub Actions CI/CD;
- User documentation and installation instructions;
- A 15-minute demonstration showing the complete workflow.



**14. Deadline**

The proposal and related course-design materials will be submitted by:

**26 November**



**
**

 

**项目提案**

**SmartMedia-AI****：智能音视频提炼、字幕翻译与摘要生成工具箱**

**1.** **项目概述**

我们小组计划开发一款基于 Python 的智能音视频处理与内容提炼系统，项目名称为 **SmartMedia-AI**。本项目主要面向跨国会议、在线教育、学术视频学习和自媒体内容创作等实际应用场景，旨在解决音视频下载、格式转换、语音转写、字幕翻译和重点提取过程繁琐的问题。

目前，用户通常需要使用多个不同的软件来完成媒体下载、音频提取、格式转换、语音识别、字幕翻译和文本摘要。这种处理方式不仅耗时，也需要用户具备一定的技术知识，尤其是当视频没有自带字幕时，整理和理解视频内容会更加困难。

SmartMedia-AI 将提供以下完整流程：

音视频下载 → 音频提取 → AI 语音转写 → 双语字幕生成 → 重点摘要提炼

例如，用户输入一个合法的英文演讲或课程视频链接，系统即可自动下载媒体文件，使用 FFmpeg 提取音频，通过 AI 模型生成中英双语字幕，并导出视频的核心摘要。

系统将同时支持**命令行界面** **CLI**和**图形用户界面** **GUI**。项目采用模块化 Python 结构，因此可以在 PyCharm、IntelliJ IDEA、Visual Studio Code 或普通终端环境中运行。



**2.** **现实问题与应用价值**

本项目主要解决以下现实问题：

- 跨国会议缺少完整的文字记录或双语记录；
- 学生难以理解外语在线课程和学术演讲；
- 自媒体创作者需要为没有字幕的视频制作字幕；
- 用户需要花费大量时间手动观看长篇访谈、讲座和会议记录；
- 目前通常需要使用多个独立工具完成下载、转换、转写、翻译和摘要。

与普通的“视频下载器”不同，SmartMedia-AI 不仅下载媒体文件，还会将非结构化的音视频内容转换为字幕和文字摘要。因此，它是一个完整的智能音视频内容提炼工具，而不是单纯的下载工具。



**3.** **项目目标**

本项目的主要目标如下：

1. 设计并实现一个支持 CLI 和 GUI 的 Python 应用程序；
2. 支持合法音视频链接下载或本地音视频文件导入；
3. 使用 FFmpeg 完成音频提取和格式转换；
4. 使用 AI 语音识别模型将语音转换为文字；
5. 生成带时间戳的 .srt 或 .vtt 字幕文件；
6. 生成中英双语或其他语言组合的字幕；
7. 从转写文本中提取重点、关键词和摘要；
8. 对无效链接、文件缺失、网络中断和 API 失败等情况进行错误处理；
9. 使用单元测试和 CI/CD 自动化提高代码质量；
10. 创建一个能够在常见 Python 开发环境中运行的独立项目。



**4.** **主要功能**

**4.1** **音视频下载与本地文件导入**

用户可以输入合法的音视频链接，也可以选择本地已有的音视频文件。网络下载模块可以使用 yt-dlp 等工具实现媒体下载，本地文件模式则允许用户直接处理已有文件。

该模块将包括以下功能：

- 输入文件验证；
- 输出目录选择；
- 文件命名管理；
- 媒体格式检查；
- 下载进度显示；
- 无效链接和下载失败处理。

项目演示和测试只使用用户具有访问或下载权限的媒体内容。

**4.2 FFmpeg** **音频提取与格式转换**

系统将使用 FFmpeg 对音视频文件进行处理，主要功能包括：

- 从视频中提取音频；
- 将音频转换为 WAV、MP3 或 M4A 等格式；
- 将音频转换为适合 AI 语音识别的标准格式；
- 调整采样率和声道；
- 必要时将长音频切分成多个片段。

例如，系统可以先将输入视频转换为 16 kHz WAV 文件，再交给语音识别模块进行处理。

**4.3 AI** **语音转写**

语音识别模块将使用 Whisper 或其他合适的语音识别模型/API，把音频内容转换为文字。

该模块计划支持：

- 自动语言识别；
- 中文和英文语音识别；
- 带时间戳的文本转写；
- 长音频处理；
- 对不同口音和语速进行基本处理。

转写结果将同时用于字幕生成和摘要提炼。

**4.4** **双语字幕生成**

系统将根据语音转写结果和时间戳，生成 .srt 或 .vtt 格式的字幕文件。

字幕生成流程如下：

1. 获取原语言语音转写结果；
2. 根据时间戳对文本进行分段；
3. 将文本翻译成目标语言；
4. 将原文和译文进行组合；
5. 导出双语字幕文件。

例如，一段英文演讲可以生成如下字幕：

1

00:00:01,000 --> 00:00:04,000

Good morning, everyone.

大家早上好。

**4.5** **文本摘要与关键词提取**

系统将对转写文本进行分析，并生成：

- 简洁的内容摘要；
- 主要观点；
- 重点信息；
- 关键词；
- 可选的章节或主题划分。

该功能适用于在线课程、会议、访谈、演讲和长篇视频等场景。

**4.6 CLI** **与** **GUI** **交互**

本项目计划提供两种交互方式。

**CLI** **模式**

示例命令：

python main.py --url "https://example.com/video" --source en --target zh

CLI 模式支持用户：

- 输入音视频链接或本地文件路径；
- 选择源语言和目标语言；
- 选择输出格式；
- 启动处理流程；
- 查看进度和错误信息；
- 定位生成的字幕和摘要文件。

**GUI** **模式**

GUI 可以使用 Tkinter、PySide6 或其他合适的 Python 框架开发，主要包括：

- 音视频链接输入框；
- 本地文件选择按钮；
- 语言选择菜单；
- 开始和取消按钮；
- 进度条；
- 处理状态显示；
- 字幕预览；
- 摘要预览；
- 输出文件夹按钮。

CLI 和 GUI 将共享相同的后台业务逻辑。这样可以避免重复编写核心代码，也能体现良好的软件架构设计。



**5.** **系统架构**

项目计划采用模块化结构：

SmartMedia-AI/

│

├── main.py

├── cli_main.py

├── gui_app.py

├── downloader.py

├── media_processor.py

├── ai_engine.py

├── summarizer.py

├── subtitle_generator.py

├── config.py

├── utils.py

├── requirements.txt

├── README.md

├── tests/

│  ├── test_downloader.py

│  ├── test_media_processor.py

│  ├── test_subtitle_generator.py

│  └── test_utils.py

└── .github/

  └── workflows/

​    └── tests.yml

**主要模块**

- main.py：程序入口和运行模式选择；
- cli_main.py：命令行参数解析和 CLI 工作流程；
- gui_app.py：图形用户界面；
- downloader.py：网络下载和本地文件处理；
- media_processor.py：FFmpeg 音频提取和格式转换；
- ai_engine.py：语音转写和 AI 服务调用；
- summarizer.py：文本摘要和关键词提取；
- subtitle_generator.py：时间戳处理和双语字幕导出；
- config.py：API 密钥、语言设置和系统配置；
- tests/：单元测试和集成测试。



**6.** **六人团队分工**

本项目由六名成员共同完成。每位成员主要负责一个模块，同时所有成员都将参与系统整合、调试、文档编写和最终展示。

| **成员** | **主要职责**                  | **负责文件或模块**                                 |
| -------- | ----------------------------- | -------------------------------------------------- |
| 成员 A   | 系统架构、项目协调和 CLI 流程 | main.py、cli_main.py                               |
| 成员 B   | GUI 设计和用户交互            | gui_app.py                                         |
| 成员 C   | 音视频下载和文件管理          | downloader.py                                      |
| 成员 D   | FFmpeg 处理和音频转换         | media_processor.py                                 |
| 成员 E   | AI 转写、翻译、字幕和摘要     | ai_engine.py、subtitle_generator.py、summarizer.py |
| 成员 F   | 测试、CI/CD、质量控制和文档   | tests/、GitHub Actions、README.md                  |

**成员** **A****：系统架构与** **CLI**

主要负责：

- 设计系统整体架构；
- 定义各模块之间的接口；
- 实现命令行参数解析；
- 管理系统主流程；
- 整合所有功能模块；
- 跟进项目进度并准备最终演示。

**成员** **B****：****GUI** **界面开发**

主要负责：

- 设计图形用户界面；
- 实现链接和本地文件输入；
- 添加语言选择功能；
- 显示处理进度和状态信息；
- 提供字幕和摘要预览；
- 将 GUI 连接到共享后台模块。

**成员** **C****：下载与文件管理**

主要负责：

- 使用 yt-dlp 或类似工具实现音视频下载；
- 支持本地媒体文件导入；
- 检查链接和文件格式；
- 管理输出文件夹；
- 处理无效链接、文件不存在和网络中断等问题。

**成员** **D****：****FFmpeg** **音视频处理**

主要负责：

- 从视频中提取音频；
- 转换音频格式；
- 准备适合 AI 处理的音频文件；
- 必要时切分长音频；
- 测试不同媒体格式和音频质量下的处理效果。

**成员** **E****：****AI** **处理与内容提炼**

主要负责：

- 集成 Whisper 或其他语音识别模型/API；
- 生成带时间戳的文本转写；
- 翻译转写文本；
- 生成双语 .srt 或 .vtt 字幕；
- 生成文本摘要和关键词；
- 评估转写和摘要结果。

**成员** **F****：测试、****CI/CD** **与文档**

主要负责：

- 使用 pytest 编写单元测试；
- 测试正常和异常情况；
- 测试网络中断、无效输入和 API 超时等问题；
- 配置 GitHub Actions 自动化测试；
- 编写 README、安装说明和使用指南；
- 协助完成最终质量控制和项目文档。

虽然每位成员都有主要负责的模块，但所有成员都会共同参与调试、系统整合、集成测试、代码审查、文档编写和最终展示。



**7.** **演示计划**

本项目计划进行约 15 分钟的现场演示。

**演示场景**

选择一个合法可访问、没有字幕的英文演讲、课程或访谈视频。

**演示步骤**

1. 打开 GUI 或运行 CLI 程序；
2. 粘贴音视频链接，或选择本地视频文件；
3. 选择英文作为源语言，中文作为目标语言；
4. 启动处理流程；
5. 显示音视频下载进度；
6. 演示 FFmpeg 音频提取；
7. 显示 AI 语音转写状态；
8. 生成双语 .srt 字幕；
9. 预览字幕内容；
10. 生成并展示视频重点摘要；
11. 将所有结果导出到指定文件夹。

**预期输出**

系统将生成：

- 处理后的音频文件；
- 原语言文字转写；
- 中英双语 .srt 或 .vtt 字幕文件；
- 文本摘要；
- 关键词列表；
- 处理日志。

该演示能够清楚地体现 SmartMedia-AI 不只是一个音视频下载器，而是一套完整的音视频内容提炼工具。



**8.** **技术与开发工具**

本项目计划使用以下技术：

- **编程语言**：Python；
- **音视频下载**：yt-dlp；
- **音视频处理**：FFmpeg 和可选的 ffmpeg-python；
- **语音识别**：Whisper 或其他合适的语音识别模型/API；
- **文本翻译**：翻译 API 或语言模型；
- **文本摘要**：大语言模型 API 或本地语言模型；
- **CLI** **开发**：argparse 或 Click；
- **GUI** **开发**：Tkinter、PySide6 或 Streamlit；
- **测试工具**：pytest；
- **版本控制**：Git 和 GitHub；
- **CI/CD**：GitHub Actions；
- **配置管理**：.env 和环境变量。

API 密钥不会直接写入源代码，而是通过环境变量或本地配置文件进行管理，并将敏感配置排除在版本控制之外。



**9.** **错误处理与系统可靠性**

系统将对以下情况进行错误处理：

- 无效链接；
- 不支持的媒体格式；
- 下载失败；
- 网络中断；
- FFmpeg 执行错误；
- 缺少依赖库；
- API 请求超时；
- API 密钥错误；
- 音频为空或质量过低；
- 文件过大或处理时间过长。

CLI 将显示清晰的错误信息，GUI 则通过状态提示或弹窗提醒用户。系统应尽量优雅地处理错误，而不是因为单个环节失败而直接崩溃。



## 10. 测试与 CI/CD

项目将进行多层次测试。

**单元测试**

分别测试以下功能：

- URL 验证；
- 文件验证；
- 音频格式转换；
- 字幕格式生成；
- 时间戳转换；
- 摘要输出检查。

**集成测试**

测试不同模块之间能否正确配合：

下载模块 → FFmpeg 处理模块 → AI 引擎 → 字幕生成模块 → 摘要模块

**CI/CD** **自动化**

GitHub Actions 将自动执行以下任务：

1. 安装项目依赖；
2. 运行单元测试；
3. 检查项目是否可以正常导入；
4. 报告测试失败信息。

项目可以使用 Codex、GitHub Copilot 等生成式 AI 工具协助代码生成、调试、测试编写和代码重构。但所有 AI 生成的代码都需要经过组员人工审查、修改和测试。如果课程要求说明 AI 使用情况，我们将在最终报告中如实记录相关使用过程。



**11. Codex** **与开发环境兼容性**

SmartMedia-AI 将被设计为一个标准 Python 项目，而不是依赖某个特定 IDE 的项目。因此，项目可以在以下环境中开发和运行：

- PyCharm；
- 支持 Python 的 IntelliJ IDEA；
- Visual Studio Code；
- 普通操作系统终端。

项目将提供：

- requirements.txt；
- 清晰的 README.md；
- 标准程序入口，例如 main.py；
- 环境变量配置说明；
- 安装和运行命令；
- 可选的配置模板。

基本安装命令如下：

python -m venv .venv

pip install -r requirements.txt

运行 CLI：

python main.py --url "MEDIA_URL" --source en --target zh

运行 GUI：

python main.py --gui

具体命令可以根据最终代码结构进行调整。Codex 或其他 AI 辅助编程工具可以在相关 IDE 中协助开发，但系统本身不会依赖 Codex 或某个特定 IDE 插件才能运行。



**12.** **项目范围与可行性**

项目将优先完成以下核心功能：

1. 本地媒体文件导入或合法音视频下载；
2. FFmpeg 音频提取；
3. AI 语音转写；
4. 双语字幕生成；
5. 文本摘要；
6. CLI 交互界面；
7. 单元测试和 CI/CD。

GUI、多线程下载、本地大模型离线部署、实时多语种翻译和字幕自动嵌入视频将作为扩展功能。这样可以确保核心项目能够按时完成，同时保留进一步展示技术深度的空间。

该项目具有可行性的原因包括：

- Python 拥有适合各个功能的成熟库；
- 各模块可以独立开发；
- CLI 和 GUI 可以共享同一套后台逻辑；
- 项目可以直接调用预训练 AI 模型或 API，不需要从零训练模型；
- 测试和系统整合可以分阶段完成。



**13.** **预期成果**

项目完成后，预计将实现：

- 一个可运行的 SmartMedia-AI Python 应用程序；
- CLI 以及在时间允许时实现的 GUI；
- 音视频下载或本地文件导入；
- 基于 FFmpeg 的音频处理；
- AI 自动语音转写；
- 中英双语字幕文件；
- 自动摘要和关键词提取；
- 错误处理和日志记录；
- 单元测试和 GitHub Actions CI/CD；
- 用户文档和安装说明；
- 一个完整的 15 分钟项目演示。



**14.** **截止日期**

项目提案及相关课程设计材料的提交截止日期为：

**11****月****26****日**

 

 