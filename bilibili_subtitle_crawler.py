import requests
import re
import json
import time

def get_bilibili_subtitle(url):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
    }
    
    # 获取视频的bvid
    bvid = re.search(r'BV\w+', url).group()
    
    # 获取视频信息
    video_info_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    response = session.get(video_info_url, headers=headers)
    video_info = json.loads(response.text)
    
    # 获取cid
    cid = video_info['data']['cid']
    
    # 获取字幕信息
    subtitle_url = f'https://api.bilibili.com/x/player/v2?cid={cid}&bvid={bvid}'
    response = session.get(subtitle_url, headers=headers)
    subtitle_info = json.loads(response.text)
    
    # 提取字幕列表
    subtitles = subtitle_info['data']['subtitle']['subtitles']
    
    if not subtitles:
        return "该视频没有字幕。"
    
    # 获取第一个字幕的URL（通常是默认字幕）
    subtitle_download_url = f'https:{subtitles[0]["subtitle_url"]}'
    
    # 下载字幕内容
    response = session.get(subtitle_download_url, headers=headers)
    subtitle_content = json.loads(response.text)
    
    # 提取字幕文本
    subtitle_text = '\n'.join([item['content'] for item in subtitle_content['body']])
    
    return subtitle_text

# 使用示例
if __name__ == '__main__':
    video_url = input("请输入B站视频URL: ")
    try:
        subtitle = get_bilibili_subtitle(video_url)
        print(subtitle)
    except Exception as e:
        print(f"获取字幕时出错: {str(e)}")
        print("请稍后再试或检查URL是否正确。")
