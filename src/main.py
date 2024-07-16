import random
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from glob import glob
import json
import base64
import altair as alt


def open_image(path: str):
    with open(path, "rb") as p:
        file = p.read()
        return f"data:image/png;base64,{base64.b64encode(file).decode()}"


def parse_json(path):
    metadata = json.load(open(f"{path}/metadata.json"))
    metadata["scene_datetime"] = pd.Timestamp(metadata["scene_datetime"])
    metadata["scene_date"] = pd.Timestamp(metadata["scene_datetime"]).normalize()
    metadata["valid_pixel"] = 100 - metadata["cloud_cover"] - metadata["no_data"]
    metadata["rgb"] = open_image(f"{path}/rgb.png")
    metadata["lst"] = open_image(f"{path}/lst.png")
    metadata["count"] = 1
    return metadata

@st.cache_data
def load():
    df = pd.DataFrame([parse_json(d) for d in glob("tests/fixtures/*")])
    return df
df = load()


with st.sidebar:
    st.title("Filters")
    min_date = df["scene_date"].min().to_pydatetime()
    max_date = df["scene_date"].max().to_pydatetime()
    slider = st.slider('Dates', min_value=min_date, max_value=max_date, value=[min_date, max_date])
    cloud_cover = st.slider('Cloud cover', min_value=0, max_value=100, value=100)
    na_cover = st.slider('No data cover', min_value=0, max_value=100, value=100)
    valid_cover = st.slider('Valid cover', min_value=0, max_value=100, value=100)
    sun_elevation = st.slider('Sun elevation', min_value=-90, max_value=90, value=(10, 90))

df["sclicing"] = (
    (df["scene_date"] >= slider[0]) & (df["scene_date"] <= slider[1]) &
    (df["cloud_cover"] <= cloud_cover) &
    (df["no_data"] <= na_cover) &
    (df["valid_pixel"] <= valid_cover) &
    (df["sun_elevation"] >= sun_elevation[0]) & (df["sun_elevation"] <= sun_elevation[1])
)


# time_count = df.groupby(pd.Grouper(key='scene_datetime', freq='1d')).size().reset_index(name='count')
# time_count["highlight"] = (time_count["scene_datetime"] >= slider[0]) & (time_count["scene_datetime"] <= slider[1])

st.title("QC")
st.header(f"{df['sclicing'].sum()}/{len(df)} Images")

# Create the histogram with Altair
histogram = alt.Chart(df).mark_bar().encode(
    x=alt.X('scene_datetime:T', title=''),
    y=alt.Y('count:Q', title=''),
    color=alt.condition(
        alt.datum.sclicing,
        alt.value('#ff4242'),
        alt.value('#343840')
    )
).properties(height=60).configure_axisY(grid=False, labels=False)

st.altair_chart(histogram, use_container_width=True)

df_sliced = df[df['sclicing']]
event = st.dataframe(
    df_sliced,
    key=[0],
    column_order=["rgb", "lst", "scene_datetime", "cloud_cover", "no_data", "sun_elevation", "atm_source"],
    hide_index=True,
    on_select="rerun",
    selection_mode="multi-row",
    column_config={
        "rgb": st.column_config.ImageColumn(width="small"),
        "lst": st.column_config.ImageColumn(width="small"),
        }
)


button = st.button("Done")
if button:
    st.write(f"You selected the following rows: {event.selection.rows}")
