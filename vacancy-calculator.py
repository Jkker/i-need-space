import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from locations import building_normalizer, find_place, places_cache, places_error
from tqdm import tqdm
from utils import dump_json

INVALID_LOCATIONS = [
    'No', 'TBA', 'Online', 'Off', 'To Be Arranged', 'No Room Required',
    'Off-Campus', 'No room needed', 'Online'
]
INVALID_CAMPUS = [
    'Off Campus', 'Online', 'Distance Learning/Synchronous',
    'Distance Learning/Asynchronous'
]

normalize_building = building_normalizer()


def recursively_default_dict():
    return defaultdict(recursively_default_dict)


def parse_meeting(meeting):
    start = datetime.strptime(meeting['beginDate'], '%Y-%m-%d %H:%M:%S')
    end = start + timedelta(minutes=meeting['minutesDuration'])
    weekday = start.weekday()
    # return weekday, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')
    return weekday, start.strftime('%H:%M'), end.strftime('%H:%M')


def parse_location(location_str):
    loc_list = re.split(r'room\:?\s*|rm[:\s]|,\s*|\s\(',
                        location_str,
                        flags=re.IGNORECASE)
    building = loc_list[0].split('-')[0].replace('Bldg:',
                                                 '').replace('.', '').strip()
    building = normalize_building(building)
    location = find_place(building)

    if location is None:
        return None, None

    room = loc_list[-1].strip()

    return location, room


def add_to_schedule(schedule, location_str, meetings, campus):
    if campus in INVALID_CAMPUS:
        return
    if location_str in INVALID_LOCATIONS:
        return

    location, room = parse_location(location_str)

    if location is None:
        return

    location_name = location.get('name_nyu')

    schedule[location_name]['location'] = location

    if meetings and len(meetings):
        for meeting in meetings:
            weekday, start, end = parse_meeting(meeting)
            if not schedule[location_name]["rooms"][room].get(weekday):
                schedule[location_name]["rooms"][room][weekday] = set()
            schedule[location_name]["rooms"][room][weekday].add((start, end))


def create_schedule(data):
    print('Creating schedule...')
    schedule = recursively_default_dict()
    for course in tqdm(data):
        try:
            for section in course['sections']:

                add_to_schedule(schedule, section['location'],
                                section['meetings'], section['campus'])
                if not section.get('recitations'): continue
                for recitation in section['recitations']:
                    add_to_schedule(schedule, recitation['location'],
                                    recitation['meetings'], section['campus'])
        except Exception as e:
            raise e
            # print('Error:', course['name'])
    return schedule


def add_valid_timeslot(time_slots, start, end, min_duration):
    s = start.split(':')
    e = end.split(':')
    diff = (int(e[0]) - int(s[0])) * 60 + (int(e[1]) - int(s[1]))
    if diff < 0: return
    if diff <= min_duration:
        return
    time_slots.append((start, end))


# TODO: fix time slot errors
def get_time_slots(times, start, end, min_duration):
    time_slots = []
    if start < times[0][0]:
        add_valid_timeslot(time_slots, start, times[0][0], min_duration)
    if len(times) > 1:
        for i in range(len(times) - 1):
            add_valid_timeslot(time_slots, times[i][1], times[i + 1][0],
                               min_duration)
    if end > times[-1][1]:
        add_valid_timeslot(time_slots, times[-1][1], end, min_duration)
    return time_slots


def main(filepath, start="08:00", end="22:00", min_duration=15):
    with open(filepath) as data_file:
        data = json.load(data_file)
        schedule = create_schedule(data)
        availabilities = recursively_default_dict()
        for building in sorted(schedule.keys()):
            rooms = schedule[building]['rooms']
            availabilities[building] = schedule[building]['location']
            availabilities[building]['rooms'] = recursively_default_dict()
            for room in sorted(rooms.keys()):
                week = rooms[room]
                for weekday in range(7):
                    if weekday in week:
                        week[weekday] = sorted(list(week[weekday]),
                                               key=lambda x: x[0])
                        time_slots = get_time_slots(week[weekday], start, end,
                                                    min_duration)
                    else:
                        time_slots = [(start, end)]
                    availabilities[building]['rooms'][room][
                        weekday] = time_slots
        return schedule, availabilities


weekday_map = {0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'}


def get_rrule(weekdays):
    rrule = 'FREQ=WEEKLY;BYDAY='
    for weekday in weekdays:
        rrule += weekday_map[weekday]
    return rrule


def parse_meeting_ical(meeting):
    start = datetime.strptime(meeting['beginDate'], '%Y-%m-%d %H:%M:%S')
    end = start + timedelta(minutes=meeting['minutesDuration'])
    weekday = start.weekday()
    # return weekday, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')
    return weekday, start.strftime('%H:%M'), end.strftime('%H:%M')


def to_ical_dict(location, meetings):
    ical = ""
    building, room = parse_location(location)
    if meetings and not (building in INVALID_LOCATIONS):
        for meeting in meetings:
            start = datetime.strptime(meeting['beginDate'],
                                      '%Y-%m-%d %H:%M:%S')
            end = start + timedelta(minutes=meeting['minutesDuration'])


# TODO: filter by location
# TODO: find closest spaces at given time

if __name__ == '__main__':
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description=
        "Calculates when each room is available based on the class schedule")
    parser.add_argument('-t',
                        '--time-range',
                        dest='time',
                        default=('08:00', '22:00'),
                        nargs=2,
                        help='range of times to search for available times')
    parser.add_argument(
        '-m',
        '--min-duration',
        dest='min_duration',
        default=15,
        type=int,
        help='minimum duration (minutes) for a time slot to be valid')
    parser.add_argument('-s',
                        '--save',
                        dest='save',
                        action='store_true',
                        help='save intermediate schedule file')
    parser.add_argument('-o',
                        '--output',
                        dest='output',
                        default='out/Vacancy-[INPUT_FILE_NAME].json',
                        help=f'output file')
    parser.add_argument('filepath',
                        default='./data/2022sp-UA_GA.json',
                        help='input file')

    args = parser.parse_args()

    schedule, availabilities = main(filepath=args.filepath,
                                    start=args.time[0],
                                    end=args.time[1],
                                    min_duration=args.min_duration)

    print('🔎 Found', len(availabilities.keys()), 'locations')
    filename = args.filepath.split("/")[-1]
    if args.save:
        save_filename = f'out/Schedule-{filename}'
        dump_json(schedule, save_filename)

    output_filename = args.output if args.output != 'out/Vacancy-[INPUT_FILE_NAME].json' else f'out/Vacancy-{filename}'

    dump_json(availabilities, output_filename)
    dump_json(places_cache, 'data/places_cache.json')
    dump_json(places_error, 'data/places_error.json')
