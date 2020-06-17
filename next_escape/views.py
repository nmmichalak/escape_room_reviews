#!/usr/bin/python
import flask
import pandas as pd
import numpy as np
import sklearn
from sklearn.impute import SimpleImputer
import geopy
from geopy import distance

# import app
from next_escape import app

# data
## read room data
room_data = pd.read_csv("data/room_data.csv")

# convert "None" to None
room_data = room_data.mask(room_data.eq("None"))

## read city and state data
state_city_data = pd.read_csv("data/state_city_room_url_df.csv")

## merge
escape_rooms = room_data.merge(state_city_data, left_on = "woe_room_url", right_on = "woe_room_url", how = "left")

## add city, state - compnay: room variable
escape_rooms["city_state_company_room"] = [city + ", " + state + " - " + room for city, state, room in zip(escape_rooms["city"], escape_rooms["state"], escape_rooms["company_and_room"])]

# define functions
# Geocoder using the Google Maps v3 API
api_key = open("google_maps_api_key.txt").readlines()[0]
googlev3_locator = geopy.geocoders.GoogleV3(api_key = api_key)

# address, latitude, and longitude
def get_lat_long(address):
    # look up location
    location = googlev3_locator.geocode(address)
    return location.address, location.latitude, location.longitude

## returns matrix of euclidian distances
def pairwise_dist(data_frame, features):
    # full dataset of features 
    X_full = data_frame.loc[:, features]
    
    # imputer parameters (use most frequent value)
    imputer = SimpleImputer(missing_values = np.nan, strategy = "most_frequent")

    # fit imputation model
    imputer_fit = imputer.fit(X_full)

    # predict missing values
    X_predict = imputer_fit.transform(X_full)
    
    # distance matrix
    distance_matrix = pd.DataFrame(
    # euclidian distances
    sklearn.metrics.pairwise.euclidean_distances(
        # standardize ((x - mean / sd))
        sklearn.preprocessing.StandardScaler().fit_transform(X_predict)
    ))
    
    return distance_matrix

## returns table of recommended rooms and their information
def recommend_rooms(user_location, travel_limit, room_played, features = ["min_players", "max_players", "time_limit", "difficulty_int", "success_rate", "fear_int", "minimum_age"], display_var = ["company_and_room", "query_address", "woe_room_url", "miles2room", "dissimilarity", "player_range", "time_limit_str", "difficulty_level", "fear_level", "age_requirement"]):
    # user location data
    user_address_query, user_latitude, user_longitude = get_lat_long(user_location)
    
    # compute miles away from each room in database
    miles2room = [round(geopy.distance.geodesic((user_latitude, user_longitude), (room_latitude, room_longitude)).miles, 2) for room_latitude, room_longitude in zip(escape_rooms["room_latitude"], escape_rooms["room_longitude"])]
    
    # add to data frame
    escape_rooms["miles2room"] = miles2room

    # get index for user input game
    room_played_index = int(escape_rooms["city_state_company_room"][escape_rooms["city_state_company_room"] == room_played].index.to_numpy())
    
    # z-score features and compute pairwise euclidian distance matrix
    escape_room_distances = pairwise_dist(escape_rooms, features).round(2)
    
    # rank rooms based on similarity to room user input
    rooms_ranked = (escape_room_distances.loc[room_played_index]
    .sort_values()
    .to_frame()
    .reset_index(level = 0)
    .rename(columns = {"index": "row_number", room_played_index: "dissimilarity"}))
 
    # left join with subset of escape rooms
    escape_rooms_subset = rooms_ranked.merge(escape_rooms, how = "left", left_on = "row_number", right_index = True)
    
    # subset escape rooms to rooms within travel limit
    escape_rooms_subset = escape_rooms_subset.loc[(escape_rooms_subset["miles2room"] <= travel_limit) | (escape_rooms_subset["city_state_company_room"] == room_played), :]
 
    # 3 most similar
    recommended_rooms = escape_rooms_subset["city_state_company_room"].values[:3].tolist()

    # recommendation table
    return escape_rooms_subset.loc[escape_rooms_subset["city_state_company_room"].isin(recommended_rooms), display_var].sort_values(by = "dissimilarity")

# input played room search method
@app.route("/input_played_room", methods = ["POST", "GET"])
def input_played_room():
    if flask.request.method == "POST":
        return recommendation_table()
    else:
        return flask.render_template("input_played_room.html")

@app.route("/input_ideal_room", methods = ["POST", "GET"])
def input_ideal_room():
    if flask.request.method == "POST":
        return recommendation_table()
    else:
        return flask.render_template("input_ideal_room.html")

@app.route("/recommendations", methods = ["POST", "GET"])
def recommendation_table():
    if flask.request.method == "POST":
        # location
        user_location = flask.request.form["location"]
            
        # miles willing to travel from location
        travel_limit = int(flask.request.form["miles_limit"])

        # escape room played before
        room_played = flask.request.form["escape_room"]

        # data frame of recommendations
        recommendations = recommend_rooms(user_location = user_location, 
        travel_limit = travel_limit, 
        room_played = room_played,
        features = ["min_players", "max_players", "time_limit", "difficulty_int", "success_rate", "fear_int", "minimum_age"], 
        display_var = ["company_and_room", "query_address", "woe_room_url", "miles2room", "dissimilarity", "player_range", "time_limit_str", "difficulty_level", "fear_level", "age_requirement"])

        # rename columns
        recommendations.columns = ["Company: Escape Room", "Room Address", "Website", "Miles Away", "Dissimilarity Score", "Number of Players", "Time Limit", "Difficulty", "Scary", "Age Requirement"]
        
        return flask.render_template("recommendations.html", recommendation_table = recommendations.to_html(classes = ["table-hover", "table-striped"], index = False, render_links = True, justify = "center"))
    else:
        return flask.render_template("input_played_room.html")

if __name__ == "__main__":
	app.run(host = "0.0.0.0", debug = False)