# IT2-norway-weather

## Getting started

You can see the deplyed webapplication at [https://it-2-norway-weather.vercel.app/](https://it-2-norway-weather.vercel.app/)

Or you can clone this repository and run the flask app locally, eg. in windows cmd:

```
$ git clone https://github.com/Myrstad/IT2-norway-weather.git my-dir
$ cd ./my-dir
$ pip install -r requirements.txt
$ python -m flask --app api.main --debug run
```

## API's

[Geodata](https://ws.geonorge.no/stedsnavn/v1/) for getting lon and lat for place name

[Weather dara](https://api.met.no/weatherapi/locationforecast/2.0/documentation) for getting weather info from lon lat