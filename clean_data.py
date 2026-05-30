import pandas as pd
import re

print("🧹 Cleaning Engine Started...")


df = pd.read_csv("youtube_defense_data.csv")


def convert_to_seconds(duration):
    
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    seconds = re.search(r'(\d+)S', duration)
    
    h = int(hours.group(1)) if hours else 0
    m = int(minutes.group(1)) if minutes else 0
    s = int(seconds.group(1)) if seconds else 0
    
    return h * 3600 + m * 60 + s


df['Duration_Seconds'] = df['Duration_ISO'].apply(convert_to_seconds)


df['Engagement_Rate_%'] = ((df['Likes'] + df['Comments']) / df['Views']) * 100


df = df.drop(columns=['Duration_ISO'])


clean_filename = "clean_youtube_data.csv"
df.to_csv(clean_filename, index=False)

print("\n✨ DATA CLEANED & UPGRADED!")
print(df[['Title', 'Duration_Seconds', 'Engagement_Rate_%']].head())
print(f"\n📁 Saved as '{clean_filename}'")