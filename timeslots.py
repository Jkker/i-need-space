import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
from argparse import ArgumentParser
from locations import building_normalizer


INVALID_LOCATIONS = ['No', 'TBA', 'Online', 'Off', 'To Be Arranged']

normalize_building = building_normalizer()


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
    building = normalize_building(building)
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


def add_valid_timeslot(time_slots, start, end, min_duration):
    s = int(start.replace(':', ''))
    e = int(end.replace(':', ''))
    if s > e: return
    if e - s <= min_duration: return
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
            rooms = schedule[building]
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
                    availabilities[building][room][weekday] = time_slots
        return schedule, availabilities


# TODO: filter by length of time
# TODO: filter by location
# TODO: find closest spaces at given time

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t',
                        '--time-range',
                        dest='time',
                        default=('08:00', '22:00'),
                        nargs=2,
                        help='start time')
    parser.add_argument('-m', '--min-duration',
                        dest='min_duration',
                        default=15,
                        type=int,
                        help='minimum duration for time slots')
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
                                    end=args.time[1],
                                    min_duration=args.min_duration)

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