# Next Escape
Next Escape ([nextescape.me](nextescape.me)) recommends escape rooms based on one of two search options:
1. Users can enter their **favorite escape room**, and Next Escape will recommend similar escape rooms to their favorite.
2. Users can enter their **ideal escape room**, and Next Escape will recommend similar escape rooms to their ideal.

## Data Source
[worldofescapes.com](https://worldofescapes.com/)

## Escape Room Features
* Difficulty Level: Very easy, Easy, Average, Difficult, Very Difficulty
* Success Rate: 0-100% (scaled so 1 unit = 20%)
* Fear Level: Not scary, A little scary, Scary, Very scary
* Time Limit: 30-120 minutes (scaled so 1 unit = 15 minutes)

## Escape Room Filters
* Travel Limit: Limit recommended rooms to those within user-entered travel limit (in miles) from their location where they're looking for escape rooms
* Group Size: Limit recommended rooms to those whose max number of players is greater than or equal to the size of the user's group
* Age Requirement: Limit recommended rooms to those whose age requirement is less than or equal to the youngest member of the user's group

## Methods
Recommend rooms based on the smallest [euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance#:~:text=In%20mathematics%2C%20the%20Euclidean%20distance,metric%20as%20the%20Pythagorean%20metric.) between user-entered rooms (their favorite or ideal room) and rooms that meet their filter requirements (described above)

## Missing Data
If escape rooms were missing data for fear level or time limit, I imputed the most frequent values for those features: "Not scary" and "60 minutes". If escape rooms were missing data for difficulty level or success rate, I imputed predicted values from a linear regression: difficulty level regressed on success rate or vice versa.
