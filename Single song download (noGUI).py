import os
import sys
import requests
import time

def search_song_id(keyword):
    """
    调用网易云音乐搜索接口，返回第一个搜索结果的 songId。
    """
    url = "https://music.163.com/api/search/get"
    params = {
        "s": keyword,
        "type": 1,     # 1 表示搜索歌曲
        "limit": 1,    # 只取第一个结果
        "offset": 0
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://music.163.com"
    }
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # 检查是否有结果
    if data.get("result") and data["result"].get("songs"):
        song = data["result"]["songs"][0]
        return {
            "id": song["id"],
            "name": song["name"],
            "artist": ", ".join(artist["name"] for artist in song["artists"])
        }
    else:
        return None

def sanitize_filename(name):
    """清理非法字符以生成安全的文件名"""
    keepchars = (" ", ".", "_", "-")
    return "".join(c for c in name if c.isalnum() or c in keepchars).rstrip()

def download_song(song_id, save_dir="."):
    """
    根据 song_id 构造下载链接并保存 MP3，返回文件路径、大小、下载耗时。
    """
    download_url = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://music.163.com"
    }
    start_time = time.time()
    resp = requests.get(download_url, headers=headers, stream=True)
    resp.raise_for_status()

    filename = f"{song_id}.mp3"
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    total_size = 0
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                total_size += len(chunk)
                f.write(chunk)
    duration = time.time() - start_time
    return filepath, total_size, duration

def main():
    keyword = input("请输入要下载的歌曲名称： ").strip()
    if not keyword:
        print("歌曲名称不能为空。")
        sys.exit(1)

    print(f"正在搜索《{keyword}》的 songId ...")
    song_info = search_song_id(keyword)
    if not song_info:
        print("未找到匹配的歌曲，请换个关键词再试。")
        sys.exit(1)

    song_id = song_info["id"]
    song_name = song_info["name"]
    artist = song_info["artist"]
    url = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"

    print(f"找到 songId：{song_id}，正在下载 ...")
    try:
        orig_path, size, duration = download_song(song_id)

        # 重命名文件
        safe_name = sanitize_filename(keyword)
        new_filename = f"{safe_name}.mp3"
        new_path = os.path.join(".", new_filename)
        count = 1
        base, ext = os.path.splitext(new_path)
        while os.path.exists(new_path):
            new_path = f"{base}({count}){ext}"
            count += 1

        os.rename(orig_path, new_path)

        status = "成功" if size >= 512000 else "失败 (文件小于500KB)"
        speed_kb = size / 1024 / duration if duration > 0 else 0

        print("\n下载日志：")
        print("-" * 50)
        print(f"歌曲：{song_name}")
        print(f"作者：{artist}")
        print(f"ID：{song_id}")
        print(f"URL：{url}")
        print(f"状态：{status}")
        print(f"大小：{size / 1024:.2f} KB")
        print(f"平均速度：{speed_kb:.2f} KB/s")
        print("-" * 50)
    except Exception as e:
        print("下载过程中出错：", e)

    input("\n下载完成，按 Enter 键退出...")

if __name__ == "__main__":
    main()
