from googleapiclient.discovery import build
import pandas as pd
import json

API_KEY = "REDACTED" 

print("🚀 Engine Started: Calling YouTube Servers...")
youtube = build('youtube', 'v3', developerKey=API_KEY)


search_query = "Indian Armed Forces Tech"
search_response = youtube.search().list(
    q=search_query,
    part="id",
    type="video",
    maxResults=50 
).execute()


video_ids = [item['id']['videoId'] for item in search_response['items']]
print(f"✅ Found {len(video_ids)} videos. Fetching detailed analytics...")


video_response = youtube.videos().list(
    part="snippet,statistics,contentDetails",
    id=",".join(video_ids) 
).execute()


video_data = []
for item in video_response['items']:
    data = {
        'Video_ID': item['id'],
        'Title': item['snippet']['title'],
        'Channel': item['snippet']['channelTitle'],
        'Published_At': item['snippet']['publishedAt'],
        
        
        'Views': int(item['statistics'].get('viewCount', 0)),
        'Likes': int(item['statistics'].get('likeCount', 0)),
        'Comments': int(item['statistics'].get('commentCount', 0)),
        
        
        'Duration_ISO': item['contentDetails']['duration'] 
    }
    video_data.append(data)


df = pd.DataFrame(video_data)

print("\n📊 DATA FETCHED SUCCESSFULLY (Preview):")
print(df[['Title', 'Views', 'Duration_ISO']].head())

filename = "youtube_defense_data.csv"
df.to_csv(filename, index=False)
print(f"\n📁 MAGIC DONE! File saved as '{filename}' in your folder!")