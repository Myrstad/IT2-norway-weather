from flask import Flask, request, redirect, url_for, render_template
import requests
import json
from datetime import datetime
import locale



app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/weather/<query>")
def display_weather(query:str):
    lat, lon = map(float, query.split(","))
    response = requests.get(f'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}', headers={'user-agent': 'my-app/0.0.1'})
    hours = response.json()["properties"]["timeseries"]
    locale.setlocale(locale.LC_TIME, 'nb_NO')
    for hour in hours:


        # dt_obj = datetime.fromisoformat(hour["time"].replace("Z", "+00:00"))

        # weekday = dt_obj.strftime("%A")
        # time = dt_obj.hour
        # hour["time"] = f"{weekday}, {time}"
        time_and_date = datetime.strptime(hour["time"], "%Y-%m-%dT%H:%M:%SZ")
        hour["time"] = f"{time_and_date.strftime('%A %d.%m')} klokka {time_and_date.strftime('%H:%M')}"
        
    #temps = [x["data"]["instant"]["details"]["air_temperature"] for x in hours]

    return render_template('weather_results.html', result=hours)
    #sreturn response.json()

@app.route("/place/<string:place_name>")
def get_place_info(place_name):
    response = requests.get(f'https://ws.geonorge.no/stedsnavn/v1/navn?sok={place_name}')
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