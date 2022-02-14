import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
from argparse import ArgumentParser

INVALID_LOCATIONS = ['No', 'TBA', 'Online']


def recursively_default_dict():
    return defaultdict(recursively_default_dict)


def parse_meeting(meeting):
    start = datetime.strptime(meeting['beginDate'], '%Y-%m-%d %H:%M:%S')
    end = start + timedelta(minutes=meeting['minutesDuration'])
    weekday = start.weekday()
    # return weekday, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')
    return weekday, start.strftime('%H:%M'), end.strftime('%H:%M')


def parse_location(location):
    loc_list = re.split(r'room\:?\s*|rm[:\s]|,\s*|\s\(',
                        location,
                        flags=re.IGNORECASE)
    building = loc_list[0].split('-')[0].replace('Bldg:', '').strip()
    room = loc_list[-1].strip()
    return building, room


def add_to_schedule(schedule, location, meetings):
    building, room = parse_location(location)
    if meetings and not (building in INVALID_LOCATIONS):
        for meeting in meetings:
            weekday, start, end = parse_meeting(meeting)
            if not schedule[building][room].get(weekday):
                schedule[building][room][weekday] = set()
            schedule[building][room][weekday].add((start, end))


def create_schedule(data):
    schedule = recursively_default_dict()
    for course in data:
        try:
            for session in course['sections']:
                add_to_schedule(schedule, session['location'],
                                session['meetings'])
                if not session.get('recitations'): continue
                for recitation in session['recitations']:
                    add_to_schedule(schedule, recitation['location'],
                                    recitation['meetings'])
        except:
            print(course)
    return schedule


def get_time_slots(times, start="08:00", end="22:00"):
    time_slots = []
    if start < times[0][0]:
        time_slots.append((start, times[0][0]))
    if len(times) > 1:
        for i in range(len(times) - 1):
            if times[i][1] < times[i + 1][0]:
                time_slots.append((times[i][1], times[i + 1][0]))
    if end > times[-1][1]:
        time_slots.append((times[-1][1], end))
    return time_slots


def main(filepath, start="08:00", end="22:00"):
    with open(filepath) as data_file:
        data = json.load(data_file)
        schedule = create_schedule(data)
        availabilities = recursively_default_dict()
        for building in sorted(schedule.keys()):
            rooms = schedule[building]
            for room in sorted(rooms.keys()):
                week = rooms[room]
                for weekday in range(7):
                    if weekday in week:
                        week[weekday] = sorted(list(week[weekday]),
                                               key=lambda x: x[0])
                        time_slots = get_time_slots(week[weekday], start, end)
                    else:
                        time_slots = [(start, end)]
                    availabilities[building][room][weekday] = time_slots
        return schedule, availabilities


# filter by length of time
# filter by location
# find closest spaces at given time

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t',
                        '--time-range',
                        dest='time',
                        default=('08:00', '22:00'),
                        nargs=2,
                        help='start time')
    parser.add_argument('-s',
                        '--save',
                        dest='save',
                        action='store_true',
                        help='save schedule file')
    parser.add_argument('-o', '--output', dest='output', help=f'output file')
    parser.add_argument('filepath',
                        default='./data/2022sp-UA_GA.json',
                        help='input file')

    args = parser.parse_args()

    schedule, availabilities = main(filepath=args.filepath,
                                    start=args.time[0],
                                    end=args.time[1])

    print('Found', len(availabilities.keys()), 'locations')
    filename = args.filepath.split("/")[-1]
    if args.save:
        save_filename = f'out/Schedule-{filename}'
        with open(save_filename, 'w') as f:
            json.dump(schedule, f, indent=2)
            print(f'Saved "{save_filename}"')
    output_filename = args.output or f'out/Slots-{filename}'
    with open(output_filename, 'w') as f:
        json.dump(availabilities, f, indent=2)
        print(f'Saved "{output_filename}"')