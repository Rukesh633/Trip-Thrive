import json
from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, url_for, session
import subprocess
import os
from flask_pymongo import PyMongo
from bson import ObjectId
import secrets
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim 
from sklearn.cluster import KMeans
import requests
import warnings


app = Flask(__name__)
warnings.filterwarnings('ignore')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/tripdb'
app.config['UPLOAD_FOLDER'] = 'uploads'
mongo = PyMongo(app)

def fetch_image_urls(city_name):
    access_key = 'BiGDjnVy3m9JLpdOjHxbEFDnT1Ev1HVmY0NTuc3f6Zg'  # Replace with your Unsplash access key
    url = f'https://api.unsplash.com/search/photos?query={city_name}&client_id={access_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            return [photo['urls']['regular'] for photo in data['results'][:3]]  # Fetch URLs of first 3 images
    return []

# Function to get image URL for a city
def get_city_image_url(city):
    image_urls = fetch_image_urls(city)
    if image_urls:
        return image_urls[0]  # Return the first image URL
    return ''

@app.route('/getrecomm')
def recomm_index():
    return render_template('recomm_index.html')

@app.route('/find_cities', methods=['POST'])
def find_cities():
    # Retrieve user's trips from MongoDB
    username=load_username_from_file()
    user_data = mongo.db.users.find_one({'username': username})
    present_location = "Visakhapatnam,Andhra Pradesh"
    user_trips = mongo.db.users.find_one({'username': username})
    trips = user_trips.get('trips', [])
    print(trips)
    print(present_location)

    suggested_cities = []

    if not trips:
        if present_location:
            country = 'India'
            geolocator = Nominatim(user_agent="Trips")

            # Geocode present location to obtain latitude and longitude
            location = geolocator.geocode(present_location + ', ' + country, timeout=10)
            if location and location.address.split(", ")[-1] == country:
                present_latitude = location.latitude
                present_longitude = location.longitude

                # Fetch nearby cities based on present location
                nearby_cities = geolocator.reverse((present_latitude, present_longitude), exactly_one=False)

                for result in nearby_cities:
                    city = result.raw.get('display_name', '').split(', ')[0]
                    if city and city not in suggested_cities:
                        suggested_cities.append(city)
                
                suggested_cities.append('Rama Krishna Beach')
                suggested_cities.append('Borra Caves')
                suggested_cities.append('Kailasagiri Hill Park')
                suggested_cities.append('Submarine Museum (INS Kursura)')
                suggested_cities.append('Kambalakonda Wildlife Sanctuary:')


    else:
        for trip in trips:
            input_city = trip['name']
            print(input_city)
            df = pd.read_csv('locations.csv', sep=',')

            # Geocode city locations to obtain latitude and longitude
            country = 'India'
            geolocator = Nominatim(user_agent="Trips")

            # Initialize lists to store latitude and longitude
            latitude = []
            longitude = []

            for city in df['location']:
                location = geolocator.geocode(city + ',' + country, timeout=10)
                if location and location.address.split(", ")[-1] == country:
                    latitude.append(location.latitude)
                    longitude.append(location.longitude)
                else:
                    latitude.append(np.nan)
                    longitude.append(np.nan)

            # Add latitude and longitude to the DataFrame
            df['latitude'] = latitude
            df['longitude'] = longitude

            # Drop rows with missing latitude or longitude
            df.dropna(subset=['latitude', 'longitude'], inplace=True)

            # Check if DataFrame is empty after filtering
            if df.empty:
                continue

            # Perform KMeans clustering on latitude and longitude
            coordinates = np.column_stack((df['latitude'], df['longitude']))
            num_clusters = 5  # Example number of clusters
            kmeans = KMeans(n_clusters=num_clusters, random_state=0)
            cluster_labels = kmeans.fit_predict(coordinates)

            # Assign cluster labels to DataFrame
            df['cluster'] = cluster_labels

            # Find cluster label of input city
            input_cluster_df = df.loc[df['location'] == input_city, 'cluster']
            if input_cluster_df.empty:
                continue

            input_cluster = input_cluster_df.values[0]

            # Find cities in the same cluster as the input city
            cities_in_cluster = df.loc[df['cluster'] == input_cluster, 'location']

            cities_list = [city for city in cities_in_cluster if city != input_city]

            # Fetch image URLs for suggested cities
            city_images = {city: fetch_image_urls(city) for city in cities_list}

            # Add suggested cities to the final list
            suggested_cities.extend(cities_list)

        # Filter suggested cities to those only in India
            suggested_cities = [city for city in suggested_cities if geolocator.geocode(city + ',' + country, timeout=10) and geolocator.geocode(city + ',' + country, timeout=10).address.split(", ")[-1] == country]

        # Limit suggested cities to 6
    suggested_cities = suggested_cities[:6]

    # Fetch image URLs for the limited suggested cities
    city_images = {city: fetch_image_urls(city) for city in suggested_cities}
    print(suggested_cities)
    return render_template('result.html', cities_list=suggested_cities, city_images=city_images, get_city_image_url=get_city_image_url)


# Route to store user's geolocation in MongoDB
@app.route('/store_location', methods=['POST'])
def store_location():
    data = request.json
    username = data.get('username')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Update or insert location data in MongoDB
    mongo.db.users.update_one(
        {'username': username},
        {'$set': {'location': {'latitude': latitude, 'longitude': longitude}}},
        upsert=True
    )

    return jsonify({'status': 'success'})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/trips')
def get_trips():
    # Retrieve the user document with username 'admin'
    username = load_username_from_file()
    user = mongo.db.users.find_one({"username": username})
    if user:
        trips = user.get('trips', [])
        # Extract only the trip names

        return jsonify(trips)
    else:
        return jsonify({'message': 'User not found'})

@app.route('/update_review/<string:trip_name>')
def update_review(trip_name):
    # Retrieve the user's review and rating for the specified trip from the database
    username = load_username_from_file()
    user = mongo.db.users.find_one({"username": username})
    trips = user.get('trips', [])
    trip_review = ''
    trip_rating = ''
    for trip in trips:
        if trip['name'] == trip_name:
            trip_review = trip.get('review', '')
            trip_rating = trip.get('rating', '')
            break

    # Render the update_review page with the trip_name, review, and rating
    return render_template('update_review.html', trip_name=trip_name, trip_review=trip_review, trip_rating=trip_rating)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if request.method == 'POST':
        place_name = request.form.get('placeName')
        review = request.form.get('review')
        rating = int(request.form.get('rating'))
        picture = request.files['picture']
        if picture and allowed_file(picture.filename):
            # picture = request.files['picture']
            # Save the file to a specific directory
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture.filename)
            picture.save(picture_path)
        else:
            username = load_username_from_file()
            user = mongo.db.users.find_one({"username": username})
            if user:
                trips = user.get('trips', [])
                for trip in trips:
                    if trip['name'] == place_name:
                        picture_path = trip['picture']
                        break
            else:
                return jsonify({'message': 'User not found'})

        username = load_username_from_file()
        user = mongo.db.users.find_one({"username": username})

        if user:
            trips = user.get('trips', [])
            existing_trip_index = None
            # Check if the trip already exists in the user's trips
            for i, trip in enumerate(trips):
                if trip['name'] == place_name:
                    existing_trip_index = i
                    break
            if existing_trip_index is not None:
                # Update the existing trip's review and rating fields
                trips[existing_trip_index]['review'] = review
                trips[existing_trip_index]['rating'] = rating
                trips[existing_trip_index]['picture'] = picture_path
            else:
                # Add a new trip entry with review and rating
                new_trip = {'name': place_name, 'review': review, 'rating': rating, 'picture': picture_path}
                trips.append(new_trip)
            # Update the user document in the database
            mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'trips': trips}})
            return render_template('trips_index.html')
        else:
            return jsonify({'message': 'User not found'})

    else:
        return jsonify({'message': 'Invalid request method'})


def allowed_file(filename):
    # Check if the file extension is allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# Route to retrieve user's geolocation from MongoDB
@app.route('/get_location/<user_id>', methods=['GET'])
def get_location(user_id):
    location_data = mongo.db.user_locations.find_one({'user_id': user_id}, {'_id': 0})
    return jsonify(location_data)

# Flag to check if Streamlit app is already running
streamlit_running = False


@app.route('/logout')
def logout():
    
    session.pop('username', None)
    
    return redirect(url_for('index'))

# Load the username from the user_data.txt file
def load_username_from_file():

    with open('user_data.txt', 'r') as file:
        username = file.read().strip()
    return username
    
@app.route('/user/<username>/account_details')
def account_details_with_username(username):
    user_data = mongo.db.users.find_one({'username': username})
    # print(user_data)
    fields = {
        'username': user_data.get('username', ''),
        'name': user_data.get('name', ''),
        'email': user_data.get('email', ''),
        'bio': user_data.get('bio', ''),
        'birthday': user_data.get('birthday', ''),
        'gender': user_data.get('gender', ''),
        'phone': user_data.get('phone', '')
    }    
    return render_template('cc_index.html',fields=fields)

@app.route('/account_details')
def account_details():
        username_from_file = load_username_from_file()
        return redirect(url_for('account_details_with_username', username=username_from_file))
        


@app.route('/trip_details',methods=['POST','GET'])
def trip_details():
    return render_template('trips_index.html')

# Define a route to handle form submission
@app.route('/update-profile', methods=['POST'])
def update_profile():
    user_data = {
        "username":request.form.get("username"),
        "name": request.form.get('name'),
        "email": request.form.get('email'),
        "currentPassword": request.form.get('currentPassword'),
        "newPassword": request.form.get('newPassword'),
        "repeatPassword": request.form.get('repeatPassword'),
        "bio": request.form.get('bio'),
        "birthday": request.form.get('birthday'),
        "gender": request.form.get('gender'),
        "phone": request.form.get('phone')
    }
    username_from_file = load_username_from_file()
    print(user_data)

    # Fetch user from MongoDB using the username from the session
    user = mongo.db.users.find_one({"username": username_from_file})

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Update user fields
    update_fields = {}
    if user_data["username"] is not None and user_data["username"]!="":
        update_fields["username"] =  user_data["username"]
    if user_data["name"] is not None and user_data["name"] != "":
        update_fields["name"] = user_data["name"]
    if user_data["email"] is not None and user_data["email"] != "":
        update_fields["email"] = user_data["email"]
    if user_data["bio"] is not None and user_data["bio"] != "":
        update_fields["bio"] = user_data["bio"]
    if user_data["birthday"] is not None and user_data["birthday"] != "":
        update_fields["birthday"] = user_data["birthday"]
    if user_data["gender"] is not None and user_data["gender"] != "":
        update_fields["gender"] = user_data["gender"]
    if user_data["phone"] is not None and user_data["phone"] != "":
        update_fields["phone"] = user_data["phone"]

    # Check current password if provided
    if user_data["currentPassword"] and user_data["currentPassword"] != user["password"]:
        flash('Incorrect Current password','danger')
        return redirect(url_for('account_details_with_username',username=username_from_file))


    print("Content of update_fields:", user_data)
    print(user_data["newPassword"])
    print(user_data["repeatPassword"])
    # Update password only if a new password is provided
    if user_data["newPassword"] and user_data["newPassword"] == user_data["repeatPassword"]:
        mongo.db.users.update_one(
        {"username": username_from_file},
        {"$set": {"password": user_data["newPassword"]}}
    )

    # Save the updated user document
    mongo.db.users.update_one(
    {"username": username_from_file},
    {
        "$set": update_fields,
        "$setOnInsert": {"username": username_from_file}
    },
    upsert=True
    )
    # print('ye')
    flash('Profile saved succesfully','success')
    return redirect(url_for('account_details_with_username',username=username_from_file))
    # return render_template('cc_index.html', fields=update_fields, alert="Profile updated successfully", success=True)


@app.route('/store_address', methods=['POST'])
def store_address():
    data = request.json
    username = data.get('username')
    address = data.get('address')
        
    mongo.db.users.update_one(
        {'username': username},
        {'$set': {'location.address': address}},
        upsert=True
    )

    return jsonify({'status': 'success'})

@app.route('/plan')
def plan():
    user_data_path = os.path.join(os.path.dirname(__file__), 'place.txt')
    query_param = request.args.get('query')
    if query_param:
        with open(user_data_path, 'w') as user_data_file:  # Path adjusted to save in the outer directory
            user_data_file.write(query_param)
        code_path = os.path.abspath("streamlit/code.py")
        subprocess.Popen(["streamlit", "run", code_path])
    
    else:
            # Handle the case where the username is not in the session
        return redirect(url_for('index'))

@app.route('/user/<username>')
def user_page(username):
    return render_template('index.html', username=username)

@app.route('/')
def index():
    if 'username' in session:
        with open('user_data.txt', 'r') as f:
            user_dat_txt = f.read().strip()
        print('HI')
        # return redirect(url_for('user_page', username=session['username']))
        return render_template('index.html', user_dat_txt=user_dat_txt)
        # return render_template('index.html', username=session['username'])
    else:
        print('hO')
        shared_data_path = os.path.join(os.path.dirname(__file__), 'user_data.txt')
        with open(shared_data_path, 'w',encoding='utf-8') as file:
            pass

        return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        birthday = request.json.get('dob')

        # Check if username already exists in the database
        existing_user = mongo.db.users.find_one({'username': username})
        if existing_user:
            return jsonify({'error': 'Username already exists'})
            # return jsonify({'error': 'Username already exists'})
            # return render_template('signup.html')

        # Validate the form data if needed
        else:
        # Store user data in MongoDB
            mongo.db.users.insert_one({'username': username, 'password': password, 'birthday': birthday})
    
            session['username'] = username  # Store username in session

            shared_data_path = os.path.join(os.path.dirname(__file__), 'user_data.txt')
            with open(shared_data_path, 'w', encoding='utf-8') as file:
                    file.write(f"{session.get('username')}")

            return jsonify({'status': 'success'})
    else:
        return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')

        user_data = mongo.db.users.find_one({'username': username, 'password': password})

        if user_data:
            session['username'] = username  # Store username in session

            shared_data_path = os.path.join(os.path.dirname(__file__), 'user_data.txt')
            with open(shared_data_path, 'w',encoding='utf-8') as file:
                file.write(f"{session.get('username')}")
                
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'})
    else:
        return render_template('login.html')
    



@app.route('/save_changes', methods=['POST'])
def save_changes():
    if 'username' in session:
        username = session['username']

        # Retrieve form data from the request
        username_input = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')

        print(username)
        print(name)
        print(email)
        
        # Add more fields as needed based on your form

        # Update the user data in MongoDB
        mongo.db.users.update_one(
            {'username': username},
            {'$set': {'username': username_input, 'name': name, 'email': email}},
        )

        # Redirect back to the account details page

        
        return redirect(url_for('account_details'))
    else:
        # Handle the case where the username is not in the session
        return redirect(url_for('index'))
    

@app.route('/book')
def book():
        
        if 'username' in session:
        # Store the current URL in the session
            session['previous_url'] = url_for('user_page', username=session['username'])

            code_path = os.path.abspath("streamlit/TripThrive.py")
            subprocess.Popen(["streamlit", "run", code_path])

            # Redirect back to the user's page
            return redirect(session.pop('previous_url', url_for('index')))
        else:

            code_path = os.path.abspath("streamlit/TripThrive.py")
            subprocess.Popen(["streamlit", "run", code_path])
            # Handle the case where the username is not in the session
            return redirect(url_for('index'))
        

@app.route('/streamlit')
def streamlit():
    global streamlit_running

    if not streamlit_running and request.args.get('action') == 'plan_a_tour':
        code_path = os.path.abspath("streamlit/code.py")
        subprocess.Popen(["streamlit", "run", code_path])
        streamlit_running = True

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
