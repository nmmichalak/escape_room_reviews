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
## escape rooms
escape_rooms = pd.read_csv("data/escape_rooms.csv")

## dissimilarity matrix
dissimilarity_matrix = pd.read_csv("data/dissimilarity_matrix.csv", index_col = ["city_state_company_room"])

# convert "None" to None in escape rooms data
escape_rooms = escape_rooms.mask(escape_rooms.eq("None"))

# define functions
# Geocoder using the Google Maps v3 API
api_key = open("google_maps_api_key.txt").readlines()[0]
googlev3_locator = geopy.geocoders.GoogleV3(api_key = api_key)

# address, latitude, and longitude
def get_lat_long(address):
    # look up location
    location = googlev3_locator.geocode(address)
    return location.address, location.latitude, location.longitude

## returns table of recommended rooms and their information
def recommend_rooms(user_location, travel_limit, room_played):
    # user location data
    user_address_query, user_latitude, user_longitude = get_lat_long(user_location)
    
    # compute miles away from each room in database
    miles2room = [distance.geodesic((user_latitude, user_longitude), (lat, long)).miles if np.isnan(lat) == False else None for lat, long in zip(escape_rooms["room_latitude"], escape_rooms["room_longitude"])]
    
    # add to data frame
    escape_rooms["miles2room"] = miles2room
    
    # rank rooms based on similarity to room user input
    rooms_ranked = (dissimilarity_matrix
                    .loc[room_played]
                    .sort_values()
                    .to_frame()
                    .reset_index()
                    .rename(columns = {"index": "city_state_company_room", room_played: "dissimilarity"}))

    # left join with subset of escape rooms
    escape_rooms_subset = rooms_ranked.merge(escape_rooms, how = "left", on = "city_state_company_room")
    
    # subset escape rooms to rooms within travel limit
    escape_rooms_subset = escape_rooms_subset.loc[(escape_rooms_subset["miles2room"] <= travel_limit) | (escape_rooms_subset["city_state_company_room"] == room_played), :]
 
    # 3 most similar
    recommended_rooms = escape_rooms_subset["city_state_company_room"].values[:4].tolist()
    
    # recommendation table
    recommendation_table = escape_rooms_subset.loc[escape_rooms_subset["city_state_company_room"].isin(recommended_rooms), ["company_and_room", "woe_room_url", "query_address", "miles2room", "player_range", "time_limit_str", "difficulty_level", "success_rate", "fear_level", "minimum_age", "dissimilarity"]].sort_values(by = "dissimilarity")

    return recommendation_table

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
        recommendations = recommend_rooms(user_location = user_location, travel_limit = travel_limit, room_played = room_played)

        # fill nan
        recommendations = recommendations.fillna("No info")

        # rename columns
        recommendations.columns = ["Company: Escape Room", "Website", "Room Address", "Miles Away", "Number of Players", "Time Limit", "Difficulty", "Success Rate", "Scariness", "Age Requirement", "Dissimilarity Score"]
        
        return flask.render_template("recommendations.html", recommendation_table = recommendations.to_html(col_space = "4.5cm", classes = ["table-hover", "table-striped"], index = False, float_format = lambda x: "%10.2f" % x, justify = "center", render_links = True))
    else:
        return flask.render_template("input_played_room.html")

if __name__ == "__main__":
	app.run(host = "0.0.0.0", debug = False)