import rasterio
from PIL import Image
import numpy as np
from affine import Affine
from pyproj import Proj, transform
import requests
import itertools
import random
import time
import sys, getopt

"""
To study the sample data
Reference:
http://www.bom.gov.au/climate/averages/tables/cw_08 6071_All.shtml
http://www.bom.gov.au/climate/averages/tables/cw_08 6071_All.shtml
http://www.australia.com/en/facts/weather/melbourne-weather.html
https://github.com/Renien/generate-weather-data.git
https://www.australiasevereweather.com/cyclones/tropical_cyclone_intensity_scale.htm

   Temperature : Max Mean (+- 40 c) Min Mean (+- 10 c)
   Snow time temp: max 7 min -2
   Raining temp: max 25 min 15
   humidity min 55 max 70
   pressure max 1200 - 700
"""

# Conditions to generate sample data
weather_conditions = {"Sunny": {"temperature": (40, 10), "pressure": (1200, 700), "humidity": (70, 55)},
                      "Rain": {"temperature": (25, 15), "pressure": (1200, 700), "humidity": (70, 55)},
                      "Snow": {"temperature": (-1, -7), "pressure": (1200, 700), "humidity": (70, 55)}}

# Sample IATA code for weather stations
stations = {"SYD": "Sydney", "MEL": "Melbourne", "ADL": "Adelaide", "PER": "Perth", "BRB": "Brisbane",
            "DAR": "Darwin", "HOB": "Hobart", "CAN": "Canberra", "ABX": "Albury", "BNK": "Ballina"}

round_robin_stations = itertools.cycle(stations.keys())


def strTimeProp(start, end, format, prop):
    """
    This function will help to shift time
    based on the random selection

    :return: Date Time
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


# Random date time generator
def randomDate(start, end, prop):
    return strTimeProp(start, end, '%Y-%m-%d %H:%M:%S', prop)


def genWeather():
    """
    Randomly generate dummy data for weather
    - Weather condition
    - Temperature
    - Pressure
    - Humidity
    :return: Concatenated string using '|'
    """

    weather = random.choice(weather_conditions.keys())
    condition = weather_conditions[weather]
    (tMax, tMin) = condition["temperature"]
    (pMax, pMin) = condition["pressure"]
    (hMax, hMin) = condition["humidity"]

    return weather + "|" + str(round(random.uniform(tMax, tMin), 1)) + "|" + \
           str(round(random.uniform(pMax, pMin), 1)) + "|" + \
           str(random.randrange(hMax, hMin, -1))

# convert the geo file type, from the high definition .PNG to low definition .tif
def png2tif(inputfile):
    img = Image.open(inputfile)

    print img.format, img.size, img.mode
    new_img = img.thumbnail((21600/10, 10800/10))

# con_img = img.convert("TIF")
    converted_file = img.save('converted.tif','TIFF',quality=100)
    return png2tif(converted_file)


# Arg parser
def main(argv):
    inputfile = ''
    random_station = ''
    try:
        opts, args = getopt.getopt(argv, "hi:r:", ["ifile=", "rstatus="])
    except getopt.GetoptError:
        print 'GenerateWeather.py -i <file path>/<geo file name>  -ry '
        print 'tiff is the default image format, the script will convert the rest of formats (png/jpg/bmp/jpeg) to tiff format automatically, with different quality and definition'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
           # print 'GenerateWeather.py -i (geo file .tif or .png format) <file path> -ry <y/n>'
            print 'GenerateWeather.py -i <file path>/<geo file name>  -ry '
            print 'tiff is the default image format, the script will convert the rest of formats (png/jpg/bmp/jpeg) to tiff format automatically, with different quality and definition'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-r", "--rstatus"):
            random_station = arg
    print 'GEO file is "', inputfile
    return (inputfile, random_station)


if __name__ == '__main__':

    # extract the args
    (img_file, random_selection) = main(sys.argv[1:])

    ## check the image file format, convert them into .tif format if it is not

    ## convert the image file format-- from (.png', '.jpg', '.jpeg' ) to .tif format
    ## To be case-insensitive, and to eliminate a potentially large else-if chain:
    #m.lower().endswith(('.png', '.jpg', '.jpeg'))

    if img_file.lower().endswith(('.png', '.jpg','.bmp', '.jpeg')):

         #img_file_2 = png2tif(img_file)
         img = Image.open(img_file).convert('1')

         print img.format, img.size, img.mode
         new_img = img.thumbnail((21600/10, 10800/10))
         converted_file = img.save('converted.tif','TIFF',quality=100)
         p1 = Proj(init='epsg:4326', no_defs='True')
         img_file_2 = 'converted.tif'
    else:
         img_file_2 = img_file

    print img_file_2
    # con p1 = Proj(r.crs)vert the PNG format into TIF format, reduce the size of the big file
     # Read raster
    with rasterio.open(img_file_2) as r:

        T0 = r.transform # replace r.affine  # upper-left pixel corner affine transform

        if img_file.lower().endswith(('.png', '.jpg','.bmp' ,'.jpeg')):
            p1 = Proj(init='epsg:4326', no_defs='True')
        else:
            p1 = Proj(r.crs)

        A = r.read(1)  # pixel values

    # All rows and columns
        cols, rows = np.meshgrid(np.arange(A.shape[1]), np.arange(A.shape[0]))

    # Get affine transform for pixel centres
        T1 = T0 * Affine.translation(0.5, 0.5)
    # Function to convert pixel row/column index (from 0) to easting/northing at centre
        rc2en = lambda r, c: (c, r) * T1

    # Based on the size of the data this will take some time
        eastings, northings = np.vectorize(rc2en, otypes=[np.float, np.float])(rows, cols)

    # Project all longitudes, latitudes
        p2 = Proj(proj='latlong', datum='WGS84')
        longs, lats = transform(p1, p2, eastings, northings)

    weatherFile = open("weather_generated.dat", "w")

# Sample data is generate in a sequential process.
    for r in range(0, len(longs)):
        s_long = longs[r]
        s_lats = lats[r]

    for i in range(0, len(s_long)):
        iat = ''
        if random_selection == 'y':
            # Get a round robin select from 'round_robin_stations' and generate the test data
            iat = round_robin_stations.next()
        else:
            # Extract the station from geo code and generate the test data
            r = requests.get('http://iatageo.com/getCode/' + str(s_lats[i]) + '/' + str(s_long[i]))
            iat = r.json()['IATA']

        datetime = randomDate("2007-11-11 00:00:00", "2017-11-19 23:00:00", random.random())
        weather = genWeather()
        geo = str(s_lats[i]) + "," + str(s_long[i])
        d = str(iat) + "|" + geo + "|" + datetime + "|" + weather + "\n"

        weatherFile.write(d)


weatherFile.close()
print "The script completed successfully!!!"
print "Generated the file weather_generated.dat in curren running folder !"