import requests
from leapcell import Leapcell
import time
import logging
import datetime
import sys
import copy
import os
from flask import Flask, render_template, request, redirect
import random
app = Flask(__name__)

# leapclient = Leapcell("http://localhost:8080", "xxx")
leapclient = Leapcell(
    api_key="lpcl_199104680.124ebf2de00728aabeeb534cc5530cdd",
    # base_url="http://localhost:8080",
)
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


headers = {'Accept': 'application/json'}

key = os.environ.get("YOUTUBE_KEY", "AIzaSyAj9h1wEcBNMkvKEGYRlOsL5goHNs44D4w")
if not key:
    raise Exception("YOUTUBE_KEY is not set")

category = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers",
}


def get_trends_video(region: str, category: str):
    url = "https://www.googleapis.com/youtube/v3/videos"
    response = requests.get(url, params={
        "part": "contentDetails",
        "chart": "mostPopular",
        "regionCode": region,
        "key": key,
        "videoCategoryId": category,
    })
    return response.json()


def get_video_info(id: str):
    url = "https://www.googleapis.com/youtube/v3/videos"
    response = requests.get(url, params={
        "part": "snippet",
        "id": id,
        "key": key
    })
    return response.json()


def get_region():
    url = "https://www.googleapis.com/youtube/v3/i18nRegions"
    response = requests.get(url, params={
        "part": "snippet",
        "key": key
    })
    return response.json()


def process_trends_video(region: str, category_id: str, region_name: str):
    now_dt = datetime.datetime.now()  # TODAY
    now = datetime.datetime(now_dt.year, now_dt.month, now_dt.day)
    now_ts = time.mktime(now.timetuple())
    table = leapclient.table(
        "salamer/youtube", table_id="tbl1715607315934547968", name_type="name")

    count = table.select().where((table["region"] == region) &
                                 (table["category"] == category[category_id]) &
                                 (table["retrieve_time"] > now_ts)).count()
    # print(count)
    if count >= 3:
        logging.info("Skip region %s, category %s",
                     region, category[category_id])
        return {"items": []}

    trends = get_trends_video(region, category_id)
    if "items" not in trends:
        return {"items": []}
    if len(trends["items"]) == count:
        logging.info("Skip region %s, category %s",
                     region, category[category_id])
        return {"items": []}

    images = []

    for item in trends["items"]:
        video_id = item["id"]
        video_info = get_video_info(video_id)
        time.sleep(1)
        if len(video_info["items"]) == 0:
            continue
        video_info = video_info["items"][0]
        response = requests.get(
            video_info["snippet"]["thumbnails"]["high"]["url"])
        if response.status_code != 200:
            logging.error("Failed to download image for video %s", video_id)
        images.append(copy.deepcopy(response.content))
        image = table.upload_file(response.content)
        publishAt = datetime.datetime.strptime(
            video_info["snippet"]["publishedAt"], '%Y-%m-%dT%H:%M:%S%z')
        tags = []
        if "tags" in video_info["snippet"]:
            tags = video_info["snippet"]["tags"]
        table.upsert({
            "title": video_info["snippet"]["title"],
            "description": video_info["snippet"]["description"],
            "cover": image.id(),
            "video_id": video_id,
            "publishAt": int(time.mktime(publishAt.timetuple())),
            "channel": video_info["snippet"]["channelTitle"],
            "tag": tags,
            "region": region_name,
            "category": category[category_id],
            "url": "https://www.youtube.com/watch?v=" + video_id,
            "retrieve_time": now_ts,
            "channelId": video_info["snippet"]["channelId"],
        }, on_conflict=["video_id", "retrieve_time", "region"])
    logging.info("Retrieved %d videos for region %s, category %s",
                 len(trends["items"]), region, category[category_id])
    return trends


def retrieve():
    regions = get_region()
    for region in regions["items"]:
        for key in category.keys():
            # try:
            process_trends_video(
                region["snippet"]["gl"], key, region_name=region["snippet"]["name"])
            # except Exception as e:
            #     logger.error(
            #         "Failed to retrieve video for region %s, category %s", region["snippet"]["gl"], key)
            #     logger.error(e)
            time.sleep(1)


@app.route("/xx")
def xx():
    logging.info("xx, youtube here")
    print("xx, youtube here")
    return {"qq": "xx"}


@app.route("/exception")
def exception():
    logging.info("exceptions")
    print("ohqoehqiowehioq")
    return Exception("wqeqwpjepoqwjepq")


@app.route("/process_trends_video")
def process_trends_video_api():
    logging.info("Process youtube trends video")
    print("Process youtube trends video")
    region = request.args.get("region")
    category_id = request.args.get("category_id")
    region_name = request.args.get("region_name")
    return process_trends_video(region, category_id, region_name)


@app.route("/retrieve")
def retrieve_api():
    regions = get_region()
    print(regions)
    logging.info("Retrieve youtube trends video")
    print("Retrieve youtube trends video")
    print(regions)
    for region in regions["items"]:
        randint_val = random.randint(1, 100)
        if randint_val > 3:
            continue
        for key in category.keys():
            # r = requests.get("http://127.0.0.1:5000/process_trends_video", params={
            r = requests.get("https://youtube-trends-test1-xamqyxwb.leapcell.dev/process_trends_video", params={
                "region": region["snippet"]["gl"],
                "category_id": key,
                "region_name": region["snippet"]["name"]
            })
            print(r)

    return {"status": "ok"}


@app.route("/hello_demo")
def hello_demo():
    print("hello demo")
    return {"hello": "demo"}


if __name__ == "__main__":
    retrieve()
    # app.run(port=5000, debug=True)
