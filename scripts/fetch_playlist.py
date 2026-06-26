"""Fetch YouTube playlist video IDs and titles for plan generation."""
import json
import re
import sys
import urllib.request

PLAYLISTS = {
    "vocab365": "PLcWqwqWwXmGImAja_ln1WVkF_sLAjKIMq",
    "course100": "PLcWqwqWwXmGI1gQHL06cnf6thN_28b8_u",
    "phonics": "PLWUeqZvLnryo39LeljmK742Ciutt5bMFx",
    "bbc6min": "PLcetZ6gSkBvWgYkm5WXP-bQj_fVh86ih",
    "easyenglish": "PLcWqwqWwXmGImAja_ln1WVkF_sLAjKIMq",
}


def fetch_playlist(playlist_id: str) -> list[dict]:
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")

    videos = []
    seen = set()

    # Parse ytInitialData for full playlist contents
    m = re.search(r"var ytInitialData = ({.*?});</script>", html)
    if m:
        data = json.loads(m.group(1))
        contents = (
            data.get("contents", {})
            .get("twoColumnBrowseResultsRenderer", {})
            .get("tabs", [{}])[0]
            .get("tabRenderer", {})
            .get("content", {})
            .get("sectionListRenderer", {})
            .get("contents", [{}])[0]
            .get("itemSectionRenderer", {})
            .get("contents", [{}])[0]
            .get("playlistVideoListRenderer", {})
            .get("contents", [])
        )
        for item in contents:
            vr = item.get("playlistVideoRenderer", {})
            vid = vr.get("videoId")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            title_runs = vr.get("title", {}).get("runs", [{}])
            title = title_runs[0].get("text", "") if title_runs else ""
            idx = vr.get("index", {}).get("simpleText", str(len(videos) + 1))
            videos.append({
                "id": vid,
                "title": title,
                "index": int(idx) if str(idx).isdigit() else len(videos) + 1,
                "url": f"https://www.youtube.com/watch?v={vid}&list={playlist_id}&index={idx}",
            })
        if videos:
            return videos

    titles = re.findall(r'"title":\{"runs":\[\{"text":"((?:\\.|[^"\\])*)"\}', html)
    ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    for vid, title in zip(ids, titles):
        if vid in seen:
            continue
        seen.add(vid)
        title = title.encode("utf-8").decode("unicode_escape")
        videos.append({
            "id": vid,
            "title": title,
            "index": len(videos) + 1,
            "url": f"https://www.youtube.com/watch?v={vid}&list={playlist_id}&index={len(videos)}",
        })

    return videos


def main():
    playlist_key = sys.argv[1] if len(sys.argv) > 1 else "vocab365"
    playlist_id = PLAYLISTS.get(playlist_key, playlist_key)
    videos = fetch_playlist(playlist_id)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    data = json.dumps(videos, ensure_ascii=False, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Wrote {len(videos)} videos to {out}")
    else:
        print(len(videos))


if __name__ == "__main__":
    main()
