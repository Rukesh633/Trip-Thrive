import os
import streamlit as st 
from utils2 import format_trip_planner_message1
from geopy.geocoders import Nominatim
from usellm import UseLLM, Message, Options
from streamlit_geolocation import streamlit_geolocation
from TripThrive import get_response, show
from utils2 import TRIP_PLANNER_SYSTEM1 


def main():
    st.markdown(
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
    user_data_path = os.path.join(os.path.dirname(__file__), '..', 'place.txt')

    with open(user_data_path, 'r') as user_data_file:
        user_input = user_data_file.read().strip()

    system_message = TRIP_PLANNER_SYSTEM1.format(user_input=user_input)
    output = get_response(system_message,user_input=user_input)
    st.markdown(output.content)
    

if __name__ == "__main__":
    main()
