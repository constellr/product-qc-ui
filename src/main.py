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
    metadata["sclicing"] = True
    metadata["colors"] = 1
    return metadata


def timeline():
    # Histogram/timeline
    return alt.Chart(st.session_state.df).mark_bar().encode(
        x=alt.X('scene_datetime:T', title=''),
        y=alt.Y('count:Q', title=''),
        color=alt.Color('colors', scale=alt.Scale(
            domain=[0, 1, 2],
            range=['#343840', '#ffc2c2', "#ff4242"]
            ),
        legend=None
            )
        ).properties(height=60).configure_axisY(grid=False, labels=False)
    

def ts():
    return alt.Chart(st.session_state.df).mark_circle(size=60).encode(
        x=alt.X('scene_datetime:T', title=''),
        y=alt.Y('lst_median:Q', title='LST Median'),
        color=alt.Color('colors:N', scale=alt.Scale(
            domain=[0, 1, 2],
            range=['#343840', '#ffc2c2', '#ff4242']
            ),
            legend=None
        )
        ).properties(
            height=300,
            width=600
        )




@st.cache_data
def load():
    df = df = pd.DataFrame([parse_json(d) for d in glob("tests/fixtures/*")])
    min_date = df["scene_date"].min().to_pydatetime()
    max_date = df["scene_date"].max().to_pydatetime()
    selected = []
    df_sliced = df[df['sclicing']]
    return df, min_date, max_date, selected, df_sliced

st.session_state.df, st.session_state.min_date, st.session_state.max_date, st.session_state.selected, st.session_state.df_sliced = load()

# Sidebar
with st.sidebar:
    st.title("Filters")
    date_slider = st.slider('Dates', min_value=st.session_state.min_date, max_value=st.session_state.max_date, value=[st.session_state.min_date, st.session_state.max_date])
    cloud_cover = st.slider('Cloud cover', min_value=0, max_value=100, value=100)
    na_cover = st.slider('No data cover', min_value=0, max_value=100, value=100)
    valid_cover = st.slider('Valid cover', min_value=0, max_value=100, value=100)
    sun_elevation = st.slider('Sun elevation', min_value=-90, max_value=90, value=(10, 90))

    # Updating df_sliced
    st.session_state.df["sclicing"] = (
        (st.session_state.df["scene_date"] >= date_slider[0]) & (st.session_state.df["scene_date"] <= date_slider[1]) &
        (st.session_state.df["cloud_cover"] <= cloud_cover) &
        (st.session_state.df["no_data"] <= na_cover) &
        (st.session_state.df["valid_pixel"] <= valid_cover) &
        (st.session_state.df["sun_elevation"] >= sun_elevation[0]) & (st.session_state.df["sun_elevation"] <= sun_elevation[1])
    )
    st.session_state.df_sliced = st.session_state.df[st.session_state.df['sclicing']]


# Main panel
st.title("QC")
header = st.container()

event = st.dataframe(
    st.session_state.df_sliced,
    key=[0],
    column_order=["rgb", "lst", "scene_datetime", "cloud_cover", "no_data", "sun_elevation", "atm_source"],
    hide_index=True,
    on_select="rerun",
    selection_mode="multi-row",
    column_config={
        "rgb": st.column_config.ImageColumn(width="small"),
        "lst": st.column_config.ImageColumn(width="small"),
        },
)

# Slicing selected rows
st.session_state.df_selected = st.session_state.df_sliced.iloc[event.selection.rows]
st.session_state.selected = st.session_state.df_selected.index.tolist()

# Header - image count update
header.header(f"{len(st.session_state.df_selected)}/{len(st.session_state.df)} Images")

# Header - timeline update
st.session_state.df["colors"] = st.session_state.df["sclicing"].astype(int)
st.session_state.df.loc[st.session_state.selected, "colors"] = 2
# header.altair_chart(timeline(), use_container_width=True)
header.altair_chart(ts(), use_container_width=True)


# Upload button
button = st.button("Done")
if button:
    if "df_selected" in st.session_state.keys():
        st.write(f"You selected the following rows: {st.session_state.selected}")
    else:
        st.write(f"You need to select the rows you want to provide to the client")
