"""Tkinter desktop interface for SmartMedia-AI."""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path

import config
import pipeline
from downloader import BatchDownloadResult, InputValidationError, download_multiple_from_urls

SOURCE_LANGUAGES = {"自动检测": None, "英语 (en)": "en", "中文 (zh)": "zh"}
TARGET_LANGUAGES = {"中文 (zh)": "zh", "英语 (en)": "en"}
STAGE_LABELS = {
    "download": "下载媒体",
    "import": "导入文件",
    "extraction": "提取音频",
    "transcription": "语音转写",
    "subtitle generation": "翻译并生成字幕",
    "summarization": "生成摘要",
}


def build_options(mode, file, url, source, target, subtitle_format, output_dir):
    if mode not in ("file", "url"):
        raise ValueError("请选择本地文件或 URL。")
    value = (file if mode == "file" else url).strip()
    if not value:
        raise ValueError("请选择媒体文件。" if mode == "file" else "请输入媒体 URL。")
    if not output_dir.strip():
        raise ValueError("请选择输出目录。")
    if source not in SOURCE_LANGUAGES or target not in TARGET_LANGUAGES:
        raise ValueError("请选择支持的语言。")
    if subtitle_format not in pipeline.SUBTITLE_FORMATS:
        raise ValueError("请选择 SRT 或 VTT 格式。")
    return pipeline.PipelineOptions(
        file=value if mode == "file" else None,
        url=value if mode == "url" else None,
        source=SOURCE_LANGUAGES[source],
        target=TARGET_LANGUAGES[target],
        format=subtitle_format,
        output_dir=output_dir.strip(),
    )


class PipelineWorker:
    def __init__(self):
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.thread = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, options):
        if self.running:
            raise RuntimeError("已有任务正在运行。")
        self.cancel_event.clear()
        self.thread = threading.Thread(target=self._run, args=(options,), daemon=False)
        self.thread.start()

    def cancel(self):
        self.cancel_event.set()

    def _run(self, options):
        try:
            outputs = pipeline.run_pipeline(
                options,
                on_progress=lambda stage: self.events.put(("progress", stage)),
                cancel_event=self.cancel_event,
            )
        except pipeline.PipelineCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:
            self.events.put(("error", str(exc)))
        else:
            self.events.put(("success", outputs))


def open_output_directory(path):
    directory = Path(path).resolve()
    if not directory.is_dir():
        raise OSError(f"输出目录不存在：{directory}")
    if sys.platform == "win32":
        os.startfile(str(directory))
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(directory)])


class BatchDownloadWorker:
    def __init__(self):
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.thread = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, urls, output_dir, max_workers):
        if self.running:
            raise RuntimeError("已有下载任务正在运行。")
        self.cancel_event.clear()
        self.thread = threading.Thread(
            target=self._run, args=(urls, output_dir, max_workers), daemon=False
        )
        self.thread.start()

    def cancel(self):
        self.cancel_event.set()

    def _run(self, urls, output_dir, max_workers):
        def progress(index, url, data):
            self.events.put(("progress", index, url, data))

        try:
            results = download_multiple_from_urls(
                urls, output_dir, max_workers, progress, self.cancel_event
            )
        except Exception as exc:
            self.events.put(("error", str(exc)))
        else:
            self.events.put(("complete", results))


class SmartMediaApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText

        self.root = root
        self.worker = PipelineWorker()
        self.batch_worker = BatchDownloadWorker()
        self.busy = False
        self.batch_mode = False
        self.closing = False
        self.output_directory = None
        self.pending_result = None
        root.title("SmartMedia-AI · 字幕与摘要")
        root.geometry("960x760")
        root.minsize(760, 620)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.mode = tk.StringVar(value="file")
        self.file = tk.StringVar()
        self.url = tk.StringVar()
        self.source = tk.StringVar(value="自动检测")
        self.target = tk.StringVar(value="中文 (zh)")
        self.subtitle_format = tk.StringVar(value="srt")
        self.output = tk.StringVar(value=config.OUTPUT_DIR)
        self.status = tk.StringVar(value="就绪：选择文件或输入 URL，然后开始处理。")
        self.operation_mode = tk.StringVar(value="single")
        self.max_workers = tk.IntVar(value=config.MAX_CONCURRENT_DOWNLOADS)
        self.batch_results = []

        container = ttk.Frame(root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(5, weight=1)
        ttk.Label(container, text="SmartMedia-AI", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(container, text="音视频 → 转写 → 双语字幕 → 摘要与关键词").grid(
            row=1, column=0, sticky="w", pady=(0, 12)
        )
        mode_bar = ttk.Frame(container)
        mode_bar.grid(row=2, column=0, sticky="w", pady=(0, 8))
        ttk.Label(mode_bar, text="模式").pack(side="left", padx=(0, 8))
        self.single_mode_radio = ttk.Radiobutton(
            mode_bar, text="单项完整处理", variable=self.operation_mode, value="single",
            command=self._operation_mode_changed,
        )
        self.single_mode_radio.pack(side="left")
        self.batch_mode_radio = ttk.Radiobutton(
            mode_bar, text="批量下载", variable=self.operation_mode, value="batch",
            command=self._operation_mode_changed,
        )
        self.batch_mode_radio.pack(side="left", padx=8)
        inputs = ttk.LabelFrame(container, text="输入与处理选项", padding=12)
        inputs.grid(row=3, column=0, sticky="ew")
        inputs.columnconfigure(1, weight=1)
        self.file_radio = ttk.Radiobutton(inputs, text="本地文件", variable=self.mode,
                                          value="file", command=self._input_states)
        self.file_radio.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.file_entry = ttk.Entry(inputs, textvariable=self.file)
        self.file_entry.grid(row=0, column=1, sticky="ew", pady=4)
        self.file_button = ttk.Button(inputs, text="浏览文件…", command=self.choose_file)
        self.file_button.grid(row=0, column=2, padx=(8, 0))
        self.url_radio = ttk.Radiobutton(inputs, text="媒体 URL", variable=self.mode,
                                         value="url", command=self._input_states)
        self.url_radio.grid(row=1, column=0, sticky="w")
        self.url_entry = ttk.Entry(inputs, textvariable=self.url)
        self.url_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)
        self.batch_label = ttk.Label(inputs, text="批量 URL（每行一个）")
        self.batch_label.grid(row=2, column=0, sticky="nw", pady=4)
        self.batch_urls = ScrolledText(inputs, height=5, wrap="word")
        self.batch_urls.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        self.workers_label = ttk.Label(inputs, text="最大并发数")
        self.workers_label.grid(row=3, column=0, sticky="w", pady=4)
        self.workers_selector = ttk.Spinbox(inputs, from_=1, to=16, width=8,
                                            textvariable=self.max_workers)
        self.workers_selector.grid(row=3, column=1, sticky="w", pady=4)
        ttk.Label(inputs, text="输出目录").grid(row=4, column=0, sticky="w")
        self.output_entry = ttk.Entry(inputs, textvariable=self.output)
        self.output_entry.grid(row=4, column=1, sticky="ew", pady=4)
        self.output_button = ttk.Button(inputs, text="选择目录…", command=self.choose_output)
        self.output_button.grid(row=4, column=2, padx=(8, 0))

        languages = ttk.Frame(inputs)
        languages.grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.selectors = []
        for column, (label, variable, values) in enumerate([
            ("源语言", self.source, tuple(SOURCE_LANGUAGES)),
            ("目标语言", self.target, tuple(TARGET_LANGUAGES)),
            ("字幕格式", self.subtitle_format, pipeline.SUBTITLE_FORMATS),
        ]):
            ttk.Label(languages, text=label).grid(row=0, column=column * 2, padx=(0, 6))
            selector = ttk.Combobox(languages, textvariable=variable, values=values,
                                    state="readonly", width=14)
            selector.grid(row=0, column=column * 2 + 1, padx=(0, 16))
            self.selectors.append(selector)

        actions = ttk.Frame(container)
        actions.grid(row=3, column=0, sticky="ew", pady=12)
        self.start_button = ttk.Button(actions, text="开始处理", command=self.start)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(actions, text="取消", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        self.open_button = ttk.Button(actions, text="打开输出目录", command=self.open_output,
                                       state="disabled")
        self.open_button.pack(side="left")
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=200)
        self.progress.pack(side="right")
        ttk.Label(container, textvariable=self.status, wraplength=880).grid(
            row=4, column=0, sticky="ew", pady=(0, 8)
        )
        self.previews = ttk.Notebook(container)
        self.previews.grid(row=5, column=0, sticky="nsew")
        self.subtitle_preview = ScrolledText(self.previews, wrap="word", state="disabled",
                                            font=("Consolas", 11))
        self.summary_preview = ScrolledText(self.previews, wrap="word", state="disabled",
                                           font=("Segoe UI", 11))
        self.previews.add(self.subtitle_preview, text="双语字幕")
        self.previews.add(self.summary_preview, text="摘要 / 关键词 / 要点")
        self.batch_frame = ttk.LabelFrame(container, text="批量下载结果", padding=8)
        self.batch_frame.grid(row=5, column=0, sticky="nsew")
        self.batch_frame.columnconfigure(0, weight=1)
        self.batch_frame.rowconfigure(0, weight=1)
        self.batch_list = tk.Listbox(self.batch_frame, height=10)
        self.batch_list.grid(row=0, column=0, sticky="nsew")
        self.batch_scrollbar = ttk.Scrollbar(self.batch_frame, orient="vertical",
                                             command=self.batch_list.yview)
        self.batch_scrollbar.grid(row=0, column=1, sticky="ns")
        self.batch_list.configure(yscrollcommand=self.batch_scrollbar.set)
        self.batch_frame.grid_remove()
        self._input_states()
        self._operation_mode_changed()
        root.after(100, self._poll)

    def _operation_mode_changed(self):
        self.batch_mode = self.operation_mode.get() == "batch"
        state = "normal" if self.batch_mode and not self.busy else "disabled"
        for widget in (self.batch_urls, self.workers_selector):
            widget.configure(state=state)
        self.batch_label.configure(state="normal" if self.batch_mode else "disabled")
        self.workers_label.configure(state="normal" if self.batch_mode else "disabled")
        if self.batch_mode:
            self.previews.grid_remove()
            self.batch_frame.grid()
        else:
            self.batch_frame.grid_remove()
            self.previews.grid()
        self._input_states()

    def _input_states(self):
        disabled = self.busy
        mode_disabled = "disabled" if disabled else "normal"
        self.single_mode_radio.configure(state=mode_disabled)
        self.batch_mode_radio.configure(state=mode_disabled)
        for radio in (self.file_radio, self.url_radio):
            radio.configure(state="disabled" if disabled or self.batch_mode else "normal")
        local = self.mode.get() == "file"
        single_disabled = disabled or self.batch_mode
        self.file_entry.configure(state="disabled" if single_disabled or not local else "normal")
        self.file_button.configure(state="disabled" if single_disabled or not local else "normal")
        self.url_entry.configure(state="disabled" if single_disabled or local else "normal")
        for widget in (self.output_entry, self.output_button):
            widget.configure(state="disabled" if disabled else "normal")
        for selector in self.selectors:
            selector.configure(state="disabled" if single_disabled else "readonly")
        batch_state = "disabled" if disabled or not self.batch_mode else "normal"
        self.batch_urls.configure(state=batch_state)
        self.workers_selector.configure(state=batch_state)

    def choose_file(self):
        from tkinter import filedialog
        from downloader import SUPPORTED_EXTENSIONS

        path = filedialog.askopenfilename(
            parent=self.root, title="选择音视频文件",
            filetypes=[("音视频", " ".join("*" + ext for ext in sorted(SUPPORTED_EXTENSIONS))),
                       ("所有文件", "*.*")],
        )
        if path:
            self.file.set(path)

    def choose_output(self):
        from tkinter import filedialog

        path = filedialog.askdirectory(parent=self.root, title="选择输出目录")
        if path:
            self.output.set(path)

    @staticmethod
    def _set_preview(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def start(self):
        if self.busy:
            return
        if self.batch_mode:
            self.start_batch()
            return
        self.start_single()

    def start_single(self):
        from tkinter import messagebox

        try:
            options = build_options(self.mode.get(), self.file.get(), self.url.get(),
                                    self.source.get(), self.target.get(),
                                    self.subtitle_format.get(), self.output.get())
        except ValueError as exc:
            self.status.set(str(exc))
            messagebox.showerror("输入错误", str(exc), parent=self.root)
            return
        self.output_directory = Path(options.output_dir).resolve()
        self.open_button.configure(state="disabled")
        self._set_preview(self.subtitle_preview, "")
        self._set_preview(self.summary_preview, "")
        self.pending_result = None
        self.busy = True
        self._input_states()
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress.start(12)
        self.status.set("开始处理，首次加载本地模型可能较慢…")
        try:
            self.worker.start(options)
        except Exception as exc:
            self._finish("error", str(exc))

    def start_batch(self):
        from tkinter import messagebox

        urls = [line.strip() for line in self.batch_urls.get("1.0", "end").splitlines()
                if line.strip()]
        try:
            if not urls:
                raise ValueError("请至少输入一个 URL（每行一个）。")
            if self.max_workers.get() < 1:
                raise ValueError("最大并发数必须至少为 1。")
            output_dir = self.output.get().strip()
            if not output_dir:
                raise ValueError("请选择输出目录。")
        except (ValueError, tk.TclError) as exc:
            self.status.set(str(exc))
            messagebox.showerror("批量下载输入错误", str(exc), parent=self.root)
            return

        self.output_directory = Path(output_dir).resolve()
        self.batch_results = [None] * len(urls)
        self.batch_list.delete(0, "end")
        for index, url in enumerate(urls):
            self.batch_list.insert("end", f"{index + 1}. 等待中 — {url}")
        self.pending_result = None
        self.busy = True
        self._input_states()
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.open_button.configure(state="disabled")
        self.progress.start(12)
        self.status.set(f"批量下载：{len(urls)} 项，最大并发 {self.max_workers.get()}…")
        try:
            self.batch_worker.start(urls, output_dir, self.max_workers.get())
        except Exception as exc:
            self._finish("error", str(exc))

    def _show_batch_results(self, results):
        from tkinter import messagebox

        self.batch_results = results
        failures = 0
        for index, result in enumerate(results):
            if result.path is not None:
                state = f"完成 — {result.path}"
            elif result.cancelled:
                failures += 1
                state = "已取消"
            else:
                failures += 1
                state = f"失败 — {result.error}"
            self.batch_list.delete(index)
            self.batch_list.insert(index, f"{index + 1}. {state} — {result.url}")
        if failures:
            self.status.set(f"批量下载结束：成功 {len(results) - failures} 项，失败/取消 {failures} 项。")
            errors = "\n".join(
                f"{r.index + 1}. {r.url}: {r.error or '已取消'}"
                for r in results if r.error or r.cancelled
            )
            if errors and not self.closing:
                messagebox.showwarning("部分下载未完成", errors, parent=self.root)
        else:
            self.status.set(f"批量下载完成：{len(results)} 项文件已保存到 {self.output_directory}")

    def cancel(self):
        if self.busy:
            if self.batch_mode:
                self.batch_worker.cancel()
                self.cancel_button.configure(state="disabled")
                self.status.set("正在取消：停止排队任务，并等待已开始的下载收尾。")
            else:
                self.worker.cancel()
                self.cancel_button.configure(state="disabled")
                self.status.set("正在取消：等待当前阶段结束，不再执行后续阶段。")

    def _poll(self):
        worker = self.batch_worker if self.busy and self.batch_mode else self.worker
        while True:
            try:
                event = worker.events.get_nowait()
            except queue.Empty:
                break
            if self.batch_mode and self.busy:
                kind = event[0]
                if kind == "progress":
                    _, index, url, data = event
                    status = data.get("status", "downloading")
                    percent = data.get("_percent_str", "").strip()
                    if status == "finished":
                        text = f"{index + 1}. 后处理中 — {url}"
                    else:
                        text = f"{index + 1}. 下载中 {percent} — {url}"
                    self.batch_list.delete(index)
                    self.batch_list.insert(index, text)
                elif kind == "complete":
                    self.pending_result = ("batch_complete", event[1])
                elif kind == "error":
                    self.pending_result = ("error", event[1])
            else:
                kind, payload = event
                if kind == "progress":
                    if not self.worker.cancel_event.is_set():
                        self.status.set("正在处理：" + STAGE_LABELS.get(payload, payload))
                else:
                    self.pending_result = (kind, payload)
        if self.pending_result is not None and not worker.running:
            result = self.pending_result
            self.pending_result = None
            if result[0] == "batch_complete":
                self._finish_batch(result[1])
            else:
                self._finish(*result)
        if self.closing and not self.busy:
            self.root.destroy()
            return
        self.root.after(100, self._poll)

    def _finish_batch(self, results):
        self.busy = False
        self.progress.stop()
        self._input_states()
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        available = self.output_directory is not None and self.output_directory.is_dir()
        self.open_button.configure(state="normal" if available else "disabled")
        self._show_batch_results(results)

    def _finish(self, kind, payload):
        from tkinter import messagebox

        self.busy = False
        self._input_states()
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        if self.batch_mode:
            self.batch_list.insert("end", f"下载失败：{payload}")
            self.status.set(f"批量下载无法启动：{payload}")
            self.open_button.configure(
                state="normal" if self.output_directory and self.output_directory.is_dir() else "disabled"
            )
            return
        self.progress.stop()
        if kind == "success":
            try:
                subtitles = Path(payload["subtitles"]).read_text(encoding="utf-8")
                summary = Path(payload["summary"]).read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                self.status.set(f"处理完成，但预览读取失败：{exc}")
                if not self.closing:
                    messagebox.showerror("预览失败", str(exc), parent=self.root)
            else:
                self._set_preview(self.subtitle_preview, subtitles)
                self._set_preview(self.summary_preview, summary)
                self.status.set(f"处理完成。输出目录：{self.output_directory}")
        elif kind == "cancelled":
            self.status.set("已取消，已生成的文件和处理日志保留在输出目录。")
        else:
            self.status.set(f"处理失败：{payload}")
            if not self.closing:
                messagebox.showerror("处理失败", payload, parent=self.root)

    def open_output(self):
        from tkinter import messagebox

        if self.output_directory is None:
            return
        try:
            open_output_directory(self.output_directory)
        except OSError as exc:
            self.status.set(f"无法打开输出目录：{exc}")
            messagebox.showerror("打开目录失败", str(exc), parent=self.root)

    def close(self):
        if self.busy:
            self.closing = True
            self.cancel()
        else:
            self.root.destroy()


def main():
    import tkinter as tk

    root = tk.Tk()
    SmartMediaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
