#!/usr/bin/python
import flask
import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import geopy
from geopy import distance

# create and configure the app
app = flask.Flask(__name__)
app.config.from_object(__name__)

# data
## read room data
room_data = pd.read_csv("data/room_data.csv")

## read city and state data
state_city_data = pd.read_csv("data/state_city_room_url_df.csv")

## merge
escape_rooms = room_data.merge(state_city_data, left_on = "woe_room_url", right_on = "woe_room_url", how = "left")

# define functions
## returns matrix of euclidian distances
def pairwise_dist(data_frame, features, index):
    # full dataset of features, replace "None" with None
    X_full = data_frame.loc[:, features].mask(data_frame.loc[:, features].eq("None"))

    # imputer parameters (default estimator is BayesianRidge())
    imputer = IterativeImputer(max_iter = 10, random_state = 39248)

    # fit imputation model
    imputer_fit = imputer.fit(X_full)

    # predict missing values
    X_predict = imputer_fit.transform(X_full)
    
    # distance matrix
    dist_matrix = pd.DataFrame(
    # euclidian distances
    sklearn.metrics.pairwise.euclidean_distances(
        # standardize ((x - mean / sd))
        sklearn.preprocessing.StandardScaler().fit_transform(X_predict)
    ))
    
    # add columns and index
    dist_matrix.columns = data_frame[index]
    dist_matrix.index = data_frame[index]
    
    return dist_matrix

## returns table of recommended rooms and their information
def recommend_rooms(user_location, travel_limit, room_played, features = ["min_players", "max_players", "time_limit", "difficulty_int", "success_rate", "fear_int"], other_var = ["query_address", "woe_room_url", "miles2room"]):
    # user location data
    user_address_query, user_latitude, user_longitude = get_lat_long(user_location)
    
    # compute miles away from each room in database
    miles2room = [distance.geodesic((user_latitude, user_longitude), (room_latitude, room_longitude)).miles for room_latitude, room_longitude in zip(state_city_room_data["room_latitude"], state_city_room_data["room_longitude"])]
    
    # add to data frame
    state_city_room_data["miles2room"] = miles2room
    
    # subset escape room database to rooms within travel limit
    # note that is same length of data frame
    escape_rooms_subset = state_city_room_data.loc[np.array(miles2room) <= travel_limit, :]
    
    # z-score features and compute pairwise euclidian distance matrix
    escape_room_distances = pairwise_dist(escape_rooms_subset, features, "company_and_room")
    
    # rank rooms based on similarity to room user input
    rooms_ranked = (escape_room_distances.loc[room_played]
    .sort_values()
    .to_frame()
    .reset_index(level = 0)
    .rename(columns = {"index": "company_and_room", room_played: "distance"}))
 
    # left join with subset of escape rooms
    escape_rooms_subset = rooms_ranked.merge(escape_rooms_subset, how = "left", on = "company_and_room")
 
    # 3 most similar and 3 most dissimilar
    recommended_rooms = rooms_ranked["company_and_room"].values[:4].tolist() + rooms_ranked["company_and_room"].values[-3:].tolist()
 
    return escape_rooms_subset.loc[escape_rooms_subset["company_and_room"].isin(recommended_rooms), other_var + ["distance"] + features].sort_values(by = "distance")

# index html makes it pretty looking
@app.route("/")
def index():
    return flask.render_template("index.html")


if __name__ == "__main__":
    app.run(host = "0.0.0.0", debug = False)