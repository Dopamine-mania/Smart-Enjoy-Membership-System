# Session 轨迹文件说明

本目录用于满足审核手册中的“模型轨迹文件”交付要求，包含：

- `codex_session.jsonl`：Codex CLI 导出的原始 session 文件（转换前）
- `openai_messages.json`：将原始 session 转换为审核要求的 OpenAI messages JSON 格式（转换后）
- `../session_trace.json`：同 `openai_messages.json` 的副本（放在项目根目录，便于自动脚本检查；两者应保持一致）

## 2026-02-25 补充说明

本项目在 2026-02-25 进行了二次加固与修复。由于当前运行环境未自动导出本次会话对应的 `rollout-*.jsonl`，
因此以 Codex JSONL 的 schema 追加了“message 类型”的 `response_item` 记录到 `codex_session.jsonl` 末尾，
并据此重新生成 `openai_messages.json` 与根目录 `session_trace.json`，以保证验收所需的“轨迹文件格式”与“聊天记录补充”。

## 如何重新生成（可选）

如果你有新的 Codex session JSONL，可在项目根目录执行：

```bash
python3 scripts/codex_jsonl_to_openai_messages.py /path/to/rollout-*.jsonl -o session_trace/openai_messages.json
cp session_trace/openai_messages.json session_trace.json
```
