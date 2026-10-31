# AI Agent 接入说明

应用把 AI 当成一个可选增强层：不配置时，题库、考试、错题、历史、音频与 JSON 导入都仍可用；配置后增加三项能力：

1. **划词/划句翻译**：阅读原文、翻译原文、写作题目、专项材料中选中英文，AI 返回释义/译文，可加入单词本。
2. **写作/翻译评分**：交卷时按 CET 15 分制评分，折算为 106.5 分，并返回反馈、优点、提升建议和修改示例。
3. **试卷导入**：PDF 文本解析 + AI 视觉识别扫描页 + AI 补全解析/参考范文，输出 `cet-glass-paper/v1` 试卷。

## 配置

点击应用顶部「AI」或仪表盘「AI 设置」：

- Base URL：`https://api.deepseek.com/v1`
- 模型：`deepseek-flash`（支持图片输入）
- API Key
- 启用 AI

配置保存在用户数据目录的 `ai_config.json`。也可复制 `docs/ai_config.example.json` 手动填写。

支持任意 OpenAI-compatible `/chat/completions` 服务：DeepSeek、OpenAI、Qwen/DashScope 兼容模式、Moonshot、Ollama 网关等。模型必须支持图片输入才能对扫描版 PDF 做视觉识别；纯文本解析不需要视觉能力。

## 已有方法

`cetapp/ai_agent.py`：

| 方法 | 用途 |
|---|---|
| `chat()` / `chat_json()` | 通用对话与 JSON 解析 |
| `translate_selection(text, context)` | 划词/划句翻译，返回 term/translation/phonetic/pos/example |
| `score_writing(prompt, answer, level, word_limit)` | CET 写作 15 分制评分 |
| `score_translation(prompt, answer, reference, level)` | CET 翻译 15 分制评分 |
| `vision_text(images, prompt)` | 扫描 PDF 页面转写 |
| `explain_question()` | 单题深度讲解 |
| `study_plan(stats)` | 7 天复习计划 |

`cetapp/pdf_import.py`：

- `extract_pdf_text()`
- `parse_cet_text()`（标准 CET 版式）
- `ocr_scanned_pdf()`（AI 视觉识别）
- `extract_answer_key_with_ai()`（答案页仅存在于答案 PDF 时的兜底）
- `build_imported_paper()`（完整导入流程）

## 数据与隐私

- API Key 只保存在本机 `ai_config.json`，不会写入题库或试卷 JSON。
- 只有用户主动触发 AI 翻译、AI 评分或 PDF 导入时，才会把必要的选中文本/作文/译文/PDF 页面发送到所配置的接口。
- 未配置或请求失败时，应用不会崩溃：翻译提示配置，评分记录错误，导入回退到本地解析。
- 建议使用单独的低额度测试 Key，不要提交 `ai_config.json` 到版本库。
