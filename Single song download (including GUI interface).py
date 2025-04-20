import os
import sys
import requests
import time
import tkinter as tk
from tkinter import messagebox, simpledialog

def format_duration(seconds):
    """将秒数转换为 x分x秒 的格式"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{int(minutes)}分{int(seconds)}秒"

def search_song_id(keyword):
    """
    调用网易云音乐搜索接口，返回搜索结果的歌曲列表。
    """
    url = "https://music.163.com/api/search/get"
    params = {
        "s": keyword,
        "type": 1,     # 1 表示搜索歌曲
        "limit": 10,   # 返回最多 10 首结果
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
        songs = data["result"]["songs"]
        return [{
            "id": song["id"],
            "name": song["name"],
            "artist": ", ".join(artist["name"] for artist in song["artists"]),
            "album": song["album"]["name"],
            "duration": song["duration"] / 1000  # 转换为秒
        } for song in songs]
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

def display_search_results(songs):
    """
    显示搜索结果的歌曲列表，用户可以选择下载。
    """
    result_window = tk.Toplevel(root)
    result_window.title("搜索结果")

    for idx, song in enumerate(songs):
        song_duration = format_duration(song['duration'])
        song_info = f"{song['name']} - {song['artist']} (专辑: {song['album']}, 时长: {song_duration})"
        song_button = tk.Button(result_window, text=song_info, command=lambda idx=idx: start_download(songs[idx]))
        song_button.pack(pady=5)

def start_download(song_info):
    song_id = song_info["id"]
    song_name = song_info["name"]
    artist = song_info["artist"]
    album = song_info["album"]
    url = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"

    log_text.delete(1.0, tk.END)
    log_text.insert(tk.END, f"正在下载《{song_name}》...\n")
    try:
        orig_path, size, duration = download_song(song_id)

        # 重命名文件
        safe_name = sanitize_filename(song_name)
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

        log_text.insert(tk.END, "\n下载日志：\n")
        log_text.insert(tk.END, "-" * 50 + "\n")
        log_text.insert(tk.END, f"歌曲：{song_name}\n")
        log_text.insert(tk.END, f"作者：{artist}\n")
        log_text.insert(tk.END, f"专辑：{album}\n")
        log_text.insert(tk.END, f"ID：{song_id}\n")
        log_text.insert(tk.END, f"URL：{url}\n")
        log_text.insert(tk.END, f"状态：{status}\n")
        log_text.insert(tk.END, f"大小：{size / 1024:.2f} KB\n")
        log_text.insert(tk.END, f"平均速度：{speed_kb:.2f} KB/s\n")
        log_text.insert(tk.END, "-" * 50 + "\n")

        messagebox.showinfo("下载完成", "歌曲下载完成！")

    except Exception as e:
        messagebox.showerror("下载错误", f"下载过程中出错：{e}")

def search():
    keyword = entry_keyword.get().strip()
    if not keyword:
        messagebox.showerror("错误", "歌曲名称不能为空。")
        return

    log_text.delete(1.0, tk.END)
    log_text.insert(tk.END, f"正在搜索《{keyword}》的歌曲...\n")
    songs = search_song_id(keyword)
    if not songs:
        messagebox.showerror("错误", "未找到匹配的歌曲，请换个关键词再试。")
        return

    display_search_results(songs)

# 创建GUI界面
root = tk.Tk()
root.title("网易云音乐歌曲下载器")

# 设置窗口大小
root.geometry("500x400")

# 输入框
label_keyword = tk.Label(root, text="请输入要下载的歌曲名称：")
label_keyword.pack(pady=10)

entry_keyword = tk.Entry(root, width=40)
entry_keyword.pack(pady=5)

# 搜索按钮
search_button = tk.Button(root, text="搜索歌曲", command=search)
search_button.pack(pady=20)

# 日志框
log_text = tk.Text(root, width=60, height=10, wrap=tk.WORD)
log_text.pack(pady=10)

# 运行界面
root.mainloop()
