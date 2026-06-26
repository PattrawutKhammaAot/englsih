"""Validate plan.json for duplicate URLs, speaking coverage, and content quality."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "data" / "plan.json"


def video_id(url: str) -> str:
    if not url:
        return ""
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else url


def load_plan() -> list:
    with open(PLAN_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate(plan: list) -> int:
    errors = []
    warnings = []

    dup_days = []
    for d in plan:
        yt_ids = []
        for s in d["segments"]:
            if s.get("replayOf"):
                continue
            vid = video_id(s.get("url", ""))
            if vid and "youtube.com" in s.get("url", ""):
                yt_ids.append(vid)
        if len(yt_ids) != len(set(yt_ids)):
            dup_days.append(d["day"])

    if dup_days:
        errors.append(f"Days with duplicate YouTube URLs: {dup_days[:10]}{'...' if len(dup_days) > 10 else ''} ({len(dup_days)} total)")

    study_days = [d for d in plan if d["type"] == "study"]
    no_speak = [d["day"] for d in study_days if not any(s.get("kind") == "speak" for s in d["segments"])]
    if no_speak:
        errors.append(f"Study days missing speak segment: {no_speak[:10]}")

    # Main lesson repeats within 7 study days
    main_ids_by_study = []
    for d in study_days:
        main = next((s for s in d["segments"] if s.get("kind") == "study"), None)
        if main:
            main_ids_by_study.append((d["day"], video_id(main.get("url", ""))))

    for i in range(len(main_ids_by_study) - 1):
        day_a, vid_a = main_ids_by_study[i]
        for j in range(i + 1, min(i + 8, len(main_ids_by_study))):
            day_b, vid_b = main_ids_by_study[j]
            if vid_a and vid_a == vid_b and day_b - day_a <= 7:
                warnings.append(f"Main lesson repeats within 7 study days: day {day_a} and {day_b}")
                break

    # Speaking minutes per week
    week_speak: dict[int, int] = {}
    for d in plan:
        w = d["week"]
        mins = sum(s["minutes"] for s in d["segments"] if s.get("kind") == "speak")
        week_speak[w] = week_speak.get(w, 0) + mins

    avg_speak = sum(week_speak.values()) / len(week_speak) if week_speak else 0
    if avg_speak < 50:
        warnings.append(f"Average speak minutes/week is low: {avg_speak:.0f}m (target ~60m)")

    # Top repeated URLs
    all_vids = []
    for d in plan:
        for s in d["segments"]:
            vid = video_id(s.get("url", ""))
            if vid and "youtube.com" in s.get("url", ""):
                all_vids.append(vid)
    top = Counter(all_vids).most_common(5)

    print("=== Plan Validation ===")
    print(f"Days: {len(plan)} | Study: {len(study_days)} | Chill: {len(plan) - len(study_days)}")
    print(f"Avg speak min/week: {avg_speak:.0f}")
    print(f"Duplicate URL days: {len(dup_days)}")
    print(f"Top repeated video IDs: {top}")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print("\nValidation FAILED")
        return 1
    print("\nValidation PASSED")
    return 0


def main():
    if not PLAN_PATH.exists():
        print(f"ERROR: {PLAN_PATH} not found")
        return 1
    plan = load_plan()
    return validate(plan)


if __name__ == "__main__":
    sys.exit(main())
