from flask import Flask, request, redirect, url_for, render_template
import requests
from datetime import datetime
import locale
import numpy as np
import sys
import urllib.parse

app = Flask(__name__)

@app.route("/")
def hello_world():
    """
    Renders the "index.html" template as the response for the root route.

    Returns:
        str: The rendered HTML content of the "index.html" template.
    """
    return render_template("index.html")

@app.route("/weather/<query>")
def display_weather(query:str):
    """Fetches weather data from the Met.no API, processes it, and renders a template with the results.

   Args:
       query: A string containing comma-separated latitude, longitude, and place information.

   Returns:
       TemplateResponse: Rendered "weather_results.html" template with processed weather data.
   """
    # Split the input query to extract latitude, longitude, and place information.
    lat, lon, place = query.split(',')[0], query.split(',')[1], query.split(',')[-1]
    place = urllib.parse.unquote_plus(place)

    # Make a GET request to the weather API with the specified latitude and longitude.
    response = requests.get(f'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}', headers={'user-agent': 'my-app/0.0.1'})

    # Parse the JSON response to get the timeseries, excluding the first entry.
    hours = response.json()["properties"]["timeseries"][1:]

    # Initialize variables for processing the weather data.
    days = []  # To store daily summaries.
    current_day_temp = []  # To store temperatures for the current processing day.

    # Set the locale for date and time formatting to Norwegian (Bokmål).
    locale.setlocale(locale.LC_TIME, 'nb_NO')

    # Initialize variables for tracking the current and last processed day.
    last_day = ""
    weekday = ""
    date = ""

    # Prepare variables for hourly data processing.
    accumulated_hours = []  # To accumulate hourly data for the current day.
    separated_hours = []  # To store separated hourly data by day.
    counter = 0

    # Loop through each hour in the timeseries to process and format the data.
    for hour in hours:
        # Convert the ISO format time to a datetime object, adjusting for timezone.
        time_and_date = datetime.strptime(hour["time"], "%Y-%m-%dT%H:%M:%SZ")
        weekday = time_and_date.strftime('%A').capitalize()

        # Initialize the last_day with the first hour's weekday if not already set.
        if last_day == "":
            last_day = weekday

        # Format the time and add a formatted day string to the hour dict.
        hour["time"] = f"{time_and_date.strftime('%H:%M')}"
        hour["day"] = f"{weekday} {time_and_date.strftime('%d %B,')}"
        
        # Round the air temperature for readability.
        hour["data"]["instant"]["details"]["air_temperature"] = round(float(hour["data"]["instant"]["details"]["air_temperature"]))

        # Handle missing short-term forecast data by using the 6-hour forecast if available.
        if not hour.get("data").get("next_1_hours") and hour.get("data").get("next_6_hours"):
            hour["data"]["next_1_hours"] = hour["data"]["next_6_hours"]
        
        # Add the current hour's temperature to the list for the current day.
        current_day_temp.append(hour["data"]["instant"]["details"]["air_temperature"])

        # Check if the day has changed based on the weekday.
        if last_day != weekday:
            # If there are recorded temperatures for the day, process them.
            if current_day_temp:
                max_temp = np.max(current_day_temp)  # Find the maximum temperature for the day.
                min_temp = np.min(current_day_temp)  # Find the minimum temperature for the day.
                
                # If there's a forecast for the next 12 hours, append the day's summary to the `days` list.
                if hour.get("data").get("next_12_hours"):
                    days.append({
                        "section_index": counter, 
                        "max": str(max_temp), 
                        "min": str(min_temp), 
                        "weekday": str(last_day), 
                        "date": str(date), 
                        "icon": hour["data"]["next_12_hours"]["summary"]["symbol_code"]
                    })

            # Accumulate and reset data for processing the next day.
            separated_hours.append({"hours": accumulated_hours, "index": str(counter)})
            counter += 1  # Increment the day counter.
            
            # Print the current day's temperatures to stdout for debugging/logging.
            print(current_day_temp, file=sys.stdout)
            
            # Reset variables for the next day's processing.
            accumulated_hours = []  # Reset the list of accumulated hours.
            current_day_temp = [hour["data"]["instant"]["details"]["air_temperature"]]  # Start with the current hour's temperature.
            last_day = weekday  # Update the last processed day.
        else:
            # If still within the same day, continue accumulating temperatures.
            current_day_temp.append(hour["data"]["instant"]["details"]["air_temperature"])

        # Update the date for the current processing hour.
        date = time_and_date.strftime(' %d. %B')
        # Accumulate the current hour's data.
        accumulated_hours.append(hour)

    # Print the days list to stdout for debugging/logging.
    print(days, file=sys.stdout)

    # Determine the current day's name for display purposes.
    current_day = datetime.now().strftime('%A').capitalize()

    # Render the weather results template with the processed data.
    return render_template('weather_results.html', current_day=current_day, section_count=counter-1, separated_hours=separated_hours, result=hours, days=days, place=place, current=hours[0])


@app.route("/place/<string:place_name>")
def get_place_info(place_name):
    """Retrieves information about a place from the Geonorge API.

   Args:
       place_name: The name of the place to search for.

   Returns:
       dict: The JSON response from the Geonorge API, containing place information.
   """
    response = requests.get(
        f'https://ws.geonorge.no/stedsnavn/v1/navn?sok={place_name}&fuzzy=true&treffPerSide=30'
    )

    return response.json()

@app.route("/search/", methods=["POST", "GET"])
def search_get():
    """Handles requests for the search page and redirecting after POST.

    Returns:
        Union[TemplateResponse, Response]:
            - If the request is a GET, returns the rendered "search.html" template.
            - If the request is a POST with valid search content, returns a redirect to
              the "search_result" view with the search query in the URL.
    """

    if request.method == "GET":
        return render_template("search.html")
    else:
        search_content = request.form.get("search_content")
        search_content = urllib.parse.quote_plus(search_content)
        if search_content:
            return redirect(url_for(endpoint="search_result", query=search_content))
        else:
            return redirect(url_for("search_get"))  # Example redirect to search




@app.route("/search/<query>")
def search_result(query:str):
    """Displays search results for a given place query.

    Args:
        query: The place name or location to search for (str).

    Returns:
        TemplateResponse: The rendered "search_query.html" template with
                        search results (dict) and the original query (str).

    Raises:
        HTTPException: If an error occurs during the search or rendering process.
    """
    query = urllib.parse.quote_plus(query)
    dictonary = get_place_info(query)
    return render_template('search_query.html', result=dictonary, query=query)