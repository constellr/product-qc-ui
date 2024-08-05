import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from glob import glob
import json
import base64
import altair as alt
import numpy as np


def open_image(path: str):
    with open(path, "rb") as p:
        file = p.read()
        return f"data:image/png;base64,{base64.b64encode(file).decode()}"


def parse_json(path):
    metadata = json.load(open(f"{path}/metadata.json"))
    metadata["scene_datetime"] = pd.Timestamp(metadata["scene_datetime"])
    metadata["scene_date"] = pd.Timestamp(metadata["scene_datetime"]).normalize()
    metadata["invalid_pixel"] = metadata["cloud_cover"] + metadata["no_data"]
    metadata["rgb"] = open_image(f"{path}/rgb.png")
    metadata["lst"] = open_image(f"{path}/lst.png")
    metadata["count"] = 1
    metadata["viz"] = True
    metadata["colors"] = 1
    return metadata


def hist(df, col, bins=20):
    assert col in df.columns, f"Column {col} not found"
    assert "origin" in df.columns, "Column 'origin' not found"

    return alt.Chart(df).mark_bar(color="red").encode(
        alt.X(col, bin=True),
        alt.Y('count()', stack=None),
        alt.Color('origin', scale=alt.Scale(
            domain=["all", "selected"],
            range=['mistyrose', 'red']
        ))
    ).properties(height=200).configure_axisY(grid=False, labels=False)


def ts():
    return alt.Chart(df).mark_circle(size=300).encode(
        x=alt.X('scene_datetime:T', title=''),
        y=alt.Y('lst_median:Q', title='LST Median'),
        color=alt.Color('colors:N', scale=alt.Scale(
            domain=["Rejected", "Validated", "TBD"],
            range=['red', 'lime', 'orange']
            )
        )
        ).properties(
            height=300,
            width=600
        )


# @st.cache_data
def load():
    df = df = pd.DataFrame([parse_json(d) for d in glob("tests/fixtures/*")])
    min_date = df["scene_date"].min().to_pydatetime()
    max_date = df["scene_date"].max().to_pydatetime()
    lst_min = float(df["lst_min"].min())
    lst_max = float(df["lst_max"].max())
    df_viz_selected = []
    df_viz = df[df['viz']]
    df_selected = []
    return df, min_date, max_date, lst_min, lst_max, df_viz_selected, df_viz, df_selected


df, min_date, max_date, lst_min, lst_max, df_viz_selected, df_viz, df_selected = load()

# Sidebar
with st.sidebar:
    st.title("Filters")
    date_slider = st.slider('Dates', min_value=min_date, max_value=max_date, value=[min_date, max_date])
    cloud_cover = st.slider('Cloud cover', min_value=0, max_value=100, value=(0, 100))
    na_cover = st.slider('No data cover', min_value=0, max_value=100, value=(0, 100))
    invalid_cover = st.slider('Invalid cover', min_value=0, max_value=100, value=(0, 100))
    sun_elevation = st.slider('Sun elevation', min_value=-90, max_value=90, value=(10, 90))
    lst_min_slider = st.slider('Min LST', min_value=lst_min, max_value=lst_max, value=(lst_min, lst_max))
    lst_max_slider = st.slider('Max LST', min_value=lst_min, max_value=lst_max, value=(lst_min, lst_max))

    # Updating df_sliced
    df["viz"] = (
        (df["scene_date"] >= date_slider[0]) & (df["scene_date"] <= date_slider[1]) &
        (df["cloud_cover"] >= cloud_cover[0]) & (df["cloud_cover"] <= cloud_cover[1]) &
        (df["no_data"] >= na_cover[0]) & (df["no_data"] <= na_cover[1]) &
        (df["invalid_pixel"] >= invalid_cover[0]) & (df["invalid_pixel"] <= invalid_cover[1]) &
        (df["lst_min"] >= lst_min_slider[0]) & (df["lst_min"] <= lst_min_slider[1]) &
        (df["lst_max"] >= lst_max_slider[0]) & (df["lst_max"] <= lst_max_slider[1]) &
        (df["sun_elevation"] >= sun_elevation[0]) & (df["sun_elevation"] <= sun_elevation[1])
    )

    df["default_selected"] = (
        (df["scene_date"] >= date_slider[0]) & (df["scene_date"] <= date_slider[1]) &
        (df["cloud_cover"] <= cloud_cover[0]) &
        (df["no_data"] <= na_cover[0]) &
        (df["invalid_pixel"] <= invalid_cover[0]) &
        (df["lst_min"] <= lst_min_slider[0]) &
        (df["lst_max"] >= lst_max_slider[1]) &
        (df["sun_elevation"] >= sun_elevation[0]) & (df["sun_elevation"] <= sun_elevation[1])
    )

    df["colors"] = df["default_selected"].map({True: "Validated", False: "Rejected"})
    df.loc[df['viz'], "colors"] = "TBD"
    df_viz = df[df['viz']]


# Main panel
st.title("QC")
header = st.container()

event = st.dataframe(
    df_viz,
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
df_viz_selected = df_viz.iloc[event.selection.rows].index.tolist()

# Header - image count update
header.header(f"{len(df_viz_selected)}/{len(df)} Images")

# Header - timeline update


df.loc[df_viz_selected, "colors"] = 1
df_selected = pd.concat([
    df.loc[df_viz_selected],
    df.loc[df["default_selected"]]
])

# header.altair_chart(timeline(), use_container_width=True)
header.altair_chart(ts(), use_container_width=True)

columns_hists = ["cloud_cover", "invalid_pixel", "lst_min", "lst_max", "lst_median"]
df_hists = pd.concat([
    df[columns_hists].assign(origin='all'),
    df_selected[columns_hists].assign(origin='selected')
], ignore_index=True)

header.altair_chart(
    hist(df_hists, 'cloud_cover', bins=20),
    use_container_width=True
)
header.altair_chart(
    hist(df_hists, 'invalid_pixel', bins=20),
    use_container_width=True
)
header.altair_chart(
    hist(df_hists, 'lst_min', bins=20),
    use_container_width=True
)
header.altair_chart(
    hist(df_hists, 'lst_median', bins=20),
    use_container_width=True
)
header.altair_chart(
    hist(df_hists, 'lst_max', bins=20),
    use_container_width=True
)

# Upload button
button = st.button("Done")
if button:
    if len(df_selected) > 0:
        st.write(f"You selected the following rows: {df_viz_selected}")
    else:
        st.write("You need to select the rows you want to provide to the client")
