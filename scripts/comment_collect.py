#Test
import csv
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
API_KEY = os.environ["YT_API_KEY"]
CONFIG_FILE = Path("config/videos.csv")
Event_Start = "2026-10-23T00:00:00Z"
Window_days = 14
Comment_Cap = 500 
Seed = 42
max_retries = 3
output_dir = Path("data/raw")

fields = (
    "nextPageToken,items(id,snippet(videoId,"
    "topLevelComment(id,snippet(textDisplay,publishedAt,likeCount))))"
) #Never requests author names or profile images, only comment text, date, and like count.

class quotaexceedederror(Exception):
    pass
class commentdisablederror(Exception):
    pass

def to_dt(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))

def get_page(video_id, page_token=None):
    params = {
        "part": "snippet",
        "videoId": video_id,
        "order": "time",
        "maxResults": 100,
        "textFormat": "plainText",
        "fields": fields,
        "key": API_KEY,
    }
    if page_token:
        params["pageToken"] = page_token #next page
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            try:
                body = json.load(e)
                reason = body["error"]["errors"][0].get("reason", "")
            except Exception:
                reason = ""
            if reason == "quotaExceeded":
                raise quotaexceedederror("Quota exceeded for YouTube Data API.")
            if reason == "commentsDisabled":
                raise commentdisablederror("Comments are disabled for this video.")
            if e.code >= 500 and attempt < max_retries:
                time.sleep(5 * attempt)  # backoff for server errors
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < max_retries:
                time.sleep(5 * attempt)  #  backoff for network errors
                continue
            raise

def load_saved(path):
    saved = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    saved[record["comment_id"]] = record
    return saved

def collect_video(video_id, channel_name, channel_type):
    start_dt = to_dt(Event_Start)
    end_dt = start_dt + timedelta(days=Window_days)
    time_retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / f"{video_id}_progress.jsonl"
    final_path = output_dir / f"{video_id}.jsonl"

    comments = load_saved(progress_path)
    already_saved = 0
    seen_this_run = set()
    duplicates = before_window = after_window = pages = 0
    page_log = []
    ordering_issues = []
    prev_page_oldest = None
    page_token = None

    with open(progress_path, "a", encoding="utf-8") as out:
        while True:
            data = get_page(video_id, page_token)
            pages += 1
            passed_start = False
            page_times = []

            for item in data.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]
                comment_id = top_comment["id"]
                published_at = to_dt(top_comment["snippet"]["publishedAt"])
                page_times.append(published_at)

                if comment_id in seen_this_run:
                    duplicates += 1
                    continue
                seen_this_run.add(comment_id)

                if published_at >= end_dt:
                    after_window += 1
                elif published_at < start_dt:
                    before_window += 1
                    passed_start = True
                elif comment_id in comments:
                    already_saved += 1
                else:
                    record = {
                        "comment_id": comment_id,
                        "video_id": item["snippet"]["videoId"],
                        "text": top_comment["snippet"]["textDisplay"],
                        "published_at": top_comment["snippet"]["publishedAt"],
                        "like_count": top_comment["snippet"].get("likeCount", 0),
                        "retrieved_at": time_retrieved,
                    }
                    comments[comment_id] = record
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")

            out.flush()  # Ensure data is saved in error
            os.fsync(out.fileno())

            if page_times:
                newest, oldest = max(page_times), min(page_times)
                page_log.append({
                    "page": pages,
                    "newest": newest.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "oldest": oldest.strftime("%Y-%m-%dT%H:%M:%SZ"),
                })

                for i in range(1, len(page_times)):
                    if page_times[i] > page_times[i-1]:
                        ordering_issues.append(f"page {pages}: timestamp moves forward at item {i}")
                        break

                if prev_page_oldest is not None and newest > prev_page_oldest:
                    ordering_issues.append(f"page {pages}: newest comment {newest} is newer than previous page's oldest {prev_page_oldest}")
                prev_page_oldest = oldest

            page_token = data.get("nextPageToken")

            if not page_token or passed_start:
                break

    ids = sorted(comments.keys())
    if len(ids) > Comment_Cap:
        ids = sorted(random.Random(Seed).sample(ids, Comment_Cap))
    with open(final_path, "w", encoding="utf-8") as f:
        for comment_id in ids:
            f.write(json.dumps(comments[comment_id], ensure_ascii=False) + "\n")
    progress_path.unlink()
    report = {
        "video_id": video_id,
        "channel_name": channel_name,
        "channel_type": channel_type,
        "status": "completed",
        "retrieved_at": time_retrieved,
        "window_start": Event_Start,
        "window_end": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "api_calls": pages,
        "comments_window": len(comments),
        "comments_collected": len(ids),
        "duplicates": duplicates,
        "before_window": before_window,
        "after_window": after_window,
        "already_saved": already_saved,
        "window_comment_ids": sorted(comments.keys()),
        "page_log": page_log,
        "ordering_issues": ordering_issues,
        "ordering_ok": len(ordering_issues) == 0,
    }
    print(f"Video {video_id}: In window: {len(comments)} comments, collected: {len(ids)} comments, duplicates: {duplicates}, before window: {before_window}, after window: {after_window}, already saved: {already_saved}, API calls: {pages}")
    print(f"Comments saved to {final_path}")
    return report

def main():
    with open(CONFIG_FILE, newline='', encoding='utf-8') as f:
        videos = list(csv.DictReader(f))

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for video in videos:
        video_id = video['video_id']
        final_path = output_dir / f"{video_id}.jsonl"

        if final_path.exists():
            with open(final_path) as f:
                print(f"Skipping video {video_id} as it is already completed.")
                manifest.append({
                    "video_id": video_id,
                    "channel_name": video["channel_name"],
                    "channel_type": video["channel_type"],
                    "status": "skipped_already_done",
                })
                continue
        entry = {
            "video_id": video_id,
            "channel_name": video["channel_name"],
            "channel_type": video["channel_type"],
        }
        try:
            report = collect_video(video_id, video["channel_name"], video["channel_type"])
            entry["status"] = "done"
            entry["report"] = report
        except commentdisablederror:
            print(f"{video_id}: comments disabled, continuing")
            entry["status"] = "comments_disabled"
        except quotaexceedederror:
            print(f"{video_id}: quota exceeded, stopping run. Re-run later to resume.")
            entry["status"] = "quota_exceeded"
            manifest.append(entry)
            break
        except Exception as e: # anything else: record it and keep going so one bad video doesn't kill the run
            print(f"{video_id}: error: {e}")
            entry["status"] = f"error: {e}"
        manifest.append(entry)
        
    manifest_path = output_dir / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "videos": manifest,
            "comments_disabled_count": sum(1 for m in manifest if m["status"] == "comments_disabled"),
        }, f, indent=2)
    print(f"Run manifest saved to {manifest_path}")

if __name__ == "__main__": #run file only if called directly, not imported.
    main()