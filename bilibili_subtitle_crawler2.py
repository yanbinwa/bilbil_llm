import json

import requests

'''
curl --location 'https://www.kedou.life/api/video/subtitleExtract' \
--header 'Content-Type: application/json' \
--data '{
    "url": "https://www.bilibili.com/video/BV1c5p4eZECv/?spm_id_from=333.337.search-card.all.click&vd_source=fa86269ec90326e1be9e108af037f6df"
}'
'''


def get_bilibili_subtitle(url):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
    }

    # 获取字幕信息
    subtitle_url = f'https://www.kedou.life/api/video/subtitleExtract'
    response = session.post(subtitle_url, headers=headers, json={'url': url})
    subtitle_info = json.loads(response.text)

    # 提取字幕列表
    subtitles = subtitle_info['data']['subtitleItemVoList'][0]['content']

    if not subtitles:
        return "该视频没有字幕。"

    # 通过'\n\n'分割 subtitles
    new_subtitles = []
    for sub_title in str.split(subtitles, '\n\n'):
        new_subtitles.append(str.split(sub_title, '\n')[-1])
    return '\n'.join(new_subtitles)


# 使用示例
if __name__ == '__main__':
    video_url = input("请输入B站视频URL: ")
    try:
        subtitle = get_bilibili_subtitle(video_url)
        print(subtitle)
    except Exception as e:
        print(f"获取字幕时出错: {str(e)}")
        print("请稍后再试或检查URL是否正确。")
