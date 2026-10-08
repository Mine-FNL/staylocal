#!/usr/bin/env python3
"""Score a prediction file against data/test.jsonl. Primary metric is instance accuracy."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def norm(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    text = re.sub(r"\s+", " ", str(value).strip().lower()).replace(",", "")
    return text


def field_ok(gold, pred):
    if isinstance(gold, list):
        return isinstance(pred, list) and len(gold) == len(pred) and all(field_ok(a, b) for a, b in zip(gold, pred))
    if isinstance(gold, dict):
        return isinstance(pred, dict) and all(field_ok(gold[k], pred.get(k)) for k in gold)
    return norm(gold) == norm(pred)


def load_split():
    rows = []
    for line in (ROOT / "data" / "test.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        row["gold"] = json.loads(row["gold"])
        row["evidence"] = json.loads(row["evidence"])
        row["abstain"] = json.loads(row["abstain"])
        rows.append(row)
    return rows


def score_instance(inst, pred):
    pred = pred or {}
    fields = pred.get("fields") or {}
    evidence = pred.get("evidence") or {}
    doc = inst["document"].lower()
    field_hits = field_n = evidence_hits = evidence_n = abstain_hits = abstain_n = 0
    false_answer = False
    for key, gold in inst["gold"].items():
        field_n += 1
        if field_ok(gold, fields.get(key)):
            field_hits += 1
        span = inst["evidence"].get(key)
        if span:
            evidence_n += 1
            if span.lower() in doc and str(evidence.get(key, "")).lower() == span.lower():
                evidence_hits += 1
    for key in inst["abstain"]:
        abstain_n += 1
        if fields.get(key) in (None, "", []):
            abstain_hits += 1
        else:
            false_answer = True
    return {
        "id": inst["instance_id"],
        "subset": inst["subset"],
        "level": inst["level"],
        "correct": field_hits == field_n and evidence_hits == evidence_n and abstain_hits == abstain_n and not false_answer,
        "field_hits": field_hits,
        "field_n": field_n,
        "evidence_hits": evidence_hits,
        "evidence_n": evidence_n,
        "abstain_hits": abstain_hits,
        "abstain_n": abstain_n,
        "false_answer": false_answer,
    }


def aggregate(rows):
    def rate(rs, h, n):
        den = sum(r[n] for r in rs)
        return round(sum(r[h] for r in rs) / den, 4) if den else None
    def block(rs):
        return {
            "n": len(rs),
            "instance_accuracy": round(sum(r["correct"] for r in rs) / len(rs), 4) if rs else None,
            "field_accuracy": rate(rs, "field_hits", "field_n"),
            "evidence_accuracy": rate(rs, "evidence_hits", "evidence_n"),
            "abstention_accuracy": rate(rs, "abstain_hits", "abstain_n"),
            "false_answer_rate": round(sum(r["false_answer"] for r in rs) / len(rs), 4) if rs else None,
        }
    out = {"primary_metric": "instance_accuracy", **block(rows), "by_subset": {}, "by_level": {}}
    for subset in sorted({r["subset"] for r in rows}):
        out["by_subset"][subset] = block([r for r in rows if r["subset"] == subset])
    for level in sorted({r["level"] for r in rows}):
        out["by_level"][level] = block([r for r in rows if r["level"] == level])
    return out


def main():
    data = load_split()
    if len(sys.argv) < 2:
        preds = {r["instance_id"]: {"fields": r["gold"], "evidence": r["evidence"]} for r in data}
        label = "ceiling"
    else:
        preds = json.loads(Path(sys.argv[1]).read_text())
        label = Path(sys.argv[1]).stem
    rows = [score_instance(r, preds.get(r["instance_id"])) for r in data]
    print(json.dumps({"system": label, **aggregate(rows)}, indent=2))


if __name__ == "__main__":
    main()
