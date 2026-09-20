# Personal Codex Rules

## Communication and transparency
- Briefly explain what will be done before each action.
- Do not create summary files, README, or documentation unless explicitly asked by the user.
- Match the user's language in conversation.
- Keep all project-facing artifacts — documentation, code, comments, and UI text — in English for collaboration.

## Code and comments
- Write all visible application UI text in English.
- Write code comments in English.
- Do not add obvious comments; only add them when logic is non-obvious.

## Context and performance
- Warn the user when context is approximately 80% full.
- If a file or symbol is already indexed in jcodemunch, use `mcp__jcodemunch__get_symbol_source`, `mcp__jcodemunch__get_file_content` or `mcp__jcodemunch__search_symbols` before reading files directly.
- Read the full file only if jcodemunch did not return the needed result.

## Project context
- Detailed project context is stored in `CLAUDE.md`; do not copy it entirely into responses or new documents without explicit request.
- This project is not related to AutoDefog; do not bring over solutions, files, or constraints from AutoDefog.
- **CONTEXT.md** is the single structured resume file for quickly restoring context in new sessions. It contains: active task, key decisions, open questions, next steps, relevant files, git state. New sessions must read CONTEXT.md first.
- Before ending a session, update CONTEXT.md: `bash scripts/update-context.sh` (updates timestamp, branch, last commit, test count).
