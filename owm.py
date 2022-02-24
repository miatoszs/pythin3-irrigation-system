#!/usr/bin/python3
import time, datetime
import json
import requests
import os.path

CACHE_EXPIRATION = 3600
KEY="936a03a9b66a08fc09f9279bf16528af"
onecall_url = 'https://api.openweathermap.org/data/2.5/onecall?lat=47.498&lon=19.0399&appid=' + KEY
history_url = 'https://api.openweathermap.org/data/2.5/onecall/timemachine?lat=47.498&lon=19.0399&dt='+ str(int(time.time() - 24*60*60))+ '&appid=' + KEY
IRRIGATION_MINIMUM_TEMPERATURE_THRESHOLD_VALUE = 20


def current(js):
   if 'current' in js:
     return(js['current'])
   return None

def today(js):
   if 'daily' in js:
     return(js['daily'][0])
   return None

def tomorrow(js):
   if 'daily' in js:
     return(js['daily'][1])
   return None

def unixtime2iso(t):
    return (datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S"))

def retrieve_url(url, cachefile):
    if cachefile and os.path.isfile(cachefile) and time.time() - os.path.getmtime(cachefile) < CACHE_EXPIRATION:
        print('Loading cached file:', cachefile)
        f = open(cachefile, 'r')
        js = json.load(fp=f)
        f.close()
        return(js)

    # print('Retrieving url :', url)
    r = requests.get(url)
    js = json.loads(r.content.decode("UTF-8"))
    if cachefile:
        f = open(cachefile, 'w')
        json.dump(js, fp=f, indent=4)
        f.close()
    return(js)

def K2C(kelvin):
    celsius = kelvin - 272.15
    return(celsius)

def is_watering_needed(js_hist, js):
    if is_watering_needed_based_on_yesterday_rainfall(js_hist) and is_watering_needed_based_on_temperatue_forecast(js):
        return(True)
    return(False)

def is_watering_needed_based_on_yesterday_rainfall(js):
    '''
    {'dt': 1641301200, 'temp': 284.27,KEY="936a03a9b66a08fc09f9279bf16528af"
 'feels_like': 283.4, 'pressure': 1004, 'humidity': 75, 'dew_point': 280.01, 'uvi': 0.19, 'clouds': 90, 'visibility': 10000, 'wind_speed': 1.34
    , 'wind_deg': 220, 'wind_gust': 3.13, 'weather': [{'id': 500, 'main': 'Rain', 'description': 'light rain', 'icon': '10d'}]}
    '''
    rainfall = False
    for hour in js['hourly']:
        for i in hour['weather']:
            if i['main']=='Rain':
                #print(hour['dt'], h)
                rainfall = True
    return(not rainfall)

def get_rainfall_volume(js):
    '''
    {'dt': 1641301200, 'temp': 284.27,KEY="936a03a9b66a08fc09f9279bf16528af"
 'feels_like': 283.4, 'pressure': 1004, 'humidity': 75, 'dew_point': 280.01, 'uvi': 0.19, 'clouds': 90, 'visibility': 10000, 'wind_speed': 1.34
    , 'wind_deg': 220, 'wind_gust': 3.13, 'weather': [{'id': 500, 'main': 'Rain', 'description': 'light rain', 'icon': '10d'}]},
    {"dt": 1645448400, "temp": 280.17, "feels_like": 276.36, "pressure": 1005, "humidity": 88, "dew_point": 278.32, "uvi": 0.32, "clouds": 100, "visibility": 5000, "wind_speed": 6.71, "wind_deg": 283, "wind_gust": 12.96, "weather": [ { "id": 501, "main": "Rain", "description": "moderate rain", "icon": "10d" } ], "rain": { "1h": 1 } }
    '''
    rain_volume = 0
    for hour in js['hourly']:
        if 'rain' in hour:
            rain_volume += float(hour['rain']['1h'])
    return(rain_volume)


def is_watering_needed_based_on_temperatue_forecast(js):
    '''Don't water when today's forecast temperature is less than 20
    inputs: oncall.js
    outputs: True, or False
    '''
    irrigate = False
    for counter, hour in enumerate(js['hourly']):
        if counter == 24:
            break
        # print(counter, f"{K2C(hour['temp']):02.1f}")
        if K2C(hour['temp']) > IRRIGATION_MINIMUM_TEMPERATURE_THRESHOLD_VALUE:
            irrigate = True
            break
    return(irrigate)

if __name__ == '__main__':
    js_hist = retrieve_url(history_url, '.history.js')
    for h in js_hist['hourly']:
        if 'rain' in h:
            print(h['dt'], unixtime2iso(h['dt']), f"{K2C(h['temp']):02.1f}", h['weather'][0]['main'], h['rain'])
        else:
            print(h['dt'], unixtime2iso(h['dt']), f"{K2C(h['temp']):02.1f}", h['weather'][0]['main'] )

    js = retrieve_url(onecall_url, '.onecall.js')
    for h in js['hourly']:
        if 'rain' in h:
            print(h['dt'], unixtime2iso(h['dt']), f"{K2C(h['temp']):02.1f}", h['weather'][0]['main'], h['rain'])
        else:
            print(h['dt'], unixtime2iso(h['dt']), f"{K2C(h['temp']):02.1f}", h['weather'][0]['main'] )

    print('get_rainfall_volume for yesterday:', get_rainfall_volume(js_hist), 'mm')
    print('get_rainfall_volume for next 48h:', get_rainfall_volume(js), 'mm')
    print('is_watering_needed_based_on_yesterday_rainfall:', is_watering_needed_based_on_yesterday_rainfall(js_hist))
    print('is_watering_needed_based_on_temperatue_forecast:', is_watering_needed_based_on_temperatue_forecast(js))
    print('is_watering_needed:', is_watering_needed(js_hist, js))
