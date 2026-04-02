# Protocol-AI

**Portable AI Launcher Suite | Skill Markup Library | AI Prompt Engineering Notes**

A central hub for local AI tools, automation scripts, and LLM skill sets.

---

## What's Inside

### SKILLS/

Drop-in skill definitions that shape how AI agents generate code, handle errors, and interact with your system. Each skill is a self-contained ruleset that agents load automatically.

| Skill | Description |
|-------|-------------|
| [agent-powershell-standardizer](SKILLS/agent-powershell-standardizer/) | Forces proper PowerShell patterns — no Bash thinking, no aliases, object-oriented pipelines, safe execution, ISE-compatible |

### Coming Soon

- Portable AI launcher scripts for local LLM toolkits
- Prompt engineering templates and patterns
- Automation workflows for agent-driven development

---

## Quick Start

1. Clone this repo into your project or workspace
2. Point your AI agent's skill/rules directory at the `SKILLS/` folder
3. The agent picks up the rules automatically — no config needed

Works with Trae, Cursor, Windsurf, Kiro, and any agent that supports skill/steering files.

---

## Philosophy

AI agents are powerful but sloppy. They hallucinate Linux commands on Windows, skip error handling, and ignore encoding. This repo is a growing collection of guardrails that keep agents producing clean, runnable, production-grade output.

Every skill here is:
- Battle-tested against real agent failures
- Designed for Standard User (non-admin) environments
- Portable — no hard-coded paths, no assumptions about your setup

---

## Contributing

PRs welcome. If you've caught an agent generating garbage and built a rule to fix it, this is the place for it.

---

## License

MIT — see individual skill folders for attribution.
