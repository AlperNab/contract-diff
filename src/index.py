#!/usr/bin/env python3
"""
contract-diff — semantic diff between two contract versions
Shows what actually changed in plain English, not just text diffs
Flags: new obligations, removed protections, changed terms, risk level changes
"""
import anthropic
import base64
import json
import re
import sys
from pathlib import Path


SYSTEM = """You are a senior contracts lawyer specializing in contract comparison and risk analysis.

Compare two versions of a contract and identify every meaningful change.
Focus on SUBSTANCE, not formatting. Ignore whitespace, punctuation, and stylistic changes.

Return ONLY valid JSON — no markdown, no explanation.

Format:
{
  "summary": "2-3 sentence overview of what changed and overall risk direction",
  "risk_direction": "increased|decreased|neutral",
  "risk_score_v1": number 0-100,
  "risk_score_v2": number 0-100,
  "changes": [
    {
      "id": "change_1",
      "section": "section name or null",
      "type": "added|removed|modified|strengthened|weakened",
      "severity": "critical|high|medium|low|info",
      "plain_english": "What changed and why it matters",
      "v1_text": "relevant text from version 1 (under 60 words) or null",
      "v2_text": "relevant text from version 2 (under 60 words) or null",
      "favors": "party_a|party_b|neutral",
      "recommendation": "Accept|Negotiate|Reject"
    }
  ],
  "new_obligations": ["list of new things you must do"],
  "removed_protections": ["list of protections removed from v1"],
  "new_rights": ["list of new rights granted in v2"],
  "key_date_changes": ["list of deadline or term changes"],
  "payment_changes": ["list of payment or financial term changes"],
  "statistics": {
    "total_changes": number,
    "critical_changes": number,
    "high_changes": number,
    "medium_changes": number,
    "low_changes": number,
    "changes_favoring_you": number,
    "changes_against_you": number
  }
}"""


def read_doc(path: Path) -> tuple[str, str]:
    """Returns (media_type, data_or_text)"""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        return "pdf", data
    return "text", path.read_text(encoding="utf-8", errors="replace")


def build_content(doc_type: str, data: str, label: str) -> list:
    if doc_type == "pdf":
        return [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}},
            {"type": "text", "text": f"[This is {label}]"}
        ]
    return [{"type": "text", "text": f"[{label}]\n{data[:25000]}"}]


def compare(path_v1: str, path_v2: str) -> dict:
    client = anthropic.Anthropic()
    p1, p2 = Path(path_v1), Path(path_v2)
    if not p1.exists(): raise FileNotFoundError(f"Not found: {path_v1}")
    if not p2.exists(): raise FileNotFoundError(f"Not found: {path_v2}")

    t1, d1 = read_doc(p1)
    t2, d2 = read_doc(p2)

    # Build content blocks
    content = []
    content.extend(build_content(t1, d1, "CONTRACT VERSION 1 (original)"))
    content.append({"type": "text", "text": "\n\n---\n\n"})
    content.extend(build_content(t2, d2, "CONTRACT VERSION 2 (revised)"))
    content.append({"type": "text", "text": "\n\nCompare these two contract versions and identify all meaningful changes."})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
    return json.loads(raw)


SEV_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}
TYPE_ICON = {"added": "➕", "removed": "➖", "modified": "✏️", "strengthened": "💪", "weakened": "⚠️"}

def print_report(result: dict):
    direction = result.get("risk_direction", "neutral")
    dir_icon = {"increased": "📈 RISK INCREASED", "decreased": "📉 RISK DECREASED", "neutral": "➡️  RISK NEUTRAL"}
    stats = result.get("statistics", {})

    print(f"\n{'═'*60}")
    print(f"  CONTRACT DIFF REPORT")
    print(f"{'═'*60}")
    print(f"  {dir_icon.get(direction, direction)}")
    print(f"  Risk score: {result.get('risk_score_v1', '?')} → {result.get('risk_score_v2', '?')}/100")
    print(f"\n  {result.get('summary', '')}")
    print(f"\n  Changes: {stats.get('total_changes', 0)} total | "
          f"{stats.get('critical_changes', 0)} critical | "
          f"{stats.get('high_changes', 0)} high | "
          f"{stats.get('medium_changes', 0)} medium")
    print(f"  Favoring you: {stats.get('changes_favoring_you', 0)} | Against you: {stats.get('changes_against_you', 0)}")

    changes = result.get("changes", [])
    if changes:
        print(f"\n{'─'*60}")
        print(f"  CHANGES")
        print(f"{'─'*60}")
        for c in sorted(changes, key=lambda x: ["critical","high","medium","low","info"].index(x.get("severity","info"))):
            sev = c.get("severity", "info")
            ctype = c.get("type", "modified")
            section = f" [{c.get('section')}]" if c.get("section") else ""
            print(f"\n  {SEV_ICON.get(sev,'•')} {TYPE_ICON.get(ctype,'')} {c.get('plain_english','')}{section}")
            rec = c.get("recommendation", "")
            if rec:
                rec_color = {"Accept": "✅", "Negotiate": "🤝", "Reject": "❌"}.get(rec, "")
                print(f"     → {rec_color} {rec}")
            if c.get("v2_text"):
                print(f"     New text: \"{c['v2_text'][:100]}{'...' if len(c.get('v2_text','')) > 100 else ''}\"")

    new_obs = result.get("new_obligations", [])
    if new_obs:
        print(f"\n{'─'*60}")
        print(f"  NEW OBLIGATIONS FOR YOU")
        for o in new_obs: print(f"  ⚠ {o}")

    removed = result.get("removed_protections", [])
    if removed:
        print(f"\n{'─'*60}")
        print(f"  PROTECTIONS REMOVED FROM V1")
        for r in removed: print(f"  ❌ {r}")

    pay = result.get("payment_changes", [])
    if pay:
        print(f"\n{'─'*60}")
        print(f"  PAYMENT CHANGES")
        for p in pay: print(f"  💰 {p}")

    print(f"\n{'═'*60}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python -m contract_diff <v1.txt|.pdf> <v2.txt|.pdf> [--json]")
        sys.exit(0)

    result = compare(args[0], args[1])

    if "--json" in args:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)
