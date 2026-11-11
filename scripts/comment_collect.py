#TEST ON ONE VIDEO
import json
from json.tool import main
import random
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
API_KEY = "YOUR_API_KEY_HERE"
VIDEO_ID = "4FOOKUfUWzg"
Channel_type = "independent"
Event_Start = "2026-10-23T00:00:00Z"
Window_days = 14
Comment_Cap = 500 
Seed = 42
output_dir = Path("data/raw")

fields = (
    "nextPageToken,items(id,snippet(videoId,"
    "topLevelComment(id,snippet(textDisplay,publishedAt,likeCount))))"
) #Never reuquests author names or profile images, only comment text, date, and like count.

def to_dt(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))

def get_page(page_token=None):
    params = {
        "part": "snippet",
        "videoId": VIDEO_ID,
        "order": "time",
        "maxResults": 100,
        "textFormat": "plainText",
        "fields": fields,
        "key": API_KEY,
    }
    if page_token:
        params["pageToken"] = page_token
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)

def collect_comments():
    if "YOUR_API_KEY_HERE" in API_KEY:
        raise ValueError("Please set your YouTube Data API key in the API_KEY.")
    
    start_dt = to_dt(Event_Start)
    end_dt = start_dt + timedelta(days=Window_days)
    time_retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    comments = {} #getting rid of duplicates 
    duplicates = before_window = after_window = pages = 0
    page_token = None

    while True: 
        data = get_page(page_token)
        pages += 1
        passed_start = False

        for item in data.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]
            comment_id = top_comment["id"]
            published_at = to_dt(top_comment["snippet"]["publishedAt"]) 

            if comment_id in comments:
                duplicates += 1
            elif published_at >= end_dt:
                after_window += 1
            elif published_at < start_dt:
                before_window += 1
                passed_start = True
            else:
                comments[comment_id] = {
                    "comment_id": comment_id,
                    "video_id": item["snippet"]["videoId"],
                    "text": top_comment["snippet"]["textDisplay"],
                    "published_at": top_comment["snippet"]["publishedAt"],
                    "like_count": top_comment["snippet"].get("likeCount", 0),
                    "retrieved_at": time_retrieved,
                }

        page_token = data.get("nextPageToken")
        if not page_token or passed_start:
            break
    ids = sorted(comments.keys())
    if len(ids) > Comment_Cap:
        ids = sorted(random.Random(Seed).sample(ids, Comment_Cap))
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / f"{VIDEO_ID}_{time_retrieved.replace(':', '-')}"
    with open(f"{base}.jsonl", "w", encoding="utf-8") as f:
        for comment_id in ids:
            f.write(json.dumps(comments[comment_id], ensure_ascii=False) + "\n")

    report = {
        "video_id": VIDEO_ID,
        "channel_type": Channel_type,
        "retrieved_at": time_retrieved,
        "window_start": Event_Start,
        "window_end": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "api_calls": pages,
        "comments_window": len(comments),
        "comments_collected": len(ids),
        "duplicates": duplicates,
        "before_window": before_window,
        "after_window": after_window,
        "window_comment_ids": sorted(comments.keys()),    
    }
    with open(f"{base}_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"In window: {len(comments)} comments, collected: {len(ids)} comments, duplicates: {duplicates}, before window: {before_window}, after window: {after_window}, API calls: {pages}")
    print(f"Comments saved to {base}.json1 and report saved to {base}_report.json")

if __name__ == "__main__":
    collect_comments()