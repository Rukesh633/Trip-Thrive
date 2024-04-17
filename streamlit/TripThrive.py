import os
from geopy.geocoders import Nominatim
import TripThrive2  # Importing the other Python file
from pymongo import MongoClient
import streamlit as st
from usellm import UseLLM, Message, Options
from utils1 import TRIP_PLANNER_SYSTEM
from utils1 import format_trip_planner_message
import streamlit_antd_components as sac
from streamlit_geolocation import streamlit_geolocation
from streamlit_extras.stylable_container import stylable_container
import csv
from geopy.geocoders import Nominatim

service = UseLLM(service_url="https://usellm.org/api/llm")

st.set_page_config(layout='wide')


video_html = """
		<style>

		#myVideo {
		  position: fixed;
		  right: 0;
		  bottom: 0;
		  min-width: 100%; 
		  min-height: 100%;
		}


		.content {
		  position: fixed;
		  bottom: 0;
		  background: rgba(0, 0, 0, 0.5);
		  color: #f1f1f1;
		  width: 100%;
		  padding: 20px;

		}

		</style>
		<video autoplay muted loop id="myVideo">
		  <source src="https://static.streamlit.io/examples/star.mp4")>
		  Your browser does not support HTML5 video.
		</video>
        """

st.markdown(video_html, unsafe_allow_html=True)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['tripdb']

# Custom CSS for styling input box
custom_css = """
    <style>
        .stTextInput input[type="text"] {
            background-color: #0B232F !important;
            border: 1px solid white !important; /* Set initial border color to transparent */
            font-size: 25px !important;
            font-weight: bold !important;
            color: white !important;
            position: absolute !important;
            border-radius:12px;
            z-index: 1 !important; /* Ensure the text input field appears over the video */
            transition: border-color 0.3s ease; /* Add smooth transition for border color change */
        }
        .st-b0{
        width:340px !important;
        }
        
        .stTextInput {
            width: 342px !important;
            height: 90px !important;
        }
        div[data-testid="stNumberInputContainer"] {
            background: transparent !important;
            border: 1px solid white !important; /* Set initial border color to transparent */
            width:150px !important;
            color: white !important;
            height:50px !important;
        }
        div[data-testid="element-container"] p{
            font-size:20px !important;
        }
        div[data-testid="element-container"] li{
            font-size:20px !important;
        }
        div[data-testid="stImage] img{
        width:50%;
        margin-left:10px;
        }
        

    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


class stylable_container:
    def __init__(self, css_styles):
        self.css_styles = css_styles

    def __enter__(self):
        for css_style in self.css_styles:
            st.markdown(f"<style>{css_style}</style>", unsafe_allow_html=True)

    def __exit__(self, type, value, traceback):
        pass


def update_sidebar_user(user_input):
    if user_input:
        st.sidebar.markdown(f'<div class="place-block" style="text-align: center;">{user_input}</div>',
                            unsafe_allow_html=True)
    else:
        user_data_path = os.path.join(os.path.dirname(__file__), '..', 'user_data.txt')

        with open(user_data_path, 'r') as user_data_file:
            username = user_data_file.read().strip()

        if username:
            user_data = db.users.find_one({"username": username})
            if user_data:
                trips = user_data.get("trips", [])
                if trips:
                # if "trips" in user_data:
                    # trips = user_data["trips"]
                    st.sidebar.markdown(
                        '<div style="margin-bottom: 10px; font-weight: bold; font-size: 43px; text-align: left; display: flex; align-items: center;">' +
                        '<img src="https://raw.githubusercontent.com/Mallika2002/OCTANET_JUNE/main/logo_1-removebg.png" ' +
                        'style="width: 60px; height: 60px; margin-right: 10px;">' +
                        '<span style="color: pink;">T</span>' +
                        '<span style="color: white;">rip</span>' +
                        '<span style="color: pink;">T</span>' +
                        '<span style="color: white;">hrive</span>' +
                        '</div>',
                        unsafe_allow_html=True
                    )
                    st.sidebar.markdown(
                        '<div style="margin-left:13px;margin-top:30px;margin-bottom:10px;color: white;font-size:23px;">Your Trips:</div>',
                        unsafe_allow_html=True)

                    for trip in trips:
                        trip_name=trip['name']
                        st.sidebar.markdown(f'<div class="place-block" style="text-align: center;">{trip_name}</div>',
                                            unsafe_allow_html=True)
                else:
                    st.sidebar.markdown(
                        '<div style="margin-bottom: 10px; font-weight: bold; font-size: 43px; text-align: left; display: flex; align-items: center;">' +
                        '<img src="https://raw.githubusercontent.com/Mallika2002/OCTANET_JUNE/main/logo_1-removebg.png" ' +
                        'style="width: 60px; height: 60px; margin-right: 10px;">' +
                        '<span style="color: pink;">T</span>' +
                        '<span style="color: white;">rip</span>' +
                        '<span style="color: pink;">T</span>' +
                        '<span style="color: white;">hrive</span>' +
                        '</div>',
                        unsafe_allow_html=True
                    )
                    st.sidebar.header("Your trips:")
            else:
                # st.sidebar.markdown('<div style="margin-left:5px;margin-bottom:10px;color: pink;font-weight: bold;font-size:43px;">TripThrive</div>', unsafe_allow_html=True)
                st.sidebar.header("Your trips:")

    custom_css = """
        <style>


        .place-list {
            display: flex;
            flex-wrap: wrap;

        }
        [data-testid="stSidebar"]{
        padding-left:30px;
        width:300px !important;
        background-image:url('https://images.unsplash.com/photo-1583161443085-2e2947a6664c?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MzB8fHRyYXZlbGxpbmd8ZW58MHx8MHx8fDA%3D');
        background-size:cover;
        width:350px !important;

        }
        .st-emotion-cache-16txtl3 {
        padding: 4rem 1rem;
        }

        .place-block {
        margin-bottom:10px;
        background-color: #eaf9e2; /* Subtle green color */
        padding: 5px;
        font-size:20px;
        margin: 5px;
        display:inline-block;
        border-radius: 8px;
        width:130px; /* Set a fixed width for each block */
        color:black;
        }
        </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

def is_place_in_india(place):
    geolocator = Nominatim(user_agent="place_in_india_checker")
    location = geolocator.geocode(place)
    return location and 'India' in location.address

def add_place_to_csv(place, csv_file_path):
    with open(csv_file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([place])

def trip_planner_section():
    st.markdown('<span style="margin-top:30px;font-size:55px;color: indianred; font-weight: bold;"> Personal Trip Planner </span>', unsafe_allow_html=True)


    user_data_path = os.path.join(os.path.dirname(__file__), '..', 'user_data.txt')
    user_path = os.path.join(os.path.dirname(__file__),'user.txt')
    no_user_data_path = os.path.join(os.path.dirname(__file__), '..', 'no_user_data.txt')

    # user_input = st.text_input(r"$\textsf{\normalsize Enter the Place You Want to Visit}$", key="input2")

    with open(user_data_path, 'r') as user_data_file:
        username = user_data_file.read().strip()

    # if len(username) == 0:
    st.header("Share your Location")
    nouser_location = streamlit_geolocation()
    st.markdown(
        f"""
    <style>
        .element-container iframe {{
            width: 30px;  /* Set your desired width */
            height: 30px;  /* Set your desired height */
        }}
    </style>
    """,
        unsafe_allow_html=True
    )
    latitude = nouser_location['latitude']
    longitude = nouser_location['longitude']

    geolocator = Nominatim(user_agent="geo_converter")

    # Reverse geocode to get the address
    location = geolocator.reverse((latitude, longitude))

    # Print the address
    print(location)

    csv_file_path = "C:\\Users\\malli\\Downloads\\tripGenie-main (1)\\tripGenie-main\\locations.csv"

    user_input = st.text_input(r"$\textsf{\normalsize Enter the Place You Want to Visit}$", key="input2")
    if user_input and is_place_in_india(user_input.strip()):
        add_place_to_csv(user_input.strip(), csv_file_path)

    if latitude is not None:
        with open(user_path, 'w',encoding='utf-8') as user_file:
            user_file.write(f'{user_input}\n{location}')

    # else:
        
    #     user_data = db.users.find_one({"username": username})
    #     user_location = user_data["location"].get("address", "Unknown Address")
    #     print(user_location)
    #     with open(user_path, 'w',encoding='utf-8') as user_file:
    #         user_file.write(f'{user_input}\n{user_location}')

    # user_input = st.text_input(r"$\textsf{\normalsize Enter the Place You Want to Visit}$", key="input2")

    # days = st.slider(r"$\textsf{\normalsize Enter the Number of Days}$", 1, 9, 1)
    # if latitude is not None:
    #     with open(user_path, 'w') as user_file:
    #         user_file.write(f'{user_input}\n{location}')

    col1, _ = st.columns([1, 4])
    with col1:
        days = st.slider(
            label=r"$\textsf{\normalsize Choose Duration of your Trip}$",
            min_value=1, max_value=9
        )
    budget = st.text_input(r"$\textsf{\normalsize Enter the Budget per person}$", key="input4")

    if days > 0:

        with stylable_container(
                css_styles=[
                    """
                    .stSelectbox {
                    background-color: transparent;
                        width: 359px !important;
                        color: white;
                    }
                    """,


                ]
        ):
                option = st.selectbox(
                    r"$\textsf{\normalsize Choose your Preferences}$",
                    ("Couple", "Friends", "Family"),
                    index=None,
                    placeholder="Select",
                )
                selected_condition = []  # List to store selected conditions

                if option == "Couple":
                    selected_condition.append("Couple")
                elif option == "Friends":
                    choose = st.radio("Choose Category", ("Boys", "Girls"))
                    if choose == "Boys":
                        selected_condition.append("Boys group")
                    elif choose == "Girls":
                        selected_condition.append("Girls group")
                elif option == "Family":
                        selected_condition.append("Family")
                    
    else:
        selected_condition = 'Solo Traveller'

    if st.button(r"$\textsf{\normalsize Generate Itinerary}$", key="button2"):
        if user_input:
            if len(username) > 0:
                user_data = db.users.find_one({"username": username})
                if user_data:
                    # user_location = user_data["location"].get("address", "Unknown Address")
                    system_message = TRIP_PLANNER_SYSTEM.format(days=days, budget=budget, user_location=location,
                                                                user_input=user_input, conditions=selected_condition)
                    output = get_response(system_message, user_input)
                    balloons_done = st.balloons()
                    st.markdown(
                        '<span style="margin-top:30px;font-size:35px;color: yellow; font-weight: bold;">Welcome to TripThrive, Granting wishes with AI travel magic 🎉 </span>',
                        unsafe_allow_html=True)

                    if balloons_done:
                        # st.markdown('<span style="margin-top:10px;color: red; font-weight: bold;">Welcome to TripThrive, Granting wishes with AI travel magic</span>', unsafe_allow_html=True)
                        st.markdown(f'You can reach from {location} to {user_input} easily.')
                        st.markdown('Check this map ')
                        TripThrive2.main()
                        st.markdown(output.content)
                    else:
                        st.warning("Please wait for the balloons to finish before proceeding.")
                    # st.markdown(output.content)

                    trips = user_data.get("trips", [])
                    user_input_lower = user_input.lower()
                    # trips_lower = [trip.lower() for trip in trips]
                    trips_lower = [trip["name"].lower() for trip in trips]
                    if user_input_lower not in trips_lower:
                        user_input_capitalized = user_input_lower.capitalize()
                        trips.append({"name":user_input_capitalized,"review":"","rating":0,"picture": None})
                        db.users.update_one({"username": username}, {"$set": {"trips": trips}})
                        update_sidebar_user(user_input_capitalized)  # Update the sidebar in case there are changes
            else:
                system_message = TRIP_PLANNER_SYSTEM.format(days=days, budget=budget, user_location=location,
                                                            user_input=user_input, conditions=selected_condition)
                output = get_response(system_message, user_input)

                # Assuming balloons are done is stored in a variable called `balloons_done`
                balloons_done = st.balloons()
                st.markdown('<span style="margin-top:30px;font-size:35px;color: yellow; font-weight: bold;">Welcome to <span style="font-color:blue;">TripThrive</span>, Granting wishes with AI travel magic 🎉 </span>', unsafe_allow_html=True)

                if balloons_done:
                    # st.markdown('<span style="margin-top:10px;color: red; font-weight: bold;">Welcome to TripThrive, Granting wishes with AI travel magic</span>', unsafe_allow_html=True)
                    st.markdown(f'You can reach from {location} to {user_input} easily.')
                    st.markdown('Check this map ')
                    TripThrive2.main()
                    st.markdown(output.content)
                else:
                    st.warning("Please wait for the balloons to finish before proceeding.")

                
        else:
            st.write("Please provide your destination")

def get_response(system_message, user_input, *args):
    messages = [
        Message(role="system", content=system_message),
        Message(role="user", content=user_input)
    ]
    options = Options(messages=messages)
    output = service.chat(options)
    return output


def show(output):
    if output:
        st.markdown(output.content)
    elif output == "NULL":
        st.markdown("Please Enter Some Text")


def main():
    user_data_path = os.path.join(os.path.dirname(__file__), '..', 'user_data.txt')

    if os.stat(user_data_path).st_size == 0:
        output = trip_planner_section()
        show(output)

    else:

        with open(user_data_path, 'r') as user_data_file:
            username = user_data_file.read().strip()

        if username:
            update_sidebar_user("")
            output = trip_planner_section()
            show(output)


if __name__ == "__main__":
    main()
