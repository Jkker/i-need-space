This repository includes a set of tools to find the nearest vacant NYU classroom at a given time.

Output data can be found in the [`out`](out) folder.



## 🗺️ NYU Classroom Location Scraper

Scrapes NYU Classroom location data from [nyu.edu](https://www.nyu.edu/students/student-information-and-resources/registration-records-and-graduation/registration/classroom-locations.html).

Output is saved to `data/locations.json`

```sh
python locations.py
```

This file also includes a Google Maps API wrapper to find the exact location of each classroom.

The API Key is loaded from the `GOOGLE_MAPS_API_KEY` environment variable.

To obtain a Google Maps API key, visit [Google Maps Platform](https://console.cloud.google.com/google/maps-apis/start).



## 🗓️ NYU Class Schedule Scraper

Scrapes the class schedule of a semester in parallel from the [Schedge API](https://schedge.a1liu.com).

```sh
python schedge-scraper.py [-h] --semester SEMESTER --year YEAR [--subjects SUBJECTS [SUBJECTS ...]]
```


### Options
```text
  -h, --help            show this help message and exit
  --semester {fa,su,sp,ja}
  --year YEAR
  --schools [SCHOOLS ...]
        Schools to retain in the output. If not specified, all schools are included.
```

### Example Usage


```sh
python schedge-scraper.py --semester fa --year 2022 --subjects UA GA
```

This will scrape the class schedule for the Fall 2022 semester of Undergraduate and Graduate School.



## 🌟 Room Vacancy Calculator

Calculates when each room is available based on the class schedule with the assumption that a room is available if there are no classes scheduled during that time.

```sh
python vacancy-calculator.py [-h] [-t TIME TIME] [-m MIN_DURATION] [-s] [-o OUTPUT] filepath
```

### Options
```text
  -h, --help            show this help message and exit
  -t TIME TIME, --time-range TIME TIME
                        range of times to search for available times (default: ('08:00', '22:00'))
  -m MIN_DURATION, --min-duration MIN_DURATION
                        minimum duration (minutes) for a time slot to be valid (default: 15)
  -s, --save            save intermediate schedule file (default: False)
  -o OUTPUT, --output OUTPUT
                        output file (default: out/Vacancy-[INPUT_FILE_NAME].json)
```


### Example Usage

```sh
python vacancy-calculator.py --time-range '08:00', '22:00' --min-duration 15 --save --output out/Vacancy-2022fa.json data/2022fa.json
```

### Example Output
```json
{
  "Bobst Library": {
    "lat": 40.7296104,
    "lng": -73.9970712,
    "address": "70 Washington Square S, New York, NY 10012, United States",
    "id": "ChIJhwizUZBZwokRoumg8C3dKGA",
    "url": "https://maps.google.com/?cid=6929031216089852322",
    "name": "Elmer Holmes Bobst Library",
    "name_nyu": "Bobst Library",
    "city": "New York",
    "borough": "Manhattan",
    "rooms": {
      "LL151": { // Room Number
        "0": [
          [
            "09:15",
            "12:30"
          ],
          [
            "13:45",
            "16:55"
          ],
          [
            "19:25",
            "22:00"
          ]
        ],
        // 0 = Monday, 1 = Tuesday, etc.
      }
    }
  }
}
```