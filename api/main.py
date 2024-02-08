from flask import Flask, request, redirect, url_for, render_template
import requests
import json
from datetime import datetime
import locale
import numpy as np
import sys

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/weather/<query>")
def display_weather(query:str):
    lat, lon, place = query.split(',')[0], query.split(',')[1], query.split(',')[-1]
    response = requests.get(f'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}', headers={'user-agent': 'my-app/0.0.1'})
    hours = response.json()["properties"]["timeseries"][1:]
    days = []
    current_day_temp = []
  
    locale.setlocale(locale.LC_TIME, 'nb_NO')
    last_day = ""
    weekday = ""
    date = ""
   
    current_hour = hours[0]

    accumulated_hours = []
    separated_hours = []

    skip_next = False
    counter = 0

    for hour in hours:

        # dt_obj = datetime.fromisoformat(hour["time"].replace("Z", "+00:00"))

        # weekday = dt_obj.strftime("%A")
        # time = dt_obj.hour
        # hour["time"] = f"{weekday}, {time}"
        time_and_date = datetime.strptime(hour["time"], "%Y-%m-%dT%H:%M:%SZ")
        weekday = time_and_date.strftime('%A').capitalize()
        
        if last_day == "":
            last_day = weekday
        
        hour["time"] = f"{time_and_date.strftime('%H:%M')}"
        hour["day"] = f"{weekday} {time_and_date.strftime('%d %B,')}"
        hour["data"]["instant"]["details"]["air_temperature"] = round(float(hour["data"]["instant"]["details"]["air_temperature"]))
        
        current_day_temp.append(hour["data"]["instant"]["details"]["air_temperature"])
       

        if last_day != weekday:
            if current_day_temp:  # Check if current_day_temp has entries to avoid division by zero.
                max_temp = np.max(current_day_temp)  # Calculate max temperature for the day.
                min_temp = np.min(current_day_temp)  # Calculate max temperature for the day.
                if hour.get("data").get("next_12_hours"):
                    days.append({"section_index":counter, "max":str(max_temp), "min":str(min_temp), "weekday":str(last_day), "date":str(date), "icon":hour["data"]["next_12_hours"]["summary"]["symbol_code"]})  # Append max temperature with the correct day's name.

          
            
            separated_hours.append({"hours":accumulated_hours, "index":str(counter)})
            # if not hour["data"].get("next_1_hours):

            #     skip_next = True
            counter += 1
            
            accumulated_hours = []       
            print(current_day_temp, file=sys.stdout)
            # Reset for the next day's data.
            current_day_temp = [hour["data"]["instant"]["details"]["air_temperature"]]  # Start new day with the current hour's temperature.
            last_day = weekday  # Update last_day to the current day after processing.
        else:
            # If still within the same day, just keep collecting temperatures.
            current_day_temp.append(hour["data"]["instant"]["details"]["air_temperature"])
        date = time_and_date.strftime(' %d. %B')
        accumulated_hours.append(hour)
    #temps = [x["data"]["instant"]["details"]["air_temperature"] for x in hours]
    
    print(days, file=sys.stdout)
    current_day = datetime.now().strftime('%A').capitalize()
    return render_template('weather_results.html', current_day=current_day, section_count=counter, separated_hours=separated_hours, result=hours, days=days, place=place, current=current_hour)
    #return response.json()

@app.route("/place/<string:place_name>")
def get_place_info(place_name):
    response = requests.get(f'https://ws.geonorge.no/stedsnavn/v1/navn?sok={place_name}&fuzzy=true&treffPerSide=30')
    return response.json()

@app.route("/search/", methods=["POST", "GET"])
def search_get():
    if request.method == "GET":
        return render_template("search.html")
    else:
        search_content = request.form['search_content']
        return redirect(url_for(endpoint='search_result', query=search_content))

@app.route("/search/<query>")
def search_result(query:str):
    dictonary = get_place_info(query)
    #lon = dictonary["representasjonspunkt"]
    #lat = 
    return render_template('search_query.html', result=dictonary, query=query)
    #info = [(x['fylker'][0]['fylkesnavn'], x['kommuner'][0]['kommunenavn'], x['skrivemåte'], x['representasjonspunkt']['nord'], x['representasjonspunkt']['øst']) for x in dictonary['navn']]
    #lenker = "".join([f'<p><a href="/weather/{x[-2]},{x[-1]}">{x[2]}, {x[1]}, {x[0]}</a></p>' for x in info])
    #return lenker