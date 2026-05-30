# Contract Diff

This folder has been upgraded into a **standalone real GUI project**.

Run the project GUI:

```bash
./run_gui.sh
```

Windows:

```powershell
.\run_gui_windows.ps1
```

Default local URL: `http://127.0.0.1:9111`

This project includes its own FastAPI backend, browser GUI, provider settings, local/cloud LLM routing, encrypted API-key storage, file uploads, job history, exports, and a project-specific plugin configuration.

See `PROJECT_IMPLEMENTATION.md` and `project_config.json` for the applied project-specific features and customization controls.

---

## Original README

# contract-diff

> **Two contract versions → semantic diff in plain English.** Shows what actually changed, not just text diffs. Flags new obligations, removed protections, risk level changes. Works on any contract type.

[![PyPI](https://img.shields.io/pypi/v/contract-diff?style=flat)](https://pypi.org/project/contract-diff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quickstart

```bash
pip install contract-diff
python -m contract_diff contract_v1.pdf contract_v2.pdf
python -m contract_diff nda_original.txt nda_revised.txt --json
```

## Example output

```
═══════════════════════════════════════════
  CONTRACT DIFF REPORT
═══════════════════════════════════════════
  📈 RISK INCREASED
  Risk score: 42 → 71/100

  The revised contract adds mandatory arbitration, removes
  the limitation of liability cap, and shortens the termination
  notice period from 90 to 30 days.

  Changes: 8 total | 2 critical | 3 high | 3 medium

  🔴 ➖ Liability cap removed — previously limited to fees paid
     → ❌ Reject

  🟠 ➕ Mandatory arbitration added — waives right to jury trial
     → 🤝 Negotiate

  PROTECTIONS REMOVED FROM V1
  ❌ Liability cap of 12 months fees
  ❌ Right to terminate for convenience with 90 days notice
```

## Supports

PDF and plain text contracts. Works on NDAs, MSAs, employment agreements, SaaS terms, lease agreements — any contract type.

## License
MIT © [Alper Nabil Gabra Zakher](https://github.com/AlperNab)
