import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from glob import glob
from plot import hist, ts
import numpy as np
import os

from argo import list_workflows
from read import make_collections, open_image, fs
from write import copy_file

# Input Selection
workflows = list_workflows(namespace="lst30-pipeline", workflow_template_name="lst30-pipeline-v0.1.0")
selected_workflows = st.multiselect(
    "Select workflows id",
    workflows,
    ["lst30-pipeline-v0.1.0-pq9wb", "lst30-pipeline-v0.1.0-2kp74"]
)

# Customer id and AOI name text inputs
customer_id = st.text_input("Customer Id")
aoi_name = st.text_input("Aoi Name")

# Applying input selection
collections = make_collections(selected_workflows)

is_collections = len(collections) > 0

if not is_collections:
    raise ValueError("No collections found, try another workflow id")


df = pd.DataFrame.from_dict(collections, orient='index')
df["datetime"] = pd.to_datetime(df["scene_datetime"])
datetime_range = (df['datetime'].min().to_pydatetime(), df['datetime'].max().to_pydatetime())
min_lst_range = (float(df["min_lst"].min()), float(df["min_lst"].max()))
max_lst_range = (float(df["max_lst"].min()), float(df["max_lst"].max()))
invalid_ratio_aoi_range = (float(df["invalid_ratio_aoi"].min()), float(df["invalid_ratio_aoi"].max()))
invalid_ratio_image_range = (float(df["invalid_ratio_image"].min()), float(df["invalid_ratio_image"].max()))


# Sidebar
with st.sidebar:
    st.title("Filters")
    st.write("[invalid-valid-invalid]")
    date_slider = st.slider('Dates ', min_value=datetime_range[0], max_value=datetime_range[1], value=datetime_range)
    sun_elevation_slider = st.slider('Sun elevation', min_value=-90, max_value=90, value=(10, 90))

    st.write("[valid-viz-invalid]")
    invalid_ratio_aoi_slider = st.slider('Invalid cover aoi', min_value=0, max_value=100, value=(0, 100))
    invalid_ratio_image_slider = st.slider('Invalid cover image', min_value=0, max_value=100, value=(0, 100))
    max_lst_slider = st.slider('Max LST', min_value=max_lst_range[0], max_value=max_lst_range[1], value=max_lst_range)

    st.write("[invalid-viz-valid]")
    min_lst_slider = st.slider('Min LST', min_value=min_lst_range[0], max_value=min_lst_range[1], value=min_lst_range)

    # Updating df_sliced
    df["default_selected"] = (
        (df["datetime"] >= date_slider[0]) & (df["datetime"] <= date_slider[1]) &
        (df["sun_elevation"] >= sun_elevation_slider[0]) & (df["sun_elevation"] <= sun_elevation_slider[1]) &
        (df["invalid_ratio_aoi"] <= invalid_ratio_aoi_slider[0]) &
        (df["invalid_ratio_image"] <= invalid_ratio_image_slider[0]) &
        (df["min_lst"] >= min_lst_slider[1]) &
        (df["max_lst"] <= max_lst_slider[0])
    )

    df["viz"] = (
        (df["invalid_ratio_aoi"] <= invalid_ratio_aoi_slider[1]) &
        (df["invalid_ratio_image"] <= invalid_ratio_image_slider[1]) &
        (df["min_lst"] >= min_lst_slider[0]) &
        (df["max_lst"] <= max_lst_slider[1]) & (~ df["default_selected"])
    )
    df_viz = df[df['viz']]


# Main panel
st.title("QC")
header = st.container()

# Dataframe selected for visualization
event = st.dataframe(
    df_viz,
    key=[0],
    # column_order=["rgb", "lst", "scene_datetime", "cloud_cover", "no_data", "sun_elevation", "atm_source"],
    # hide_index=True,
    on_select="rerun",
    selection_mode="multi-row",
    # column_config={
    #     "rgb": st.column_config.ImageColumn(width="small"),
    #     "lst": st.column_config.ImageColumn(width="small"),
    #     },
)

# Slicing selected rows
df_viz_selected = df_viz.iloc[event.selection.rows].index.tolist()
df.loc[df_viz_selected, "colors"] = 1
df_selected = pd.concat([
    df.loc[df_viz_selected],
    df.loc[df["default_selected"]]
])
df["colors"] = df["default_selected"].astype(int)
df.loc[df['viz'] & (df['default_selected'] == 0), "colors"] = 2
df["colors"] = df["colors"].map({0: "Rejected", 1: "Validated", 2: "TBD"})   

# Header - image count update
header.header(f"{len(df_viz_selected)}/{len(df)} Images")

# Time-serie plot
header.altair_chart(ts(df), use_container_width=True)

# Histograms
columns_hists = ["invalid_ratio_aoi", "invalid_ratio_image", "min_lst", "max_lst", "median_lst"]
df_hists = pd.concat([
    df[columns_hists].assign(origin='all'),
    df_selected[columns_hists].assign(origin='selected')
], ignore_index=True)

for col in columns_hists:
    header.altair_chart(
        hist(df_hists, col, bins=20),
        use_container_width=True
    )

# Upload button
button = st.button("Done")
if button:

    assert customer_id is not None, "Customer Id is required"
    assert aoi_name is not None, "Aoi Name is required"
    assert len(df_selected) > 0, "You haven't selected any image to provide to the client"

    for index, paths, workflow_id in zip(df_selected.index, df_selected["workflow"], df_selected["workflow_id"]):
        for in_path in paths.values():
            out_path = f"s3://data-delivery-213979744349/{customer_id}/{aoi_name}/{workflow_id}/{index}/{os.path.basename(in_path)}"
            st.write("saving", in_path, "to", out_path)
            # copy_file(in_path, out_path)

