import requests
from bs4 import BeautifulSoup
import json
from utils import dump_json

url = "https://www.nyu.edu/students/student-information-and-resources/registration-records-and-graduation/registration/classroom-locations.html"


def classrooms_scraper():
    print('Scraping NYU classroom locations...')
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    d = {}
    for table in tables[1:]:
        table_data = []
        for row in table.find_all("tr"):
            if row("td"):
                table_data.append([
                    cell.text.strip().replace(' / ', ', ')
                    for cell in row("td")
                ])
        d = {**d, **dict(table_data)}

    with open("data/locations.json", "w") as f:
        json.dump(d, f, indent=4)
        print('✅ NYU classroom locations saved to data/locations.json')


def building_normalizer():
    with open("data/locations.json", "r") as f:
        data = json.load(f)

        def normalize(b):
            if b in data:
                # print(f'Replaced {b} with {data[b]}')
                return data[b]
            else:
                return b

        return normalize


import googlemaps
from dotenv import load_dotenv
from os import getenv

load_dotenv()

key = getenv('GOOGLE_MAPS_API_KEY')

G = googlemaps.Client(key=key)

places_cache = json.load(open('data/places_cache.json', 'r'))

places_error = json.load(open('data/places_error.json', 'r'))


def get_city_district(address_components):
    city, district = None, None
    for addr in address_components:
        if city is not None and district is not None:
            return city, district
        if "locality" in addr["types"]:
            city = addr["long_name"]
        if "sublocality_level_1" in addr["types"]:
            district = addr["long_name"]

    return city, district


def find_place(place, catch_error=True):
    if place in places_cache:
        return places_cache[place]
    if place in places_error:
        return None

    else:
        try:
            print(f'🗺️ Searching for {place}')
            res = G.find_place(input=place,
                               input_type='textquery',
                               fields=[
                                   'formatted_address', 'geometry/location',
                                   'name', 'place_id', 'address_component'
                               ],
                               location_bias='point:40.7294279,-73.9972212')

            if len(res['candidates']) == 0:
                raise Exception(f'No results for {place}')

            data = res['candidates'][0]
            item = dict()

            item['lat'] = data.get('geometry').get('location').get('lat')
            item['lng'] = data.get('geometry').get('location').get('lng')

            item['address'] = data.get('formatted_address')
            item['id'] = data.get('place_id')
            item[
                'url'] = 'https://www.google.com/maps/place/?q=place_id:' + item[
                    'id']
            item['name'] = data.get('name')
            item['name_nyu'] = place
            item['city'], item['borough'] = get_city_district(
                data.get('address_components'))

            places_cache[place] = item
            return item

        except Exception as e:
            places_error[place] = 'Not Found'

            dump_json(places_cache, 'data/places_cache.json', confirm=False)
            dump_json(places_error, 'data/places_error.json', confirm=False)

            if not catch_error:
                print('❌ Error finding place:', place, e)
                return e

            return None


if __name__ == "__main__":
    classrooms_scraper()