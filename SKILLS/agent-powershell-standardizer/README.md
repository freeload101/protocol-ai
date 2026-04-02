# Agent PowerShell Standardizer

A high-reliability PowerShell execution & generation skill for AI agents. Eliminates "Linux-thinking" hallucinations and enforces enterprise-grade PowerShell patterns.

Merged with the **Agentic PowerShell ISE Specialist** for portable, non-admin, ISE-compatible execution.

## What It Does

- Enforces Verb-Noun commands (no `ls`, `cat`, `grep` aliases)
- Object-oriented pipeline thinking over string parsing
- Path safety with `Join-Path`, no hard-coded paths
- Explicit UTF-8 encoding for file I/O
- `-WhatIf` dry-run for all destructive operations
- Structured error handling with typed `ErrorRecord` analysis
- Standard User (non-admin) privilege enforcement
- Portable environment isolation for ISE and locked-down systems
- .NET fallback download for restricted environments

## Usage

Copy the `agent-powershell-standardizer` folder into your agent's skill/rules directory:

- **Trae**: `.trae/skills/`
- **Cursor**: `.cursor/rules/`
- **Windsurf**: `.windsurf/rules/`
- **Kiro**: `.kiro/skills/`

## Credits

- Original skill by [young (hqy2435662352)](https://github.com/hqy2435662352/agent-powershell-standardizer) — MIT License
- ISE Specialist patterns by [freeload101](https://github.com/freeload101)

## License

MIT
