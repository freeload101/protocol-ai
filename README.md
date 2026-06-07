# Protocol-AI

**Portable AI Launcher Suite | Skill Markup Library | AI Prompt Engineering Notes**

A central hub for local AI tools, automation scripts, and LLM skill sets.

---

## What's Inside

### SKILLS/

Drop-in skill definitions that shape how AI agents generate code, handle errors, and interact with your system. Each skill is a self-contained ruleset that agents load automatically.

| Skill | Description |
|-------|-------------|
| [agent-powershell-standardizer](SKILLS/agent-powershell-standardizer/) | Forces proper PowerShell patterns no Bash thinking, no aliases, object-oriented pipelines, safe execution, ISE-compatible |

### Coming Soon

- Portable AI launcher scripts for local LLM toolkits
- Prompt engineering templates and patterns
- Automation workflows for agent-driven development

---

## Quick Start

1. Clone this repo into your project or workspace
2. Point your AI agent's skill/rules directory at the `SKILLS/` folder
3. The agent picks up the rules automatically no config needed

Works with Trae, Cursor, Windsurf, Kiro, and any agent that supports skill/steering files.

---

## Philosophy

AI agents are powerful but sloppy. They hallucinate Linux commands on Windows, skip error handling, and ignore encoding. This repo is a growing collection of guardrails that keep agents producing clean, runnable, production-grade output.

Every skill here is:
- Battle-tested against real agent failures
- Designed for Standard User (non-admin) environments
- Portable no hard-coded paths, no assumptions about your setup

---

## Contributing

PRs welcome. If you've caught an agent generating garbage and built a rule to fix it, this is the place for it.

---

## Benchmark Results Summary

    OS: Microsoft Windows 11 Pro
    CPU: 13th Gen Intel(R) Core(TM) i5-13600K
    Motherboard: Micro-Star International Co., Ltd. MPG Z690 FORCE WIFI (MS-7D30)
    RAM: 63.69GB (52GB Available)
    GPU: NVIDIA GeForce RTX 3090 (24GB VRAM)
    Hyper-V/WHPX: Enabled

**Repo Pi-Bench:** https://github.com/kyuz0/pi-bench

**Model:** `llmfan46/Qwen3.6-27B-uncensored-heretic-v2-Native-MTP-Preserved-Q4_K_M.gguf.json`

**Link:** https://huggingface.co/llmfan46/Qwen3.6-27B-uncensored-heretic-v2-Native-MTP-Preserved-GGUF/blob/main/Qwen3.6-27B-uncensored-heretic-v2-Native-MTP-Preserved-Q4_K_M.gguf

**LM Studio JSON: ** `.lmstudio\.internal\user-concrete-model-default-config\llmfan46\Qwen3.6-27B-uncensored-heretic-v2-Native-MTP-Preserved-GGUF\Qwen3.6-27B-uncensored-heretic-v2-Native-MTP-Preserved-Q4_K_M.gguf.json`

    {
      "preset": "",
      "operation": {
        "fields": [
          {
            "key": "llm.prediction.temperature",
            "value": 0
          },
          {
            "key": "llm.prediction.contextOverflowPolicy",
            "value": "rollingWindow"
          },
          {
            "key": "llm.prediction.llama.cpuThreads",
            "value": 10
          }
        ]
      },
      "load": {
        "fields": [
          {
            "key": "llm.load.contextLength",
            "value": 65536
          },
          {
            "key": "llm.load.llama.evalBatchSize",
            "value": 512
          },
          {
            "key": "llm.load.numParallelSessions",
            "value": 1
          },
          {
            "key": "llm.load.llama.vCacheQuantizationType",
            "value": {
              "checked": true,
              "value": "q4_0"
            }
          },
          {
            "key": "llm.load.llama.kCacheQuantizationType",
            "value": {
              "checked": true,
              "value": "q4_0"
            }
          }
        ]
      }
    }


### Overall Score
| Metric | Value |
|---|---|
| **Pass Rate** | **96.00%** (48/50) |
| **Total Duration** | ~6.1 hours (21,875,968 ms) |
| **Avg Duration/Task** | ~7.3 min (437,519 ms) |

### Failed Tasks (2)

| Task | Issue |
|---|---|
| **django__django-12209** | Introduced an undefined variable `meta` (should be `self._meta`) causing a `NameError` at runtime. Also omitted the `not raw and` condition needed for fixture loading with explicit PK values. |
| **django__django-12325** | Modified unrelated files (replacing deprecated `cgi`/`distutils` modules) instead of fixing the actual model inheritance logic in `django/db/models/base.py` and `django/db/models/options.py` to correctly identify the parent link among multiple `OneToOneField`s. |

### Notable Patterns

- **Side-effect habit:** The model consistently replaced the deprecated `cgi` module across many tasks (even when unrelated to the core fix). This was generally harmless but added noise to diffs and occasionally distracted from the actual task (as in `django__django-12325`).
- **Strong test coverage:** Most passing tasks included relevant regression tests alongside the fix.
- **Clean, minimal fixes:** The majority of solutions were targeted and matched or closely approximated the known correct solutions (e.g., `django__django-12262`, `django__django-12276`, `django__django-12155`, `sphinx-doc__sphinx-10323`).

### Pass Rate by Project

| Project | Pass | Fail | Rate |
|---|---|---|---|
| Django | 38 | 2 | 95.0% |
| Sphinx | 10 | 0 | 100% |

Overall, a strong result the two failures stem from a typo/missing condition and a misdirected fix rather than fundamental misunderstanding.

---


