# Session 轨迹文件说明

本目录用于满足审核手册中的“模型轨迹文件”交付要求，包含：

- `codex_session.jsonl`：Codex CLI 导出的原始 session 文件（转换前）
- `openai_messages.json`：将原始 session 转换为审核要求的 OpenAI messages JSON 格式（转换后）
- `../session_trace.json`：同 `openai_messages.json` 的副本（放在项目根目录，便于自动脚本检查）

## 如何重新生成（可选）

如果你有新的 Codex session JSONL，可在项目根目录执行：

```bash
python3 scripts/codex_jsonl_to_openai_messages.py /path/to/rollout-*.jsonl -o session_trace/openai_messages.json
cp session_trace/openai_messages.json session_trace.json
```

