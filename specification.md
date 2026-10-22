# Software Requirements Specification (SRS)
## SmartMedia-AI: An Intelligent Media Extraction, Subtitle Translation and Summarization Toolkit

**Document version**: v1.0
**Date written**: 2026-10-12
**Applicable standard**: Structured with reference to ISO/IEC/IEEE 29148 SRS
**Source document**: `SmartMedia/proposal.md`
**Assignment**: INT6181 Applied Programming with Python — Group Project

---

## Revision History

| Version | Date | Description | Author |
|---|---|---|---|
| v1.0 | 2026-10-12 | Initial version, derived from the approved project proposal | Project Team |

---

## 1. Introduction

### 1.1 Purpose

This document is the software requirements specification for **SmartMedia-AI**, a Python-based intelligent audio/video processing and content summarization system. It formalizes the ideas presented in the project proposal into a structured, verifiable set of requirements that can drive implementation and be used as an acceptance baseline.

Intended readers of this document:
- The development team (six members, one primary module owner each): as the basis for implementation and module interface agreement
- The course assessor: as the basis for evaluating whether the delivered system meets the proposed scope
- Future contributors: as a reference for extending or maintaining the system after the course

### 1.2 Scope

The system **includes**:
- Acquisition of media via a legal URL download or local file import
- Audio extraction and format conversion using FFmpeg
- AI-based speech transcription with timestamps
- Bilingual subtitle generation (`.srt` / `.vtt`)
- Text summarization and keyword extraction
- A Command-Line Interface (CLI)
- A Graphical User Interface (GUI) that shares the same backend as the CLI
- Error handling and logging across the pipeline
- Automated unit/integration testing and CI/CD via GitHub Actions

The system **excludes**:
- Training a speech-recognition, translation, or summarization model from scratch (pre-trained models/APIs are used instead)
- Downloading or processing media the user does not have legal access/download rights to
- Real-time (live-stream) translation or transcription
- Automatic subtitle embedding/burning into the video file
- Offline local large-language-model deployment
- Multi-threaded/concurrent batch downloading
- Any cloud hosting, multi-user accounts, or server deployment (the system is a locally run desktop/CLI tool for a single operator at a time)

Per the proposal (Section 12), this SRS treats the following as **core** (must-have) requirements: local import/legal download, FFmpeg extraction, AI transcription, bilingual subtitles, summarization, CLI, and unit testing/CI. The following are treated as **extension** (should-have) requirements and are explicitly marked as such throughout Section 3: the GUI, multi-threaded downloading, offline local LLM deployment, real-time multilingual translation, and automatic subtitle embedding. This mirrors the phased-delivery intent of the proposal while still giving the extension features verifiable, testable requirement statements per the group's decision to formalize them now rather than leave them undefined.

### 1.3 Definitions and Acronyms

| Term | Description |
|---|---|
| SRS | Software Requirements Specification |
| CLI | Command-Line Interface |
| GUI | Graphical User Interface |
| ASR | Automatic Speech Recognition (speech-to-text) |
| SRT / VTT | Subtitle file formats (`SubRip Text` / `WebVTT`) |
| Source language | The spoken language in the original media |
| Target language | The language the subtitles/summary are translated into |
| Pipeline | The end-to-end processing chain: Downloader → Media Processor → AI Engine → Subtitle Generator → Summarizer |
| CI/CD | Continuous Integration / Continuous Delivery |

### 1.4 References

- `SmartMedia/proposal.md` (the approved project proposal; primary source of this SRS)
- `SmartMedia-AI An Intelligent Audio/Video Processing and Subtitle Summarization System.docx`
- ISO/IEC/IEEE 29148:2018, *Systems and software engineering — Life cycle processes — Requirements engineering*
- FFmpeg documentation (https://ffmpeg.org/documentation.html)
- yt-dlp documentation (https://github.com/yt-dlp/yt-dlp)

### 1.5 Document Structure Overview

Section 2 gives the overall product description. Section 3 lists the specific functional, non-functional, and interface requirements (core and extension). Section 4 states constraints and assumptions. Section 5 gives the acceptance criteria and evaluation plan. The appendix provides the requirements traceability table.

---

## 2. Overall Description

### 2.1 Product Perspective

SmartMedia-AI is a standalone, modular Python application, not a web service. It is run locally by a single operator at a time, either via a terminal (CLI) or a desktop window (GUI); both interfaces call into the same backend package so that the processing logic is never duplicated. The system orchestrates third-party tools and AI models/APIs (yt-dlp, FFmpeg, an ASR model such as Whisper, a translation service, and a summarization LLM) rather than reimplementing any of that capability itself.

### 2.2 Product Functions

| ID | Feature module | Priority | Summary |
|---|---|---|---|
| F1 | Media acquisition | Core | Download via URL (yt-dlp) or import a local file |
| F2 | Audio extraction & conversion | Core | Use FFmpeg to extract/convert audio to a format suitable for ASR |
| F3 | Speech transcription | Core | Convert speech to timestamped text via an ASR model/API |
| F4 | Bilingual subtitle generation | Core | Produce `.srt`/`.vtt` subtitles combining source and translated text |
| F5 | Summarization & keyword extraction | Core | Produce a summary, main points, and keywords from the transcript |
| F6 | CLI | Core | Command-line argument-driven execution of the full pipeline |
| F7 | Error handling & logging | Core | Graceful handling of failures at every pipeline stage |
| F8 | Testing & CI/CD | Core | Unit/integration tests and automated checks on GitHub Actions |
| F9 | GUI | Extension | A graphical front end sharing the CLI's backend |
| F10 | Multi-threaded downloading | Extension | Concurrent/parallel media downloads |
| F11 | Offline local LLM deployment | Extension | Run summarization/translation without external API calls |
| F12 | Real-time multilingual translation | Extension | Live/streaming translation rather than post-hoc batch translation |
| F13 | Automatic subtitle embedding | Extension | Burn or mux subtitles directly into the output video file |

### 2.3 User Characteristics

A single user role: **the operator** — a person processing meeting recordings, lectures, interviews, or similar audio/video content who has basic command-line or desktop-application familiarity but is not assumed to have expertise in FFmpeg, ASR, or machine translation. The user is responsible for ensuring they have legal rights to download/process the media they supply to the system.

### 2.4 Assumptions and Dependencies

| ID | Assumption / Dependency |
|---|---|
| A1 | The host machine has Python 3.10+ and FFmpeg installed and available on the system PATH |
| A2 | The user supplies valid API keys (for the ASR, translation, and/or summarization services in use) via environment variables or a local, version-control-excluded configuration file |
| A3 | The system has internet access when a cloud ASR/translation/summarization API is used; this is not required when the extension feature "offline local LLM deployment" (F11) is enabled instead |
| A4 | Only media the user has legal rights to download or process is supplied as input; the system does not verify copyright status beyond what the source platform's own access controls enforce |
| A5 | The system processes one media item at a time per run unless the multi-threaded downloading extension (F10) is implemented and enabled |
| A6 | The GUI and CLI share one backend package; a requirement stated for "the system" in Section 3 applies identically regardless of which front end invoked it, unless a requirement explicitly says "CLI only" or "GUI only" |

### 2.5 Constraints

See Section 4.

---

## 3. Specific Requirements

> Requirement ID conventions: `FR-xx` functional requirements, `NFR-xx` non-functional requirements, `IFR-xx` interface requirements. Each requirement is tagged **[Core]** or **[Extension]** per Section 1.2. Every requirement is a single, verifiable statement.

### 3.1 Functional Requirements

#### 3.1.1 Media Acquisition

- **FR-01** [Core] The system shall accept a media URL as input and download the corresponding audio/video file using a downloading tool such as yt-dlp.
- **FR-02** [Core] The system shall accept a local file path as input and use it directly without requiring a download step.
- **FR-03** [Core] The system shall validate the input (URL reachability/format, or local file existence and a supported media extension) before starting the pipeline, and shall reject invalid input with a clear error message rather than proceeding.
- **FR-04** [Core] The system shall allow the user to specify or default an output directory for all generated artifacts (audio, transcript, subtitles, summary, log).
- **FR-05** [Core] The system shall display download progress to the user (percentage or equivalent indicator) while a URL-based download is in progress.
- **FR-06** [Extension] The system shall support downloading multiple media items concurrently (multi-threaded downloading), with a configurable maximum concurrency.

#### 3.1.2 Audio Extraction and Conversion

- **FR-07** [Core] The system shall use FFmpeg to extract the audio track from an input video file.
- **FR-08** [Core] The system shall convert extracted or input audio into at least one of WAV, MP3, or M4A format, as selected or defaulted.
- **FR-09** [Core] The system shall convert audio to the sample rate and channel configuration required by the ASR module (e.g., 16 kHz mono) before transcription.
- **FR-10** [Core] The system shall split an audio file exceeding a configurable duration/size threshold into smaller segments before transcription, and shall reassemble the resulting timestamped transcript into a single continuous timeline.

#### 3.1.3 Speech Transcription

- **FR-11** [Core] The system shall transcribe the prepared audio into text using an ASR model or API (e.g., Whisper).
- **FR-12** [Core] The system shall produce a transcript in which each segment carries a start and end timestamp.
- **FR-13** [Core] The system shall support transcription of English and Chinese speech at minimum.
- **FR-14** [Core] The system shall attempt automatic detection of the spoken (source) language when the user does not explicitly specify one.
- **FR-15** [Core] If transcription fails or returns an empty/unusable result (e.g., silent or corrupted audio), the system shall report the failure to the user and halt the pipeline for that media item rather than producing an empty or garbled downstream output.

#### 3.1.4 Bilingual Subtitle Generation

- **FR-16** [Core] The system shall divide the transcript into subtitle segments according to the transcript's timestamps.
- **FR-17** [Core] The system shall translate each subtitle segment's text from the source language into the user-specified target language.
- **FR-18** [Core] The system shall produce a bilingual subtitle file in which each subtitle entry contains both the original-language line and the translated line, in `.srt` format at minimum.
- **FR-19** [Core] The system shall additionally support exporting subtitles in `.vtt` format when selected by the user.
- **FR-20** [Extension] The system shall support embedding (burning or muxing) the generated subtitles directly into a copy of the output video file.
- **FR-21** [Extension] The system shall support translating and displaying subtitle text with latency suitable for a near-real-time/streaming use case, as distinct from the default post-hoc batch translation of a fully downloaded/transcribed file.

#### 3.1.5 Summarization and Keyword Extraction

- **FR-22** [Core] The system shall generate a concise natural-language summary of the transcript's content.
- **FR-23** [Core] The system shall extract a list of keywords from the transcript.
- **FR-24** [Core] The system shall extract the main points/key ideas from the transcript as a structured list, distinct from the free-text summary.
- **FR-25** [Core] The system shall save the summary, keywords, and main points to a plain-text (or equivalent structured) output file in the output directory.
- **FR-26** [Extension] The system shall optionally divide the summary output into chapters or topic sections aligned with timestamp ranges in the source transcript.
- **FR-27** [Extension] The system shall perform summarization using a locally deployed language model as an alternative to a remote LLM API, selectable via configuration, without requiring network access for this step.

#### 3.1.6 CLI

- **FR-28** [Core] The system shall provide a command-line entry point accepting, at minimum, a media URL or local file path, a source language, and a target language as arguments (e.g., `python main.py --url "<URL>" --source en --target zh`).
- **FR-29** [Core] The CLI shall allow the user to select the subtitle output format among the formats supported by FR-18/FR-19.
- **FR-30** [Core] The CLI shall print progress messages for each pipeline stage (download, extraction, transcription, subtitle generation, summarization) as that stage executes.
- **FR-31** [Core] The CLI shall print the final output file locations (audio, transcript, subtitles, summary, log) upon successful completion.
- **FR-32** [Core] The CLI shall print a distinguishable error message and a non-zero exit code when the pipeline fails at any stage, without raising an unhandled stack trace to the end user.

#### 3.1.7 GUI

- **FR-33** [Extension] The system shall provide a graphical interface offering, at minimum: a URL input field, a local-file selection control, source/target language selection controls, start and cancel buttons, and a progress indicator.
- **FR-34** [Extension] The GUI shall provide a preview of the generated subtitles before the user leaves the application.
- **FR-35** [Extension] The GUI shall provide a preview of the generated summary before the user leaves the application.
- **FR-36** [Extension] The GUI shall provide a control (e.g., a button) that opens the output directory in the operating system's file browser.
- **FR-37** [Extension] The GUI shall invoke the same backend modules used by the CLI (per A6) rather than reimplementing pipeline logic, so that a defect fixed in the backend is fixed for both front ends simultaneously.
- **FR-38** [Extension] The GUI shall allow the user to cancel an in-progress pipeline run, after which no further pipeline stages shall execute for that run.

#### 3.1.8 Error Handling and Logging

- **FR-39** [Core] The system shall catch and report, without crashing the whole process, at least the following failure categories: invalid URL, unsupported media format, download failure, network interruption, FFmpeg execution error, missing dependency, API timeout, invalid API key, and empty/low-quality audio.
- **FR-40** [Core] The system shall write a processing log (including timestamps and the stage reached) to the output directory for every run, whether it succeeds or fails.
- **FR-41** [Core] In the GUI, each failure category in FR-39 shall be surfaced to the user as a status message or dialog box rather than a silent failure or an application crash.

### 3.2 External Interface Requirements

- **IFR-01 Command-line interface**: The system shall expose its CLI via `argparse` or an equivalent library, documented with `--help` output listing all supported arguments.
- **IFR-02 Graphical interface** [Extension]: The GUI shall be implemented using Tkinter, PySide6, Streamlit, or an equivalent Python GUI framework, launched via a dedicated entry point or flag (e.g., `python main.py --gui`).
- **IFR-03 Downloading interface**: The system shall interface with yt-dlp (or an equivalent downloading library) through its documented Python API or CLI invocation, not by scraping or reverse-engineering undocumented endpoints.
- **IFR-04 Media processing interface**: The system shall interface with FFmpeg via subprocess invocation or a binding library such as `ffmpeg-python`.
- **IFR-05 AI service interface**: The system shall interface with the ASR, translation, and summarization capabilities through a documented model/API client (e.g., the Whisper API/library, a translation API, an LLM API), with the specific provider configurable rather than hard-coded.
- **IFR-06 Configuration interface**: The system shall read API keys and other sensitive configuration from environment variables or a local `.env`-style file that is excluded from version control; no API key shall appear in the committed source code.
- **IFR-07 File system interface**: The system shall read input media from, and write all generated artifacts (audio, transcript, subtitle files, summary, log) to, the local file system, using paths that are valid across the operating systems listed in NFR-04.

### 3.3 Non-Functional Requirements

- **NFR-01 Portability**: The system shall run as a standard Python project (not an IDE-specific project) launchable from PyCharm, IntelliJ IDEA with Python support, Visual Studio Code, or a standard OS terminal, using only `requirements.txt` plus a documented `python -m venv` + `pip install` setup.
- **NFR-02 Modularity**: Each pipeline stage (downloading, media processing, AI engine, subtitle generation, summarization) shall be implemented in its own module with a defined interface, such that any one module can be unit-tested and replaced without modifying the others (supports NFR-06 and the team's parallel module ownership).
- **NFR-03 Shared backend**: The GUI and CLI shall invoke one shared backend implementation; no pipeline business logic shall be duplicated between `cli_main.py` and `gui_app.py`.
- **NFR-04 Compatibility**: The system shall run on at least one of Windows, macOS, or Linux with Python 3.10+ and a compatible FFmpeg build installed; OS-specific path handling shall use the Python standard library (e.g., `pathlib`) rather than hard-coded separators.
- **NFR-05 Reliability / graceful degradation**: A failure in any single pipeline stage (per FR-39) shall not corrupt or delete artifacts already successfully produced by prior stages, and shall not leave partial/corrupt output files silently presented as complete.
- **NFR-06 Testability**: Each core module's primary functions (URL validation, file validation, audio-format conversion invocation, subtitle formatting, timestamp conversion, summary-output formatting) shall be callable and testable in isolation via pytest, without requiring a live network connection or a real external API call (achieved via mocking/stubbing where an external service is involved).
- **NFR-07 Security**: No API key or other secret shall be committed to version control; the repository shall include a `.gitignore` entry excluding the local configuration/`.env` file.
- **NFR-08 Maintainability**: The project shall include a `README.md` describing setup, environment-variable configuration, and both CLI and GUI invocation commands, sufficient for a new team member or assessor to run the system without consulting the original authors.
- **NFR-09 CI automation**: Every push/pull request shall trigger a GitHub Actions workflow that installs dependencies, verifies the project imports successfully, and runs the full pytest suite, reporting failures back to the team.

---

## 4. Constraints

| ID | Constraint |
|---|---|
| C1 | Implementation language is Python; media processing must use FFmpeg (not a reimplementation of audio/video codec handling) |
| C2 | The system must not train an ASR, translation, or summarization model from scratch; only pre-trained models/APIs (e.g., Whisper, a translation API, an LLM API) may be used |
| C3 | The system must only download or process media the user has legal rights to access, per the course's ethical/legal requirement (proposal Section 1 and 7) |
| C4 | API keys must never be hard-coded in source files; they must be supplied via environment variables or an excluded local configuration file (ties to IFR-06 and NFR-07) |
| C5 | The CLI must remain fully functional on its own; the GUI (an extension requirement) must not be a hard dependency for the system's core pipeline to run |
| C6 | The project must be developed and delivered as a standard, IDE-agnostic Python project (ties to NFR-01); it must not depend on a specific IDE plugin (including Codex) to execute |
| C7 | Any code generated with the assistance of generative AI tools (e.g., Codex, GitHub Copilot) must be reviewed, modified as needed, and tested by a team member before being merged; its use must be documented transparently if required by the course |
| C8 | The project proposal and related course-design materials are due **26 November**; the implementation driven by this SRS must be feasible within that timeline, which is why Section 1.2 splits requirements into Core (must ship by the deadline) and Extension (ship if time permits) |

---

## 5. Evaluation Plan

### 5.1 Evaluation Objective

To verify that the delivered SmartMedia-AI implementation satisfies all **Core** functional and non-functional requirements in Section 3 (mandatory for acceptance) and to record the status of **Extension** requirements (delivered on a best-effort basis, per Section 1.2 and C8), providing evidence for both the course's code-quality review and the team's own internal milestone tracking.

### 5.2 Evaluation Method: Automated Testing (Unit + Integration) via CI/CD

Following the proposal's testing plan (Section 10), the team shall use **pytest** for unit and integration testing, orchestrated via **GitHub Actions**, covering the following test suites:

| Test suite | Related requirements | Test focus |
|---|---|---|
| T-Input validation | FR-03 | URL format/reachability validation and local file existence/extension validation, for both valid and invalid inputs |
| T-Media download | FR-01, FR-05 | Downloading a legally accessible test media URL succeeds and produces a file; progress callback/indicator is invoked |
| T-Audio extraction/conversion | FR-07, FR-08, FR-09 | FFmpeg invocation extracts audio and produces the expected sample rate/channel/format output, verified against a known test media file |
| T-Audio splitting | FR-10 | An audio file above the configured threshold is split into segments and the reassembled transcript timeline is continuous and correctly ordered |
| T-Transcription | FR-11, FR-12, FR-13, FR-14 | A test audio clip (English and a separate Chinese clip) produces a non-empty, timestamped transcript; language auto-detection returns the expected language for each clip |
| T-Transcription failure handling | FR-15 | A silent/corrupted audio input causes the pipeline to halt with a reported failure rather than silently continuing |
| T-Subtitle segmentation | FR-16 | Transcript segments map to subtitle entries with correct timestamp boundaries |
| T-Subtitle translation | FR-17, FR-18, FR-19 | A sample transcript produces a bilingual `.srt` file (and `.vtt` when requested) with both original and translated lines present per entry |
| T-Summarization | FR-22, FR-23, FR-24, FR-25 | A sample transcript produces a non-empty summary, keyword list, and main-points list, written to the expected output file |
| T-CLI argument parsing | FR-28, FR-29 | The CLI accepts the documented arguments and rejects/explains missing or malformed ones |
| T-CLI error reporting | FR-32 | A simulated pipeline failure at each stage produces a clear CLI error message and a non-zero exit code |
| T-Error handling coverage | FR-39, FR-40 | Each failure category listed in FR-39 is independently simulated (e.g., via mocking) and results in a logged, non-crashing failure |
| T-GUI shared backend [Extension] | FR-33, FR-37 | GUI-triggered and CLI-triggered runs of the same input produce identical pipeline output, confirming no logic duplication |
| Integration test | all Core FR | The full pipeline (Downloader → Media Processor → AI Engine → Subtitle Generator → Summarizer) run end-to-end on one legally accessible sample video produces all expected output artifacts |

**CI pipeline**: On every push/pull request, GitHub Actions shall (1) install dependencies from `requirements.txt`, (2) verify the project imports without error, (3) run the full pytest suite, and (4) report any failures to the team (NFR-09).

### 5.3 Requirements-to-Test Traceability (sample excerpt; full table in Appendix A)

| Requirement ID | Test case / test function | Status |
|---|---|---|
| FR-03 | `test_validate_url_and_file_input` | To be implemented |
| FR-09 | `test_audio_converted_to_asr_format` | To be implemented |
| FR-15 | `test_transcription_failure_halts_pipeline` | To be implemented |
| FR-18 | `test_bilingual_srt_output` | To be implemented |
| FR-39 | `test_error_handling_all_categories` | To be implemented |

### 5.4 Acceptance Criteria

The software is considered to have **passed acceptance for its Core scope** when all of the following hold:
1. Every **Core**-tagged FR / NFR / IFR item in Section 3 has at least one corresponding automated test (or, where automation is impractical, a documented manual walkthrough), and all of them pass;
2. The pytest suite executes via GitHub Actions with no failures and no errors on the main branch;
3. The end-to-end integration test (Section 5.2) succeeds on at least one legally accessible sample media file, producing all expected output artifacts (processed audio, transcript, bilingual subtitle file, summary file, keyword list, processing log);
4. No API key or secret is present in the committed source code (verified by a manual repository scan, per NFR-07);
5. The 15-minute demonstration plan from the proposal (Section 7) can be executed successfully using the delivered CLI (and GUI, if that extension was implemented) without an unhandled crash.

**Extension requirements** (FR-06, FR-20, FR-21, FR-26, FR-27, FR-33–FR-38) are evaluated separately and are **not required** for Core acceptance; each delivered extension requirement shall be recorded in Appendix A with its own test/verification status, consistent with the proposal's phased-delivery approach (Section 12).

---

## Appendix A: Full Requirements Traceability Table (to be completed during the implementation phase)

| Requirement ID | Priority | Requirement summary | Test function / verification | Status |
|---|---|---|---|---|
| FR-01 | Core | Download media via URL | `test_download_via_url` | To be implemented |
| FR-02 | Core | Import local media file | `test_import_local_file` | To be implemented |
| FR-03 | Core | Validate URL/file input | `test_validate_url_and_file_input` | To be implemented |
| FR-04 | Core | Configurable output directory | `test_output_directory_selection` | To be implemented |
| FR-05 | Core | Display download progress | `test_download_progress_indicator` | To be implemented |
| FR-06 | Extension | Multi-threaded downloading | `test_concurrent_downloads`; manual batch-download walkthrough | Implemented — pending verification |
| FR-07 | Core | Extract audio via FFmpeg | `test_ffmpeg_audio_extraction` | To be implemented |
| FR-08 | Core | Convert to WAV/MP3/M4A | `test_audio_format_conversion` | To be implemented |
| FR-09 | Core | Convert to ASR-ready format | `test_audio_converted_to_asr_format` | To be implemented |
| FR-10 | Core | Split long audio & reassemble timeline | `test_audio_split_and_timeline_merge` | To be implemented |
| FR-11 | Core | ASR transcription | `test_asr_transcription` | To be implemented |
| FR-12 | Core | Timestamped transcript | `test_transcript_has_timestamps` | To be implemented |
| FR-13 | Core | English/Chinese support | `test_transcription_en_zh` | To be implemented |
| FR-14 | Core | Auto language detection | `test_auto_language_detection` | To be implemented |
| FR-15 | Core | Transcription failure handling | `test_transcription_failure_halts_pipeline` | To be implemented |
| FR-16 | Core | Timestamp-based subtitle segmentation | `test_subtitle_segmentation` | To be implemented |
| FR-17 | Core | Subtitle text translation | `test_subtitle_translation` | To be implemented |
| FR-18 | Core | Bilingual .srt output | `test_bilingual_srt_output` | To be implemented |
| FR-19 | Core | .vtt output support | `test_vtt_output` | To be implemented |
| FR-20 | Extension | Subtitle embedding into video | `test_subtitle_embedding` | To be implemented |
| FR-21 | Extension | Near-real-time translation | `test_realtime_translation_latency` | To be implemented |
| FR-22 | Core | Generate summary | `test_summary_generation` | To be implemented |
| FR-23 | Core | Keyword extraction | `test_keyword_extraction` | To be implemented |
| FR-24 | Core | Main points extraction | `test_main_points_extraction` | To be implemented |
| FR-25 | Core | Save summary output file | `test_summary_output_file` | To be implemented |
| FR-26 | Extension | Chapter/topic division | `test_chapter_division` | To be implemented |
| FR-27 | Extension | Offline local LLM summarization | `test_offline_llm_summarization` | To be implemented |
| FR-28 | Core | CLI argument parsing | `test_cli_argument_parsing` | To be implemented |
| FR-29 | Core | CLI subtitle format selection | `test_cli_format_selection` | To be implemented |
| FR-30 | Core | CLI progress messages | Manual walkthrough | To be implemented |
| FR-31 | Core | CLI prints output locations | `test_cli_prints_output_paths` | To be implemented |
| FR-32 | Core | CLI error reporting & exit code | `test_cli_error_exit_code` | To be implemented |
| FR-33 | Extension | GUI core controls | Manual walkthrough | To be implemented |
| FR-34 | Extension | GUI subtitle preview | Manual walkthrough | To be implemented |
| FR-35 | Extension | GUI summary preview | Manual walkthrough | To be implemented |
| FR-36 | Extension | GUI open-output-folder control | Manual walkthrough | To be implemented |
| FR-37 | Extension | GUI shares CLI backend | `test_gui_cli_backend_parity` | To be implemented |
| FR-38 | Extension | GUI cancel in-progress run | Manual walkthrough | To be implemented |
| FR-39 | Core | Error handling for all failure categories | `test_error_handling_all_categories` | To be implemented |
| FR-40 | Core | Processing log written per run | `test_processing_log_written` | To be implemented |
| FR-41 | Core | GUI surfaces errors to user | Manual walkthrough | To be implemented |

---

*This document is the initial v1.0 version, derived from the project proposal and intended to guide implementation by the six-member team (or an AI coding agent fed this specification). If any requirement ambiguity or conflict with the proposal is discovered during implementation, this document should be revised first — and the change communicated to the whole team — before continuing, so as to maintain consistency (traceability) between the requirements, the proposal, and the code.*
