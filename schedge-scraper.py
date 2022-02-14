import requests as re
import json
import argparse
import aiohttp
import asyncio
from tqdm.asyncio import tqdm

ROOT_URL = "https://schedge.a1liu.com"
SUBJECT_URL = f"{ROOT_URL}/subjects"
SEMESTERS = ["fa", "su", "sp", "ja"]


def get_subjects():
    res = re.get(SUBJECT_URL)
    subjects = res.json()
    with open('subjects.json', 'w') as f:
        json.dump(subjects, f, indent=4)
    return subjects


async def scrape(sem, year, subjects):
    data = []

    async with aiohttp.ClientSession() as session:
        if subjects:
            for subject in tqdm(subjects,
                                position=0,
                                desc="Subjects",
                                leave=False,
                                colour='#ffa502',
                                ncols=80):
                for subjectCode in tqdm(subjects[subject],
                                        position=1,
                                        desc=subject,
                                        leave=False,
                                        colour='yellow',
                                        ncols=80):
                    async with session.get(
                            f"{ROOT_URL}/{year}/{sem}/{subject}/{subjectCode}?full=true"
                    ) as res:
                        courses = await res.json()
                        if courses:
                            data = [*data, *courses]
                            # data.append(courses)
    return data


def write_to_file(data, sem, year):
    with open(f"./data/{year}{sem}.json", "w") as f:
        json.dump(data, f, indent=4)


async def main(args):
    semester = args.semester
    year = args.year
    subject_keys = args.subjects
    if semester not in SEMESTERS:
        raise ValueError("Invalid semester string!. Please try again")
    subjects = get_subjects()

    courses = await scrape(semester, year,
                        {k: subjects[k]
                         for k in subject_keys} if subject_keys else subjects)
    with open(f"./data/{year}{semester}-{'_'.join(subject_keys)}.json" if subject_keys else f"./data/{year}{semester}.json", "w") as f:
        json.dump(courses, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Quick script for scraping schedge")
    parser.add_argument('--semester',
                        '-sem',
                        dest='semester',
                        required=True,
                        type=str,
                        help="Semester to scrape from [fa, su, sp, ja]")
    parser.add_argument('--year',
                        '-yr',
                        dest='year',
                        required=True,
                        type=int,
                        help="Year to choose from")
    parser.add_argument(
        '--subjects',
        '-sub',
        dest='subjects',
        required=False,
        type=str,
        nargs='+',
    )
    arguments = parser.parse_args()
    asyncio.run(main(arguments))

    # main(arguments)