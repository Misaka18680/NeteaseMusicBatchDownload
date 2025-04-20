import os
import sys
import requests
import urllib.parse
import time

def search_song_id(keyword):
    """
    调用网易云音乐搜索接口，返回第一个搜索结果的 songId 及其信息。
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


def sanitize_filename(name):
    """
    删除文件名中非法字符，避免重命名失败。
    """
    keepchars = (" ", ".", "_", "-")
    return "".join(c for c in name if c.isalnum() or c in keepchars).rstrip()


def batch_download_from_txt(txt_file, output_dir="downloads"):
    """
    从 txt 文件读取每行歌曲名，批量下载并重命名。
    并输出日志信息。
    """
    if not os.path.isfile(txt_file):
        print(f"错误：找不到文件 {txt_file}")
        return

    os.makedirs(output_dir, exist_ok=True)
    log_entries = []

    with open(txt_file, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for keyword in lines:
        print(f"正在搜索并下载：{keyword}")
        song_info = search_song_id(keyword)
        if not song_info:
            print(f"未找到《{keyword}》，跳过。")
            continue

        song_id = song_info["id"]
        artist = song_info["artist"]
        song_name = song_info["name"]
        url = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"

        try:
            orig_path, size, duration = download_song(song_id, save_dir=output_dir)

            # 重命名
            safe_name = sanitize_filename(keyword)
            new_filename = f"{safe_name}.mp3"
            new_path = os.path.join(output_dir, new_filename)
            count = 1
            base, ext = os.path.splitext(new_path)
            while os.path.exists(new_path):
                new_path = f"{base}({count}){ext}"
                count += 1

            os.rename(orig_path, new_path)

            status = "成功" if size >= 512000 else "失败 (文件小于500KB)"
            speed_kb = size / 1024 / duration if duration > 0 else 0

            log_entries.append(
                f"歌曲：{song_name} | 作者：{artist} | ID：{song_id} | URL：{url}\n"
                f"状态：{status} | 大小：{size/1024:.2f} KB | 速度：{speed_kb:.2f} KB/s\n"
            )

            print(f"{song_name} 下载完成：{status}")
        except Exception as e:
            log_entries.append(
                f"歌曲：{keyword} | 下载失败：{e}\n"
            )
            print(f"下载《{keyword}》时出错：{e}")

    print("\n\n下载日志：")
    for entry in log_entries:
        print("-" * 50)
        print(entry)


def main():
    txt_file = "songs.txt"
    if len(sys.argv) > 1:
        txt_file = sys.argv[1]

    print(f"使用 txt 列表：{txt_file}")
    batch_download_from_txt(txt_file)
    input("\n下载完成，按 Enter 键退出...")

if __name__ == "__main__":
    main()
