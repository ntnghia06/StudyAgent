from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
ytt_api = YouTubeTranscriptApi()

def get_youtube_video_id(url):
    """Sử dụng yt-dlp để lấy ID video một cách an toàn nhất"""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("id"), info.get("title")

url = r"https://www.youtube.com/watch?v=h3H5qfN-ifY"
info = get_youtube_video_id(url)
# retrieve the available transcripts
transcript_list = ytt_api.list(info[0])

# iterate over all available transcripts
for transcript in transcript_list:
    # # fetch the actual transcript data
    data = transcript.fetch()
    # # translating the transcript will return another transcript object
    text_content = " ".join([item.text for item in data.snippets])
    
    print(text_content)
