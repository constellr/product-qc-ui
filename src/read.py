import fsspec
import os
import json
import base64
import streamlit as st


fs = fsspec.filesystem('s3')


def make_collection(workflow_id='lst30-pipeline-v0.1.0-fmdc5'):
    parent_dir = f"s3://lst30-pipeline-product/{workflow_id}/"
    collection = {}

    # Listing the items that have been processed
    for path in fs.glob(parent_dir + "find-stac-items/*"):
        satellite = os.path.basename(path)
        if satellite == "ecostress":
            continue

        with fs.open(path + "/stac_items.json", 'r') as f:
            items = json.loads(f.read())

        for item in items:
            basename = os.path.basename(item["l1_item_href"])
            collection[basename] = {"satellite": satellite}

    # Adding metadata to the items
    for name, metadata in collection.items():
        metadata["workflow"] = {
            "cloud_mask": f"{parent_dir}{name}/get-cloud-mask/cloud_mask.tif",
            "lst_kelvin": f"{parent_dir}{name}/lst-process/lst_kelvin.tif",
            "metadata": f"{parent_dir}{name}/write-metadata/metadata.json"
        }
        with fs.open(f"{parent_dir}{name}/write-metadata/metadata.json", 'r') as f:
            metadata.update(json.loads(f.read()))
    
        metadata["workflow_id"] = workflow_id

    return collection

@st.cache_data
def make_collections(selected_workflows):
    collections = {}
    for selected_workflow in selected_workflows:
        collections.update(make_collection(workflow_id=selected_workflow))
    return collections


def open_image(path: str):
    with open(path, "rb") as p:
        file = p.read()
        return f"data:image/png;base64,{base64.b64encode(file).decode()}"
    

# def parse_json_old(path):
#     metadata = json.load(open(f"{path}/metadata.json"))
#     metadata["scene_datetime"] = pd.Timestamp(metadata["scene_datetime"])
#     metadata["scene_date"] = pd.Timestamp(metadata["scene_datetime"]).normalize()
#     metadata["invalid_pixel"] = metadata["cloud_cover"] + metadata["no_data"]
#     metadata["rgb"] = open_image(f"{path}/rgb.png")
#     metadata["lst"] = open_image(f"{path}/lst.png")
#     metadata["count"] = 1
#     metadata["viz"] = True
#     metadata["colors"] = 1
#     return metadata