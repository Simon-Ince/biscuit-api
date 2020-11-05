import os  # for grbbing os variables
import base64  # for decoding os variables
from flask import Flask, request, render_template, jsonify  # for web
from datetime import datetime  # for working with time
import pytz  # for working with timezones

# for Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials


"""
Flask Setup
"""
app = Flask(__name__)
app.debug = os.getenv("DEBUG", True)

"""
Google Sheets Setup
"""
# Setup creds
gcreds = os.getenv("GCREDS", False)

if not os.path.exists("/creds"):
    os.makedirs("/creds")

with open("/creds/gcreds.json", "wb") as fh:
    fh.write(base64.b64decode(gcreds))

# use creds to create a client to interact with the Google Drive API
scope = ["https://spreadsheets.google.com/feeds"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/creds/gcreds.json", scope)
client = gspread.authorize(creds)

"""
Date & Time
"""
# set timezone to London
tz = pytz.timezone("Europe/London")

# determine time of day by hour
def time_of_day(hour):
    return (
        "Morning"
        if 10 <= hour <= 12
        else "Afternoon"
        if 13 <= hour <= 18
        else "Evening"
        if 19 <= hour <= 22
        else "Night"
        if 19 <= hour <= 22
        else None
    )


"""
Google Sheets
"""

# class for Google Sheet as an object
class Gs:
    def __init__(self):
        self.sheet = client.open_by_key("12oECP06QG6bgJ8LnpNawvJ0kRCIUm4Ej3TSewUQBKoM")
        self.values = self.read_all()

    def read_all(self):
        list_of_hashes = self.sheet.sheet1.get_all_records()
        return list_of_hashes

    def acceptable_now(self, date_time=None):

        # if the date_time has not been given...
        if date_time is None:
            # grab the current hour
            date_time = datetime.now(tz)

        # determine the time of day by Sophia's rules
        _time_of_day = time_of_day(date_time.hour)

        # prep our list of acceptable biscuits
        acceptable = {"time": _time_of_day, "date_time": date_time, "list": []}

        # check if each of our biscuits is acceptable or not
        for biscuit in self.values:
            # check it the biscuit is acceptable at this time of day
            if biscuit[_time_of_day] == "TRUE":
                # check it the biscuit is acceptable this month
                if (
                    date_time.strftime("%B") in biscuit["Acceptable Months"].split(",")
                    or biscuit["Acceptable Months"] == ""
                ):
                    acceptable["list"].append(biscuit)

        return acceptable


"""
Routes
"""

# index page
@app.route("/", methods=["GET"])
def index():
    # create Google Sheet object
    sheet = Gs()

    return render_template("index.html", data=sheet.acceptable_now())


# index page
@app.route("/api/v1/acceptable-now", methods=["GET"])
def api_acceptable_now():
    # create Google Sheet object
    sheet = Gs()

    # grab what's acceptable
    acceptable_now = sheet.acceptable_now()

    # prep our return data
    data = {
        "date_time": acceptable_now["date_time"].strftime("%Y-%m-%d %H:%M:%S %Z%z"),
        "time": acceptable_now["time"],
        "biscuits": [],
    }

    # loop through our acceptable biscuits and add them to our return data
    for biscuit in acceptable_now["list"]:
        item = {
            "biscuit": biscuit["Item"],
            "other_restrictions": biscuit["Other Restrictions"],
        }
        data["biscuits"].append(item)

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 80)))
