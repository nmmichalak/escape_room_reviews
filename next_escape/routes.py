#!/usr/bin/python
import flask
import pandas as pd
import numpy as np
import sklearn
from sklearn import linear_model
from sklearn.impute import SimpleImputer
import geopy
from geopy import distance

# pandas column width
pd.set_option("display.max_colwidth", -1)

# import app
from next_escape import app

# data
## escape rooms
escape_rooms = pd.read_csv("next_escape/data/escape_rooms.csv")

## imputed feature matrix
X_features = pd.read_csv("next_escape/data/X_features.csv", index_col = [0])

### time limit units in 15 minute interval
X_features.iloc[:, 0] = X_features.iloc[:, 0] / 15

### success rate units in 0.20 interval
X_features.iloc[:, 2] = X_features.iloc[:, 2] / 0.20

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

# recode difficulty_level
def recode_difficulty(x):
    if x == "Very easy":
        return 0
    elif x == "Easy":
        return 1
    elif x == "Average":
        return 2
    elif x == "Difficult":
        return 3
    elif x == "Very difficult":
        return 4
    else:
        return "None"

# recode fear_level
def recode_fear(x):
    if x == "Not scary":
        return 0
    elif x == "A little scary":
        return 1
    elif x == "Scary":
        return 2
    elif x == "Very scary":
        return 3
    else:
        return "None"

## returns table of recommended rooms and their information
def favorite_room(user_location, miles_limit, group_size, youngest_person, user_room):
    # user location data
    user_address_query, user_latitude, user_longitude = get_lat_long(user_location)
    
    # compute miles away from each room in database
    miles2room = [distance.geodesic((user_latitude, user_longitude), (lat, long)).miles if np.isnan(lat) == False else None for lat, long in zip(escape_rooms["room_latitude"], escape_rooms["room_longitude"])]
    
    # add to data frame
    escape_rooms["miles2room"] = miles2room

    # compute euclidean distance matrix
    dissimilarity_matrix = pd.DataFrame(
        sklearn.metrics.euclidean_distances(
            X_features
    ), index = escape_rooms["city_state_company_room"].tolist(), columns = escape_rooms["city_state_company_room"].tolist())
    
    # rank rooms based on similarity to room user input
    rooms_ranked = (dissimilarity_matrix
                    .loc[user_room]
                    .sort_values()
                    .to_frame()
                    .reset_index()
                    .rename(columns = {"index": "city_state_company_room", user_room: "dissimilarity"}))

    # left join with subset of escape rooms
    escape_rooms_subset = rooms_ranked.merge(escape_rooms, how = "left", on = "city_state_company_room")
    
    # subset escape rooms to rooms within travel limit and don't exclude group size or the youngest group member(s)
    escape_rooms_subset = escape_rooms_subset.loc[((escape_rooms_subset["miles2room"] <= miles_limit) & (escape_rooms_subset["max_players"] >= group_size) & (escape_rooms_subset["minimum_age"] <= youngest_person)) | (escape_rooms_subset["city_state_company_room"] == user_room), :]
 
    # 3 most similar
    recommended_rooms = escape_rooms_subset["city_state_company_room"].values[:4].tolist()
    
    # recommendation table
    recommendation_table = escape_rooms_subset.loc[escape_rooms_subset["city_state_company_room"].isin(recommended_rooms), ["company_and_room", "woe_room_url", "query_address", "miles2room", "player_range", "time_limit_str", "difficulty_level", "success_rate", "fear_level", "minimum_age", "dissimilarity"]].sort_values(by = "dissimilarity")

    return recommendation_table

# returns table of recommended rooms and their information
def ideal_room(user_location, miles_limit, group_size, youngest_person, time_limit_str, fear_level, difficulty_level):
    # user location data
    user_address_query, user_latitude, user_longitude = get_lat_long(user_location)
    
    # compute miles away from each room in database
    miles2room = [distance.geodesic((user_latitude, user_longitude), (lat, long)).miles if np.isnan(lat) == False else None for lat, long in zip(escape_rooms["room_latitude"], escape_rooms["room_longitude"])]

    # add to data frame
    escape_rooms["miles2room"] = miles2room
    
    # new row
    ideal_features = pd.DataFrame({"company_and_room": "Your Ideal Escape Room", "woe_room_url": np.nan, "query_address": user_address_query, "miles2room": 0, "player_range": str(group_size) + " or more", "time_limit_str": time_limit_str, "difficulty_level": difficulty_level, "success_rate": np.nan, "fear_level": fear_level, "minimum_age": str(youngest_person) + " or younger"}, index = [0])
    
    # predict success rate
    predict_succes_rate = linear_model.LinearRegression().fit(escape_rooms[["success_rate", "difficulty_int"]].dropna().to_numpy()[:, 1].reshape(-1, 1), 
                                                                      escape_rooms[["success_rate", "difficulty_int"]].dropna().to_numpy()[:, 0].reshape(-1, 1))
    
    # modify variables
    ideal_features = ideal_features.assign(time_limit = time_limit_str.split(" minutes")[0],
                                           time_limit_scaled = float(time_limit_str.split(" minutes")[0]) / 15,
                                           difficulty_int = recode_difficulty(difficulty_level),
                                           success_rate = predict_succes_rate.predict([[recode_difficulty(difficulty_level)]]),
                                           success_rate_scaled = predict_succes_rate.predict([[recode_difficulty(difficulty_level)]]) / 0.20,
                                           fear_int = recode_fear(fear_level))
    
    # append features
    X = np.r_[X_features, ideal_features.loc[:, ["time_limit_scaled", "fear_int", "difficulty_int", "success_rate_scaled"]]]
    
    # compute euclidean distance matrix
    dissimilarity_matrix = pd.DataFrame(
    sklearn.metrics.euclidean_distances(
        X
    ), index = escape_rooms["city_state_company_room"].append(pd.Series(["Your Ideal Escape Room"]), ignore_index = True), 
    columns = escape_rooms["city_state_company_room"].append(pd.Series(["Your Ideal Escape Room"]), ignore_index = True))
    
    # rank rooms based on similarity to room user input
    rooms_ranked = (dissimilarity_matrix
                    .loc["Your Ideal Escape Room"]
                    .sort_values()
                    .to_frame()
                    .reset_index()
                    .rename(columns = {"index": "city_state_company_room", "Your Ideal Escape Room": "dissimilarity"}))

    # left join with subset of escape rooms
    escape_rooms_subset = rooms_ranked.merge(escape_rooms, how = "left", on = "city_state_company_room")
    
    # subset escape rooms to rooms within travel limit
    escape_rooms_subset = escape_rooms_subset.loc[((escape_rooms_subset["miles2room"] <= miles_limit) & (escape_rooms_subset["max_players"] >= group_size) & (escape_rooms_subset["minimum_age"] <= youngest_person)) | (escape_rooms_subset["city_state_company_room"] == "Your Ideal Escape Room"), :]
 
    # 3 most similar
    recommended_rooms = escape_rooms_subset.loc[:, "city_state_company_room"].values[:4].tolist()
    
    # recommendation table
    recommendation_table = escape_rooms_subset.loc[escape_rooms_subset["city_state_company_room"].isin(recommended_rooms), ["company_and_room", "woe_room_url", "query_address", "miles2room", "player_range", "time_limit_str", "difficulty_level", "success_rate", "fear_level", "minimum_age", "dissimilarity"]].sort_values(by = "dissimilarity")
    
    # replace nan
    recommendation_table.loc[0, ["company_and_room", "woe_room_url", "query_address", "miles2room", "player_range", "time_limit_str", "difficulty_level", "success_rate", "fear_level", "minimum_age"]] = ideal_features.loc[0, ["company_and_room", "woe_room_url", "query_address", "miles2room", "player_range", "time_limit_str", "difficulty_level", "success_rate", "fear_level", "minimum_age"]].tolist()
    
    return recommendation_table

# index
@app.route("/")
def index():
    return flask.render_template("index.html")

# input played room search method
@app.route("/input_favorite_room", methods = ["POST", "GET"])
def input_favorite_room():
    if flask.request.method == "POST":
        return favorite_recommendation()
    else:
        return flask.render_template("input_favorite_room.html")

@app.route("/input_ideal_room", methods = ["POST", "GET"])
def input_ideal_room():
    if flask.request.method == "POST":
        return ideal_recommendation()
    else:
        return flask.render_template("input_ideal_room.html")

@app.route("/favorite_recommendations", methods = ["POST", "GET"])
def favorite_recommendation():
    if flask.request.method == "POST":
        # location
        user_location = flask.request.form["location"]
            
        # miles willing to travel from location
        miles_limit = int(flask.request.form["miles_limit"])
            
        # group size
        group_size = int(flask.request.form["group_size"])
            
        # youngest person in group
        youngest_person = int(flask.request.form["youngest_person"])

        # favorite escape room
        user_room = flask.request.form["escape_room"]

        # data frame of recommendations
        recommendations = favorite_room(user_location = user_location, miles_limit = miles_limit, group_size = group_size, youngest_person = youngest_person, user_room = user_room)

        # fill nan
        recommendations = recommendations.fillna("No info")

        # rename columns
        recommendations.columns = ["Company: Escape Room", "Website", "Room Address", "Miles Away", "Number of Players", "Time Limit", "Difficulty", "Success Rate", "Scariness", "Age Requirement", "Dissimilarity Score"]
        
        return flask.render_template("favorite_recommendations.html", recommendation_table = recommendations.to_html(col_space = "4.5cm", classes = ["table-hover", "table-striped"], index = False, float_format = lambda x: "%10.2f" % x, justify = "center", render_links = True))
    else:
        return flask.render_template("input_favorite_room.html")

@app.route("/ideal_recommendations", methods = ["POST", "GET"])
def ideal_recommendation():
    if flask.request.method == "POST":
        # location
        user_location = flask.request.form["location"]
            
        # miles willing to travel from location
        miles_limit = int(flask.request.form["miles_limit"])
            
        # group size
        group_size = int(flask.request.form["group_size"])
            
        # youngest person in group
        youngest_person = int(flask.request.form["youngest_person"])

        # fear level
        fear_level = flask.request.form["fear_level"]

        # difficulty level
        difficulty_level = flask.request.form["difficulty_level"]

        # time limit in minutes
        time_limit_str = flask.request.form["time_limit_str"]

        # data frame of recommendations
        recommendations = ideal_room(user_location = user_location, miles_limit = miles_limit, group_size = group_size, youngest_person = youngest_person, time_limit_str = time_limit_str, fear_level = fear_level, difficulty_level = difficulty_level)

        # fill nan
        recommendations = recommendations.fillna("No info")

        # rename columns
        recommendations.columns = ["Company: Escape Room", "Website", "Room Address", "Miles Away", "Number of Players", "Time Limit", "Difficulty", "Success Rate", "Scariness", "Age Requirement", "Dissimilarity Score"]
        
        return flask.render_template("ideal_recommendations.html", recommendation_table = recommendations.to_html(col_space = "4.5cm", classes = ["table-hover", "table-striped"], index = False, float_format = lambda x: "%10.2f" % x, justify = "center", render_links = True))
    else:
        return flask.render_template("input_ideal_room.html")

if __name__ == "__main__":
	app.run(host = "0.0.0.0", debug = False)