import re
import requests
from zlapi.models import Message
from moviepy.editor import VideoFileClip
import os


des = {
    'version': "1.0.9",
    'credits': "Quốc Khánh",
    'description': "Tải video hoặc ảnh từ các nền tảng hỗ trợ."
}

IMGUR_CLIENT_ID = "6d0dba3a66763d9"

SUPPORTED_DOMAINS = [
    "tiktok", "douyin", "capcut", "threads", "instagram", "facebook", "espn", "kuaishou",
    "pinterest", "imdb", "imgur", "ifunny", "izlesene", "reddit", "youtube", "twitter", 
    "vimeo", "snapchat", "bilibili", "dailymotion", "sharechat", "linkedin", "tumblr", 
    "hipi", "telegram", "getstickerpack", "bitchute", "febspot", "9gag", "oke.ru", 
    "rumble", "streamable", "ted", "sohu", "xvideos", "xnxx", "xiaohongshu", "weibo", 
    "miaopai", "meipai", "xiaoying", "national", "yingke", "soundcloud", "mixcloud", 
    "spotify", "zingmp3", "bandcamp"
]

API_URL = "https://www.hungdev.id.vn/media/downAIO"
API_KEY = "kddWJu8X2U"


def compress_video(input_path, output_path, target_size_mb=10):
    clip = VideoFileClip(input_path)
    duration = clip.duration
    target_bitrate = (target_size_mb * 8 * 1024 * 1024) / duration
    clip.write_videofile(output_path, codec="libx264", bitrate=f"{int(target_bitrate)}")
    clip.close()


def handle_down_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip()

    
    def extract_links(content):
        return re.findall(r'(https?://[^\s]+)', content)

   
    def is_supported_link(link):
        return any(domain in link.lower() for domain in SUPPORTED_DOMAINS)

    
    def download_video(video_link):
        params = {'url': video_link, 'apikey': API_KEY}
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('success') and data.get('data'):
            video_data = data['data']
            medias = video_data.get("medias", [])
            for media in medias:
                if media.get("type") == "video":
                    video_url = media.get("url")
                    thumbnail_url = video_data.get("thumbnail")
                    return video_url, thumbnail_url
        raise Exception("Không tìm thấy video hợp lệ.")

    
    def upload_to_imgur(file_path):
        headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
        with open(file_path, "rb") as file_data:
            response = requests.post(
                "https://api.imgur.com/3/upload",
                headers=headers,
                files={"video": file_data}
            )
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            return result["data"]["link"]
        raise Exception("Tải lên Imgur thất bại.")

    
    def get_video_info(file_path):
        clip = VideoFileClip(file_path)
        duration = clip.duration
        width, height = clip.size
        clip.close()
        return duration, width, height

    try:
        links = extract_links(content)
        if not links:
            client.replyMessage(Message(text="Không tìm thấy URL nào trong nội dung."), message_object, thread_id, thread_type, ttl=10000)
            return

        video_link = links[0].strip()
        if not is_supported_link(video_link):
            client.replyMessage(Message(text="URL không được hỗ trợ."), message_object, thread_id, thread_type, ttl=10000)
            return

        video_url, thumbnail_url = download_video(video_link)
        client.replyMessage(Message(text="Bắt đầu tải xuống..."), message_object, thread_id, thread_type, ttl=10000)

        video_file = requests.get(video_url)
        local_path = "downloaded_video.mp4"
        with open(local_path, "wb") as f:
            f.write(video_file.content)

        if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
            raise Exception("File tải về không hợp lệ hoặc bị trống.")

        
        if os.path.getsize(local_path) > 10 * 1024 * 1024:
            compressed_path = "compressed_video.mp4"
            compress_video(local_path, compressed_path, target_size_mb=10)
            file_to_upload = compressed_path
        else:
            file_to_upload = local_path

        
        imgur_link = upload_to_imgur(file_to_upload)
        duration, width, height = get_video_info(file_to_upload)

        
        success_message = Message(text=f"Video tải về thành công! URL tải lên: {imgur_link}")
        client.sendRemoteVideo(
            video_url,
            thumbnailUrl=thumbnail_url,
            duration=duration,
            message=success_message,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=600000
        )

    except Exception as e:
        client.sendMessage(Message(text=f"Đã xảy ra lỗi: {str(e)}"), thread_id, thread_type)
    
    finally:
        
        if os.path.exists("downloaded_video.mp4"):
            os.remove("downloaded_video.mp4")
        if os.path.exists("compressed_video.mp4"):
            os.remove("compressed_video.mp4")


def handle_message_auto_download(message, message_object, thread_id, thread_type, author_id, client):
    handle_down_command(message, message_object, thread_id, thread_type, author_id, client)


def get_mitaizl():
    return {
        'down': handle_down_command
    }