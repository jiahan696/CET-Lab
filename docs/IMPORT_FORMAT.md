# 试卷导入格式

程序固定使用 `cet-glass-paper/v1` 模板，完整示例见 [`paper_template.json`](paper_template.json)。导入后 JSON 保存在：

- 开发环境：`data/papers/<paper-id>/paper.json`
- exe：`%APPDATA%\CETGlassLab\papers\<paper-id>\paper.json`

同目录下是 `listening.mp3`（或 `.wav` / `.m4a`）。试卷文件夹可直接复制到另一台电脑。

## 顶层字段

| 字段 | 说明 |
|---|---|
| `schema` | 固定为 `cet-glass-paper/v1` |
| `paper.id` | 唯一 id，建议英文/数字/短横线 |
| `paper.title` | 试卷名称 |
| `paper.level` | `CET-4` 或 `CET-6` |
| `paper.duration_sec` | 总答题秒数，125 分钟 = 7500 |
| `paper.audio` | 音频相对文件名 |
| `writing` | 写作题（prompt、reference_answer、max_score=106.5） |
| `listening.sections[].questions[]` | 听力选择题 |
| `reading.passages[]` | 阅读篇章；`display` 可为 `passage` / `word_bank` / `paragraph_matching` |
| `translation` | 中文原文 + 参考译文，max_score=106.5 |

## 题目字段

```json
{
  "id": "L1",
  "number": 1,
  "type": "single",
  "question": "题干",
  "options": ["A 选项文本", "B 选项文本", "C 选项文本", "D 选项文本"],
  "answers": ["B"],
  "explanation": "中文解析"
}
```

- `type`：`single` 或 `multiple`。
- `answers`：字母数组，例如 `["A"]`、`["A","C"]`。
- 阅读选词填空/段落匹配可使用 `bank`，题目的 `options` 也可使用 `{"key":"A","text":"..."}` 结构。
- 导入时 AI 会尽量补全解析、写作参考与翻译参考。

## 评分

- 写作 106.5 + 听力 248.5 + 阅读 248.5 + 翻译 106.5 = 710。
- 客观题按正确数折算；写作/翻译使用 AI 15 分制评分后折算。
- 听力可为 0 题（部分六级第三套 PDF 明确不提供听力）；此时听力计 0 分，阅读/写作/翻译仍正常计分。
