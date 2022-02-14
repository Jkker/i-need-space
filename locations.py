import requests
from bs4 import BeautifulSoup
import json

url = "https://www.nyu.edu/students/student-information-and-resources/registration-records-and-graduation/registration/classroom-locations.html"


def classrooms_scraper():
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    d = {}
    for table in tables[1:]:
        table_data = []
        for row in table.find_all("tr"):
            if row("td"):
                table_data.append([
                    cell.text.strip().replace(' / ', ', ') for cell in row("td")
                ])
        d = {**d, **dict(table_data)}

    with open("data/locations.json", "w") as f:
        json.dump(d, f, indent=4)


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


if __name__ == "__main__":
    classrooms_scraper()