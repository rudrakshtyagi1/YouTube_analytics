import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import re


st.set_page_config(page_title="Defense Analytics", layout="wide", initial_sidebar_state="collapsed")


@st.cache_data
def load_data():
    
    candidates = ["clean_youtube_data.csv", "youtube_defense_data.csv", "clean_youtube_data.csv"]
    for f in candidates:
        if os.path.exists(f):
            return pd.read_csv(f)
    return pd.DataFrame()


def parse_iso_duration(s):
    if pd.isna(s):
        return np.nan
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", str(s))
    if not m:
        return np.nan
    h = int(m.group(1) or 0)
    mm = int(m.group(2) or 0)
    ss = int(m.group(3) or 0)
    return h * 3600 + mm * 60 + ss


df = load_data()
if df.empty:
    st.error("No data file found. Put `clean_youtube_data.csv` or `youtube_defense_data.csv` in the project folder.")
    st.stop()


for col in ["Views", "Likes", "Comments"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    else:
        df[col] = 0


if "Duration_Seconds" not in df.columns:
    if "Duration_ISO" in df.columns:
        df["Duration_Seconds"] = df["Duration_ISO"].apply(parse_iso_duration)
    else:
        df["Duration_Seconds"] = np.nan


if "Engagement_Rate_%" not in df.columns:
    
    df["Engagement_Rate_%"] = ((df["Likes"] + df["Comments"]) / df["Views"].replace(0, np.nan)) * 100
    df["Engagement_Rate_%"] = df["Engagement_Rate_%"].fillna(0)


if "Title" in df.columns:
    df["Short_Title"] = df["Title"].astype(str).apply(lambda x: x[:35] + "..." if len(x) > 35 else x)
    df["Clean_Title"] = df["Title"].astype(str)
else:
    df["Short_Title"] = df.index.astype(str)
    df["Clean_Title"] = df.index.astype(str)


st.markdown("<h1 style='text-align: center; color: #00f2fe;'>🛡️ Defense Tech YouTube Analytics</h1>", unsafe_allow_html=True)
st.markdown("---")


m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Videos Analyzed", len(df))
m2.metric("Total Market Views", f"{df['Views'].sum() / 1e6:.2f} M")
m3.metric("Average Engagement", f"{df['Engagement_Rate_%'].mean():.2f} %")
m4.metric("Top Channel", df.loc[df['Views'].idxmax()]['Channel'])

st.markdown("---")


st.sidebar.header("Filters & Settings")
min_views = st.sidebar.number_input("Minimum views", min_value=0, value=int(df["Views"].quantile(0.25)), step=100)
max_v = int(df["Views"].max()) if df["Views"].size else 0
top_n = st.sidebar.slider("Top N videos to show", 5, 50, 10)

top_channels = df["Channel"].value_counts().index.tolist()[:20]
selected_channels = st.sidebar.multiselect("Channels (top 20)", top_channels, default=top_channels[:5])

min_d = int(df["Duration_Seconds"].min(skipna=True) or 0)
max_d = int(df["Duration_Seconds"].max(skipna=True) or 0)
duration_range = st.sidebar.slider("Duration (seconds)", min_value=min_d, max_value=max_d, value=(min_d, max_d))


filtered = df.copy()
filtered = filtered[filtered["Views"] >= min_views]
if selected_channels:
    filtered = filtered[filtered["Channel"].isin(selected_channels)]
filtered = filtered[filtered["Duration_Seconds"].between(duration_range[0], duration_range[1], inclusive="both")]


st.title("YouTube EDA Dashboard")
st.markdown("Interactive exploratory analysis of your YouTube dataset. Use the sidebar to filter data.")


col1, col2, col3, col4 = st.columns(4)
col1.metric("Videos (filtered)", len(filtered))
col2.metric("Total Views", f"{int(filtered['Views'].sum()):,}")
col3.metric("Average Engagement %", f"{filtered['Engagement_Rate_%'].mean():.2f}%")
col4.metric("Median Duration (s)", f"{int(filtered['Duration_Seconds'].median(skipna=True) or 0)}")


col1, col2 = st.columns(2)


with col1:
    
    top_10 = df.sort_values('Views', ascending=False).head(10)
    fig1 = px.bar(top_10, x='Views', y='Short_Title', orientation='h',
                  title="1. Top 10 Videos by Sheer Volume",
                  hover_data={'Title': True, 'Short_Title': False}, # Shows full name only when mouse hovers
                  color_discrete_sequence=['#00f2fe'])
    fig1.update_layout(template="plotly_dark", yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    
    fig3 = px.scatter(df, x='Duration_Seconds', y='Engagement_Rate_%', size='Views',
                      title="3. Does Video Length Impact Engagement?",
                      hover_name='Clean_Title',
                      color_discrete_sequence=['#ff0844'], size_max=40)
    fig3.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig3, use_container_width=True)


with col2:
    
    fig2 = px.scatter(df, x='Views', y='Engagement_Rate_%', trendline="ols",
                      title="2. The Viral Trap: Views vs. Engagement",
                      hover_name='Clean_Title',
                      color_discrete_sequence=['#0ba360'])
    fig2.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    
    channel_views = df.groupby('Channel')['Views'].sum().reset_index().sort_values('Views', ascending=False).head(10)
    fig4 = px.bar(channel_views, x='Views', y='Channel', orientation='h',
                  title="4. Creator Dominance: Top Channels by Market Share",
                  color_discrete_sequence=['#ffb199'])
    fig4.update_layout(template="plotly_dark", yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig4, use_container_width=True)


with st.expander("Distributions", expanded=False):
    d1, d2 = st.columns(2)
    with d1:
        st.subheader("Views Distribution (log scale)")
        fig_hist = px.histogram(filtered[filtered['Views']>0], x='Views', nbins=50)
        fig_hist.update_xaxes(type='log')
        st.plotly_chart(fig_hist, use_container_width=True)
    with d2:
        st.subheader("Engagement Rate Distribution")
        fig_eng = px.histogram(filtered, x='Engagement_Rate_%', nbins=40)
        st.plotly_chart(fig_eng, use_container_width=True)


with st.expander("Correlation matrix", expanded=False):
    numeric = filtered.select_dtypes(include=[np.number])
    if not numeric.empty:
        corr = numeric.corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r')
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("No numeric columns available for correlation.")


st.subheader("Filtered data")
st.dataframe(filtered.reset_index(drop=True))

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(filtered)
st.download_button("Download filtered data as CSV", data=csv, file_name="filtered_youtube_data.csv", mime="text/csv")

st.markdown("---")
st.caption("EDA app powered by Streamlit — modify `visualize.py` to add more analyses.")