import requests as re
import json
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import aiohttp
import asyncio
from tqdm.asyncio import tqdm

ROOT_URL = "https://schedge.a1liu.com"
SUBJECT_URL = f"{ROOT_URL}/subjects"
SEMESTERS = ["fa", "su", "sp", "ja"]
SCHOOLS = ['NT', 'DN', 'NY', 'UA', 'UB', 'UC', 'UD', 'UE', 'UF', 'UG', 'UH', 'UN', 'GA', 'GB', 'GC', 'GE', 'US', 'UT', 'GG', 'UU', 'SHU', 'CD', 'GH', 'UY', 'GN', 'GP', 'GS', 'GT', 'GU', 'GX', 'GY', 'NB', 'NE', 'NH', 'NI', 'DC']

def get_subjects(save=True):
    res = re.get(SUBJECT_URL)
    subjects = res.json()
    if save:
        with open('./data/subjects.json', 'w') as f:
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
    school_keys = args.schools
    subjects = get_subjects()

    courses = await scrape(
        semester, year, {k: subjects[k]
                         for k in school_keys} if school_keys else subjects)
    with open(
            f"./data/{year}{semester}-{'_'.join(school_keys)}.json"
            if school_keys else f"./data/{year}{semester}.json", "w") as f:
        json.dump(courses, f, indent=4)


if __name__ == '__main__':
    parser = ArgumentParser(
        description=
        "Scrapes a specific semester's class schedule from the Schedge API (https://schedge.a1liu.com)",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--semester',
        dest='semester',
        required=True,
        type=str,
        choices=SEMESTERS,
    )
    parser.add_argument(
        '--year',
        dest='year',
        required=True,
        type=int,
    )
    parser.add_argument('--schools',
                        dest='schools',
                        required=False,
                        type=str,
                        nargs='+',
                        help="Schools to retain in the output. If not specified, all schools are included.")
    arguments = parser.parse_args()
    asyncio.run(main(arguments))