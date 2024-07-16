
import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import base64
from streamlit import session_state as ss

if "style_data" not in ss:
    ss.style_data = []

if "input_style" not in ss:
    ss.input_style = ''

# Streamlit configuration
st.set_page_config(layout="wide")

# Define API URL
API_URL = "http://localhost:8000"

# Function to fetch style info from backend
def fetch_style(style):
    try:
        response = requests.get(f"{API_URL}/style/{style}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Style not found")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

def get_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error fetching image from URL: {e}")
        return None

def get_thumbnail(url):
    img = get_image_from_url(url)
    if img:
        img.thumbnail((200, 200))
    return img

def image_to_base64(img):
    if img:
        with BytesIO() as buffer:
            img.save(buffer, 'jpeg') 
            return base64.b64encode(buffer.getvalue()).decode()

def image_formatter(url):
    img = get_thumbnail(url)
    if img:
        return f'<img src="data:image/jpeg;base64,{image_to_base64(img)}">'

@st.cache_data
def convert_df(input_df):
     return input_df.to_html(escape=False, formatters=dict(thumbnail=image_formatter))

def new_styles_cb():
    """Append data to style_data from selection."""
    ss.style_data.insert(0,
        {
            "styleno": ss.styleno,
            "imagelink": ss.imagelink
        }
    )

def fetch_data():
    style_info = fetch_style(ss.input_style)
    # Display style information in a table
    if style_info:
        list_data = list((style_info.values()))
        ss.styleno = list_data[0]
        ss.imagelink = list_data[1]
        new_styles_cb()
        ss.input_style = ''

# Streamlit UI
st.title("Style Information")

# Input form for style number
st.text_input("Enter Style Number", key='input_style', on_change=fetch_data)
 

if (len(ss.style_data)) > 0:

    df_data = pd.DataFrame(ss.style_data)
    df_data['thumbnail'] = df_data['imagelink']

    html_view = convert_df(df_data)
    st.markdown(
        html_view,
        unsafe_allow_html=True
    )


# import streamlit as st
# import pandas as pd

# st.title('🎈 Image Table Demo')

# df = pd.DataFrame(
#     [
#         [2768571, 130655, 1155027, 34713051, 331002277],
#         [1448753, 60632, 790040, 3070447, 212558178],
#         [654405, 9536, 422931, 19852167, 145934619],
#         [605216, 17848, 359891, 8826585, 1379974505],
#         [288477, 9860, 178245, 1699369, 32969875],
#     ],
#     columns=[
#         "Total Cases",
#         "Total Deaths",
#         "Total Recovered",
#         "Total Tests",
#         "Population",
#     ],
# )

# # Create a list named country to store all the image paths
# country = [
#     "/Users/jonasberhin/Documents/product-qc-ui/tests/fixtures/img1/img.png",
#     "/Users/jonasberhin/Documents/product-qc-ui/tests/fixtures/img1/img.png",
#     "/Users/jonasberhin/Documents/product-qc-ui/tests/fixtures/img1/img.png",
#     "/Users/jonasberhin/Documents/product-qc-ui/tests/fixtures/img1/img.png",
#     "/Users/jonasberhin/Documents/product-qc-ui/tests/fixtures/img1/img.png",
# ]
# # Assigning the new list as a new column of the dataframe
# df["Country"] = country

# # Converting links to html tags
# def path_to_image_html(path):
#     return '<img src="' + path + '" width="60" >'

# # @st.cache
# def convert_df(input_df):
#      # IMPORTANT: Cache the conversion to prevent computation on every rerun
#      return input_df.to_html(escape=False, formatters=dict(Country=path_to_image_html))

# html = convert_df(df)

# st.markdown(
#     html,
#     unsafe_allow_html=True
# )
