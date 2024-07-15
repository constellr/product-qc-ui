import streamlit as st
from streamlit_folium import st_folium
import geopandas as gpd
import fsspec
from datetime import datetime, timedelta, date
import re




fields = list_fields()
customers = sorted([i["name"] for i in fields['Organisation']["options"]])
today = datetime.now()
previous_2_weeks = today - timedelta(weeks=2)
next_1_months = today + timedelta(weeks=4)
next_6_months = today + timedelta(weeks=26)


form_default = {
    "organisation": None,
    "contact": "",
    "contract_type": 0,
    "contract_status": 0,
    "order_type": 0,
    "paid_order": 0,
    "constellr_contact": "",
    "requested_order": 'Single Order',
    "requested_period": (previous_2_weeks, today),
    "requested_delivery": next_1_months,
    "delivery_method": 0,
    "comment": "",
    "aoi": None,
}

st.session_state["error"] = {}
st.session_state["output"] = {}
st.session_state["output"]["today"] = today


# Some User text need to be checked if they have been filled
def st_text_input_validated(key, **kwargs):
    kwargs.update({"value": form_default[key]})
    st.session_state["output"][key] = st.text_input(**kwargs)
#     st.session_state["error"][key] = st.empty()

def is_kebab_case(string):
    pattern = r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$'
    return re.match(pattern, string) is not None

# suggestion
# st_datalist

st.header("Customer Request Form")

# Client Information
with st.expander("Client Information"):

    # If existing client, select from the list, if not, input the name
    new_client = st.radio(
        label="Existing client",
        options=["Yes", "No"],
        index=0
    )

    if new_client == "No":
        organisation = st.text_input(value=form_default["organisation"], label="Organisation Name")        
    else:
        organisation = st.selectbox("Organisation Name", options=customers, index=form_default["organisation"])
    st.session_state["error"]["organisation"] = st.empty()

    # Check for kebab-case format
    if (organisation is None) or (organisation == ""):
        pass
    elif is_kebab_case(organisation):
        st.session_state["output"]["organisation"] = organisation
    else:
        st.session_state["error"]["organisation"].error("Not 'kebab-case' format")
    
    # Contact Information
    st.session_state["output"]["contact"] = st.text_input(value=form_default["contact"], label="Person of contact from the organisation")
    st.session_state["error"]["contact"] = st.empty()

    st.session_state["output"]["contract_type"] = st.radio(
        label="Contract Type",
        options=["EAP", "Single Order"],
        index=form_default["contract_type"]
    )
    st.session_state["output"]["contract_status"] = st.radio(
        label="Contract Status",
        options=["Confirmed", "Pending"],
        index=form_default["contract_status"]
    )
    st.session_state["output"]["paid_order"] = st.radio(
        label="Paid Order",
        options=["Yes", "No"],
        index=form_default["paid_order"]
    )
    st.session_state["output"]["constellr_contact"] = st.text_input(value=form_default["constellr_contact"], label="Constellr Person of contact")

# Order Information
with st.expander("Order Information"):

    st.session_state["output"]["order_type"] = st.radio(
        label="Order Type",
        options=["LST", "ET", "Analytics"],
        index=form_default["order_type"]
    )

    st.session_state["output"]["requested_order"] = st.multiselect(
        'Requested Order Type',
        [
            'Single Order',
            'Watch Order'
        ],
        default=form_default["requested_order"]
    )
    st.session_state["output"]["requested_period"] = st.date_input(
        "Requested period",
        value=form_default["requested_period"], # Default range
        min_value=date(2016, 1, 1), # Min date
        max_value=today, # Max date
        format="YYYY/MM/DD",
    )
    st.session_state["output"]["requested_delivery"] = st.date_input(
        "Expected delivery date",
        value=form_default["requested_delivery"], # Default date
        min_value=today, # Min date
        max_value=next_6_months, # Max date
        format="YYYY/MM/DD",
    )
    st.session_state["output"]["delivery_method"] = st.radio(
        label="Prefered delivery method",
        options=["Download link", "API (not available yet)"],
        index=form_default["delivery_method"]
    )
    st.session_state["output"]["comment"] = st.text_area("Comment", form_default["comment"])

# AOI Information
with st.expander("AOI Uploader"):
    tab_draw, tab_upload, tab_uploads = st.tabs(["Draw AOI", "Upload Single AOI file (beta)", "Upload Multiple AOI files"])
    
    with tab_draw:
        st.header("Draw AOI")
        single_file = True
        aoi = None

        m_data = st_folium(draw_aoi_on_map(), use_container_width=True, height=500)
        
        if m_data["all_drawings"]:
            aoi = gpd.GeoDataFrame.from_features(m_data["all_drawings"])

    with tab_upload:
        st.header("Upload Single AOI file")
        st.markdown("Upload a single file, that may contain multiple AOIs.")
        st.markdown("It allows for visaualisation/editing/preprocessing of the AOIs and minimize the operator work.")
        uploaded_file = st.file_uploader("Upload GeoJSON:", type=["json", "geojson", "zip", "gpkg"])

        if uploaded_file:
            # Read AOI
            single_file = True
            aoi = None
            aoi = read_uploaded_file(uploaded_file)

            # Buffering
            buffer = st.number_input("Buffer", min_value=0, max_value=10000, step=100)
            if buffer > 0:
                aoi = aoi.to_crs(aoi.estimate_utm_crs())
                aoi.geometry = aoi.geometry.buffer(buffer, join_style=2)
                aoi = aoi.to_crs(4326)

            # Dissolving
            col1, col2 = st.columns(2)
            with col1:
                is_dissolving = st.checkbox("Dissolving")
            with col2:
                if is_dissolving:
                    dissolving = st.selectbox("Dissolving", [None] + list(aoi.columns))
                    aoi = aoi.dissolve(dissolving)

            st.header("Data Editing")
            aoi = edit_table(aoi)

            st.header("Dynamic map")
            if aoi.shape[0] > 0:
                st_folium(display_aoi_on_map(aoi), use_container_width=True, height=500)
            else:
                st.markdown("**:red[No shape to show]**")

    with tab_uploads:
        st.header("Upload Multiple AOI files")
        st.markdown("Upload a multiple files, that may contain multiple AOIs.")
        st.markdown("No pre-processing or visualization is available for this option, the preprocessing will be done by the operator.")
        uploaded_file = st.file_uploader("Upload files:", accept_multiple_files=True)

        if uploaded_file:
            # Read AOI
            single_file = False
            aoi = uploaded_file.copy()
            # for i in uploaded_file:
            #     print(i.name)
            #     # print(i.getvalue())

            if aoi is None:
                st.markdown("**:red[No file to upload]**")

                

submit = st.button("Submit")

if submit:
    # Checking that what needed to be answered has been answered
    not_answered = []
    
    for key in st.session_state["error"].keys():
        if st.session_state["output"][key] == form_default[key]:
            not_answered.append(key)
            st.session_state["error"][key].error("Required")
    
    if aoi is None:
        not_answered.append("AOI")
    elif len(aoi) == 0:
        not_answered.append("AOI")

    # In case there are no missing informations, the issue is created and aoi saved
    if len(not_answered) > 0:
        st.markdown(f"**:red[The following informations are missing {not_answered}]**")
    else:
        # Saving aoi
        if single_file:
            aoi_name = st.session_state["output"]["organisation"] + "_" + today.strftime("%F") + ".geojson"
            aoi_path = f"s3://constellr-product-segment/form/{aoi_name}"
            
            with fsspec.open(aoi_path, "wb") as f:
                aoi.to_file(f, driver="GeoJSON")

            st.session_state["output"]["aoi"] = f"aws s3 cp {aoi_path} ."
        else:
            aoi_name = st.session_state["output"]["organisation"] + "_" + today.strftime("%F")
            aoi_dir = f"s3://constellr-product-segment/form/{aoi_name}/"

            for i in uploaded_file:
                aoi_path = aoi_dir + i.name
                with fsspec.open(aoi_path, "wb") as f:
                    f.write(i.getvalue())
                print("upload", aoi_path)
            st.session_state["output"]["aoi"] = f"aws s3 cp --recursive {aoi_dir} ."

        # Creating issue
        title = format_title(st.session_state["output"])
        body = format_body(st.session_state["output"])

        update = form_to_github(st.session_state["output"])
        issue_id = creating_issue(title, body)
        issue_project_id = attributing_issue(issue_id)

        st.markdown("**:green[Your request has been sent!]**")
