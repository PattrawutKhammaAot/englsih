"""Generate 180-day evening study plan (1 hour/day) with real YouTube URLs.

Week structure: days 1-5 study (60 min, 4 segments), days 6-7 chill.
Listen vs speak pools are separate — no duplicate YouTube URLs within a day.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "plan.json"

PLAYLISTS = {
    "vocab365": "PLcWqwqWwXmGImAja_ln1WVkF_sLAjKIMq",
    "course100": "PLcWqwqWwXmGI1gQHL06cnf6thN_28b8_u",
    "tonamorn_basic": "PLrstMNlAK0Iu3XViE08wFLjyxyRFFhKYl",
    "tonamorn_speak": "PL-mTjxH2S72jUYQJB51HIFPaPrEMOoBKA",
    "adam": "PLBjOnHjDlsB-2X2g-cmwwhv9Mk0AIAd8P",
    "bbc_daily": "PLcetZ6gSk968C_wAbx0wljnY1gJlNtDrT",
}

CHANNELS = {
    "unfox": ("https://www.youtube.com/@unfoxenglish/videos", "UNFOX English"),
    "krudew": ("https://www.youtube.com/@kdenglishofficial/videos", "KruDew English"),
    "vanessa": ("https://www.youtube.com/@SpeakEnglishWithVanessa/videos", "Speak English with Vanessa"),
    "easyenglish": ("https://www.youtube.com/channel/UCZncsrwBf4_j7JWDzhZIuQg/videos", "Easy English"),
    "english101": ("https://www.youtube.com/@EnglishClass101/videos", "EnglishClass101"),
}

VERIFIED_SPEAK = [
    {"id": "DAcNrKXmkYk", "title": "ฝึกพูด 50 ประโยคสนทนาพื้นฐาน", "url": "https://www.youtube.com/watch?v=DAcNrKXmkYk", "channel": "UNFOX English"},
    {"id": "qmq2BblI6qs", "title": "ฝึกพูด 600 ประโยคพื้นฐาน (ใช้ 10 นาทีแรก)", "url": "https://www.youtube.com/watch?v=qmq2BblI6qs", "channel": "ต้นอมร"},
]

CARTOONS = [
    {"title": "Peppa Pig — Muddy Puddles", "url": "https://www.youtube.com/watch?v=G6FpH0kSV18", "channel": "Peppa Pig"},
    {"title": "Bluey — Magic Xylophone", "url": "https://www.youtube.com/watch?v=JkaxUblCGz0", "channel": "Bluey"},
    {"title": "Peppa Pig — Best Friend", "url": "https://www.youtube.com/watch?v=6AZP9de86uc", "channel": "Peppa Pig"},
    {"title": "Bluey — Keepy Uppy", "url": "https://www.youtube.com/watch?v=9tUzzDtDRLk", "channel": "Bluey"},
    {"title": "Peppa Pig — Potato City", "url": "https://www.youtube.com/watch?v=9oR0o8Q0Q4k", "channel": "Peppa Pig"},
    {"title": "Bluey — The Pool", "url": "https://www.youtube.com/watch?v=KqT9Z1qXJZQ", "channel": "Bluey"},
    {"title": "Peppa Pig — Camping", "url": "https://www.youtube.com/watch?v=6gS5w9X8Q4k", "channel": "Peppa Pig"},
    {"title": "Bluey — Bike", "url": "https://www.youtube.com/watch?v=8Qn_spdM5Zg", "channel": "Bluey"},
]

PHASE_META = {
    1: {"name": "ปูพื้นฐาน", "months": "เดือน 1–2", "emoji": "🏗️"},
    2: {"name": "ฟัง + พูดตาม", "months": "เดือน 3–4", "emoji": "🎧"},
    3: {"name": "ใช้จริง", "months": "เดือน 5–6", "emoji": "🚀"},
}

META_KEYWORDS = [
    "chatgpt", "why study", "why self", "mindset", "subscribe", "support",
    "how to improve faster", "proficient in english quickly", "teacher?",
    "avatar:", "youtube ", "promo", "discount", "sale",
]

SPEAK_KEYWORDS = [
    "speak", "speaking", "conversation", "shadow", "pronunciation", "พูด",
    "ฝึกพูด", "สนทนา", "ออกเสียง", "repeat", "listen and repeat",
    "talk", "dialogue", "ประโยค", "phrase", "1-minute", "1 minute",
]

AI_URL = "https://chat.openai.com/"
QUIZLET_URL = "https://quizlet.com/"


def clean_title(title: str) -> str:
    t = title.strip()
    if not t or t in {"!", "(!)"} or len(t) < 4:
        return ""
    return t


def is_usable(title: str) -> bool:
    t = clean_title(title)
    if not t:
        return False
    if t.replace("!", "").replace(" ", "") == "":
        return False
    return True


def video_id(url: str) -> str:
    if not url:
        return ""
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else url


def yt_list(source_url: str, channel: str = "", playlist_id: str = "") -> list[dict]:
    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--flat-playlist", "--print", "%(id)s|%(title)s", source_url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    videos = []
    for line in result.stdout.strip().splitlines():
        if "|" not in line:
            continue
        vid, title = line.split("|", 1)
        vid, title = vid.strip(), clean_title(title)
        if len(vid) != 11 or not is_usable(title):
            continue
        url = f"https://www.youtube.com/watch?v={vid}"
        if playlist_id:
            url += f"&list={playlist_id}&index={len(videos) + 1}"
        videos.append({"id": vid, "title": title, "url": url, "channel": channel})
    return videos


def yt_playlist(playlist_id: str, channel: str = "") -> list[dict]:
    return yt_list(f"https://www.youtube.com/playlist?list={playlist_id}", channel, playlist_id)


def yt_channel(key: str) -> list[dict]:
    url, channel = CHANNELS[key]
    return yt_list(url, channel)


def is_meta_clip(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in META_KEYWORDS)


def is_long_clip(title: str) -> bool:
    t = title.lower()
    bad = ["ชม.", "hour", "600 ", "1000", "challenge course", "21 day", "3:0", "compil", "full course"]
    return any(b in t for b in bad) or len(title) >= 120


def is_listen_clip(title: str) -> bool:
    return is_usable(title) and not is_meta_clip(title) and not is_long_clip(title)


def is_speak_clip(title: str) -> bool:
    if not is_listen_clip(title):
        return False
    t = title.lower()
    return any(k in t for k in SPEAK_KEYWORDS)


def pick(pool: list, n: int, offset: int = 0) -> dict:
    if not pool:
        return {"title": "—", "url": "", "channel": "", "id": ""}
    item = pool[(n - 1 + offset) % len(pool)]
    return {
        "title": item["title"],
        "url": item["url"],
        "channel": item.get("channel", ""),
        "id": item.get("id", video_id(item.get("url", ""))),
    }


def pick_unique(pool: list, n: int, exclude_ids: set, offset: int = 0) -> dict | None:
    if not pool:
        return None
    for i in range(len(pool)):
        item = pool[(n - 1 + offset + i) % len(pool)]
        vid = item.get("id") or video_id(item.get("url", ""))
        if vid and vid not in exclude_ids:
            return {
                "title": item["title"],
                "url": item["url"],
                "channel": item.get("channel", ""),
                "id": vid,
            }
    return None


def pick_vocab(vocab: list, n: int) -> dict:
    idx = min(n, len(vocab) - 1)
    item = vocab[idx]
    return {
        "title": item["title"],
        "url": item["url"],
        "channel": "English by Chris",
        "id": item.get("id", video_id(item["url"])),
    }


def vocab_words(n: int) -> str:
    start = (n - 1) * 10 + 1
    end = n * 10
    return f"คำที่ {start}–{end} (ชุดที่ {n}) — ท่อง + ออกเสียงดัง ๆ ใน Anki/Quizlet"


def seg(
    minutes: int,
    label: str,
    emoji: str,
    title: str,
    kind: str,
    url: str = "",
    channel: str = "",
    note: str = "",
    replay_of: str = "",
) -> dict:
    s = {
        "minutes": minutes,
        "label": label,
        "emoji": emoji,
        "title": title,
        "kind": kind,
        "url": url,
        "channel": channel,
        "note": note,
    }
    if replay_of:
        s["replayOf"] = replay_of
    return s


def build_pools(pools: dict) -> dict:
    vocab = [v for v in pools.get("vocab365", []) if "Day" in v["title"] or "365" in v["title"]]
    if not vocab:
        vocab = pools.get("vocab365", [])[1:]

    course = [v for v in pools.get("course100", []) if "/" in v["title"] or "P:" in v["title"] or "C:" in v["title"] or "S:" in v["title"]]
    if not course:
        course = pools.get("course100", [])[1:]

    tonamorn_basic = pools.get("tonamorn_basic", [])
    tonamorn_speak = pools.get("tonamorn_speak", [])
    tonamorn = tonamorn_basic + tonamorn_speak
    adam = pools.get("adam", [])
    bbc = pools.get("bbc_daily", [])
    unfox = pools.get("unfox", [])
    krudew = pools.get("krudew", [])
    vanessa = pools.get("vanessa", [])
    easy = pools.get("easyenglish", [])
    e101 = pools.get("english101", [])

    def filter_listen(videos):
        return [v for v in videos if is_listen_clip(v["title"])]

    def filter_speak(videos):
        return [v for v in videos if is_speak_clip(v["title"])]

    speak_base = VERIFIED_SPEAK + filter_speak(tonamorn_speak) + filter_speak(unfox) + filter_speak(krudew) + filter_speak(vanessa) + filter_speak(e101) + filter_speak(tonamorn_basic)

    return {
        "vocab": vocab,
        "course": course,
        "tonamorn_speak": filter_listen(tonamorn_speak) or tonamorn_speak,
        "listen_p1": filter_listen(unfox[:80] + tonamorn_basic[:40] + bbc[:20] + easy[:30]),
        "listen_p2": filter_listen(easy[:60] + bbc + unfox[40:80]),
        "listen_p3": filter_listen(vanessa[:60] + e101[:60] + easy[60:100]),
        "speak_p1": speak_base + filter_speak(unfox[:80]) + filter_speak(adam),
        "speak_p2": filter_speak(vanessa[:80]) + filter_speak(easy[:40]) + filter_speak(bbc) + speak_base,
        "speak_p3": filter_speak(vanessa) + filter_speak(e101[:80]) + filter_speak(tonamorn_speak) + speak_base,
        "main_p2": filter_listen(bbc + krudew[:60]) or krudew + adam,
        "main_p3": filter_listen(vanessa[:80] + tonamorn) or vanessa + tonamorn,
    }


def build_main_lesson(p: dict, phase: int, n: int, course: list, tonamorn_speak: list, vocab_item: dict) -> dict:
    if phase == 1:
        if n % 2 == 0 and tonamorn_speak:
            t = pick(tonamorn_speak, n // 2)
            return seg(25, "บทเรียนหลัก", "🎓", t["title"], "study", t["url"], t["channel"],
                       "ฝึกพูดตามประโยคในชีวิตจริง — ออกเสียงดัง ๆ")
        if course:
            c = course[(n - 1) % len(course)]
            return seg(25, "บทเรียนหลัก", "🎓", c["title"], "study", c["url"], "English by Chris",
                       "คอร์สหลัก — จดประโยคที่ใช้บ่อย แล้วพูดตามครู")
    elif phase == 2:
        m = pick(p["main_p2"], n)
        return seg(25, "บทเรียนหลัก", "🎓", m["title"], "study", m["url"], m["channel"],
                   "ฟัง + พูดตามประโยคตัวอย่าง — เน้น Tense พื้นฐาน")
    else:
        m = pick(p["main_p3"], n)
        return seg(25, "บทเรียนหลัก", "🎓", m["title"], "study", m["url"], m["channel"],
                   "ฟังแล้วพูดสรุปด้วยคำของตัวเอง 1–2 ประโยค")
    return seg(25, "บทเรียนหลัก", "🎓", vocab_item["title"], "study", vocab_item["url"], "English by Chris", "")


def build_speak_segment(phase: int, n: int, p: dict, used_ids: set, listen_vid: str) -> dict:
    pool = p["speak_p1"] if phase == 1 else (p["speak_p2"] if phase == 2 else p["speak_p3"])
    sp = pick_unique(pool, n, used_ids, offset=3)
    if sp:
        return seg(
            10, "พูดตาม (Shadowing)", "🗣️", sp["title"], "speak",
            sp["url"], sp["channel"],
            "หยุดทีละประโยค พูดตามให้เหมือนที่สุด ออกเสียงดัง ๆ",
        )
    return seg(
        10, "พูดตาม (Shadowing)", "🗣️",
        "กลับไปเปิดคลิปฟังด้านบนอีกรอบ", "speak",
        "", listen_vid and "" or "",
        "ไม่มีคลิปพูดแยกวันนี้ — เปิดคลิปฟังด้านบนซ้ำ แล้วพูดตามทีละประโยค",
        replay_of="listen",
    )


def build_plan(pools: dict) -> list[dict]:
    p = build_pools(pools)
    plan = []
    study_count = 0

    for day in range(1, 181):
        day_in_week = ((day - 1) % 7) + 1
        phase = 1 if day <= 60 else (2 if day <= 120 else 3)
        meta = PHASE_META[phase]
        week = (day - 1) // 7 + 1

        if day_in_week <= 5:
            study_count += 1
            n = study_count
            used_ids: set[str] = set()

            v = pick_vocab(p["vocab"], n)
            if v.get("id"):
                used_ids.add(v["id"])

            vocab_seg = seg(
                10, "ท่องศัพท์ + ออกเสียง", "🃏",
                v["title"] or f"ศัพท์ชุดที่ {n}", "vocab",
                v["url"], "English by Chris",
                vocab_words(n) if phase == 1 else "ทบทวน + ออกเสียงดัง ๆ ทุกคำ ใน Anki/Quizlet",
            )

            # Days 3 & 5: AI speak instead of listen slot
            if day_in_week in (3, 5):
                listen_seg = seg(
                    15, "ฝึกพูดกับ AI", "🤖",
                    "คุยกับ ChatGPT — พิมพ์ 'Let's practice English conversation about daily life'",
                    "speak", AI_URL, "ChatGPT",
                    "ตอบเป็นภาษาอังกฤษเท่านั้น 5–6 ประโยค ผิดได้ไม่เป็นไร",
                )
            else:
                listen_pool = p["listen_p1"] if phase == 1 else (p["listen_p2"] if phase == 2 else p["listen_p3"])
                lc = pick_unique(listen_pool, n, used_ids)
                if not lc:
                    lc = pick(listen_pool, n)
                if lc.get("id"):
                    used_ids.add(lc["id"])
                listen_seg = seg(
                    15, "ฟัง (Listening)", "👂",
                    lc["title"], "listen",
                    lc["url"], lc["channel"],
                    "ฟังจับใจความ ไม่ต้องเข้าใจทุกคำ — อย่าพูดตามรอบนี้",
                )

            main_seg = build_main_lesson(p, phase, n, p["course"], p["tonamorn_speak"], v)
            main_vid = video_id(main_seg.get("url", ""))
            if main_vid:
                used_ids.add(main_vid)

            if phase == 3:
                speak_seg = seg(
                    10, "พูด + เขียน", "🗣️",
                    "พูดกับ AI 5 นาที แล้วเขียนไดอารี่ 3 ประโยค",
                    "speak", AI_URL, "ChatGPT",
                    "1) คุยกับ AI 5 นาที 2) เขียนสรุปวันนี้ 3 ประโยค 3) ให้ AI ช่วยแก้",
                )
            else:
                speak_seg = build_speak_segment(phase, n, p, used_ids, "")

            segments = [vocab_seg, listen_seg, main_seg, speak_seg]
            plan.append({
                "day": day,
                "week": week,
                "type": "study",
                "phase": phase,
                "phaseName": meta["name"],
                "phaseMonths": meta["months"],
                "phaseEmoji": meta["emoji"],
                "totalMinutes": 60,
                "segments": segments,
            })

        elif day_in_week == 6:
            ct = pick(CARTOONS, week)
            plan.append({
                "day": day, "week": week, "type": "chill",
                "phase": phase, "phaseName": meta["name"],
                "phaseMonths": meta["months"], "phaseEmoji": meta["emoji"],
                "totalMinutes": 45,
                "segments": [seg(
                    45, "ดูการ์ตูน/หนังซับอังกฤษ", "🍿",
                    ct["title"], "listen", ct["url"], ct["channel"],
                    "เปิดซับอังกฤษ ดูสบาย ๆ พยายามฟังเสียงไม่ต้องจด",
                )],
            })

        else:
            plan.append({
                "day": day, "week": week, "type": "chill",
                "phase": phase, "phaseName": meta["name"],
                "phaseMonths": meta["months"], "phaseEmoji": meta["emoji"],
                "totalMinutes": 30,
                "segments": [
                    seg(20, "ฝึกพูดกับ AI", "🤖",
                        "คุยกับ ChatGPT/Gemini — 'Let's practice English conversation'",
                        "speak", AI_URL, "ChatGPT",
                        "ให้ AI ถามคำถามง่าย ๆ ตอบเป็นภาษาอังกฤษ ออกเสียงดัง ๆ"),
                    seg(10, "ทบทวนศัพท์ทั้งสัปดาห์", "🎮",
                        "เล่นเกมทวนศัพท์ใน Quizlet (โหมด Match/Test)",
                        "vocab", QUIZLET_URL, "Quizlet",
                        "ทวนคำศัพท์ของสัปดาห์นี้แบบเกม"),
                ],
            })

    return plan


def main():
    print("Fetching playlists...")
    pools = {}
    ch_map = {
        "vocab365": "English by Chris", "course100": "English by Chris",
        "tonamorn_basic": "ต้นอมร", "tonamorn_speak": "ต้นอมร",
        "adam": "Adam Bradshaw", "bbc_daily": "BBC Learning English",
    }
    for key, pid in PLAYLISTS.items():
        try:
            videos = yt_playlist(pid, ch_map.get(key, ""))
            pools[key] = videos
            print(f"  {key}: {len(videos)} videos")
        except Exception as e:
            print(f"  {key}: FAILED ({e})")
            pools[key] = []

    for key in CHANNELS:
        try:
            videos = yt_channel(key)
            pools[key] = videos
            print(f"  {key}: {len(videos)} videos")
        except Exception as e:
            print(f"  {key}: FAILED ({e})")
            pools[key] = []

    plan = build_plan(pools)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(plan)} days to {OUT}")

    js_out = ROOT / "data" / "plan.js"
    with open(js_out, "w", encoding="utf-8") as f:
        f.write("window.ENGLISH_PLAN = ")
        json.dump(plan, f, ensure_ascii=False)
        f.write(";\n")
    print(f"Wrote {js_out}")

    validate = ROOT / "scripts" / "validate_plan.py"
    if validate.exists():
        subprocess.run([sys.executable, str(validate)], cwd=str(ROOT))


if __name__ == "__main__":
    main()
