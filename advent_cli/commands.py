import curses
import importlib
import os
import pytz
import re
import requests
import sys
import time
import configparser

from bs4 import BeautifulSoup
from datetime import datetime as dt
from tabulate import tabulate

from . import config
from .utils import (
    colored,
    compute_answers,
    custom_markdownify,
    get_time_until_unlock,
    submit_answer,
    Status
)

def infer_year():
    selected = 2015
    for y in range(2015, dt.now().year + 1):
        if os.path.exists(f'{y}/'):
            selected = y
    return f'{selected:04}'

def infer_day(year):
    selected = 0
    for d in range(1, 26):
        
        path = f'{year}/{d:02}/'
        if os.path.exists(path):
            selected = d
        else:
            break
    return f'{selected:02}'

def load_configuration():
    lconfig = configparser.ConfigParser()
    lconfig.read('aoc_cli_config.ini')
    if 'DEFAULT' not in lconfig:
        lconfig['DEFAULT'] = {}
    if 'year' not in lconfig['DEFAULT']:
        lconfig['DEFAULT']['year'] = infer_year()
    if 'day' not in lconfig['DEFAULT']:
        lconfig['DEFAULT']['day'] = infer_day(lconfig['DEFAULT']['year'])
    lconfig.write(open('aoc_cli_config.ini', 'w'))
    print(colored("Configured Day: " + lconfig['DEFAULT']['year'] + "/" + lconfig['DEFAULT']['day'], "grey"))    
    return lconfig
    

my_config = load_configuration()
selected_year = my_config['DEFAULT']['year']
selected_day = my_config['DEFAULT']['day']
def raw_set_year(year):
    globals()['selected_year'] = year
    my_config.set('DEFAULT', 'year', year)
    my_config.write(open('aoc_cli_config.ini', 'w'))

def raw_set_day(day):
    globals()['selected_day'] = day
    my_config.set('DEFAULT', 'day', day)
    my_config.write(open('aoc_cli_config.ini', 'w'))


def raw_get_year():
    return globals()['selected_year']
def raw_get_day():
    return globals()['selected_day']


def set_year(year):
    if isinstance(year, int):    
        year = f'{year}'
    raw_set_year(year)

    #os.environ['ADVENT_CLI_YEAR'] = year

    print(f'Selected year: {year}')
    path = f'{year}/'
    
    if not os.path.exists(path):
        os.makedirs(path)
    day = '00'
    for d in range(1, 26):
        path = f'{year}/{d:02}/'
        if os.path.exists(path):
            day = f'{d:02}'
        else:
            break
    set_day(day)

def set_day(day):
    if isinstance(day, int):        
        day = f'{day:02}'
    raw_set_day(day)
    print(f'Selected day: {day}')

def get_year():
    return raw_get_year()
def get_day():
    return raw_get_day()



def get(year, day):
    if not year:
        year = get_year()
    if not day:
        day = int(get_day())
        if day == 25:
            print("Completed all days for this year!")
            return
        day += 1
        day = f'{day:02}'

    print(colored(f"Getting {year}/{day}", "yellow"))        
    set_day(day)
    
    

    template = importlib.resources.read_text('advent_cli', 'template.txt')
    if os.path.exists(f'{year}/{day}/'):
        print(colored('Directory already exists:', 'red'))
        print(colored(f'  {os.getcwd()}/{year}/{day}/', 'red'))
        return

    conf = config.get_config()
    r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}',
                     cookies={'session': conf['session_cookie']})
    if r.status_code == 404:
        if 'before it unlocks!' in r.text:
            print(colored('This puzzle has not unlocked yet.', 'red'))
            print(colored(f'It will unlock on Dec {day} {year} at midnight EST (UTC-5).',
                          'red'))
            print(colored(f'Use "advent countdown {year}/{day}" to view a live countdown.',
                          'grey'))
            return
        else:
            print(colored('The server returned error 404 for url:', 'red'))
            print(colored(f'  "https://adventofcode.com/{year}/day/{int(day)}/"', 'red'))
            return
    elif '[Log In]' in r.text:
        print(colored('Session cookie is invalid or expired.', 'red'))
        return

    os.makedirs(f'{year}/{day}/')

    soup = BeautifulSoup(r.text, 'html.parser')
    part1_html = soup.find('article', class_='day-desc').decode_contents()

    # remove hyphens from title sections, makes markdown look nicer
    part1_html = re.sub('--- (.*) ---', r'\1', part1_html)

    # also makes markdown look better
    part1_html = part1_html.replace('\n\n', '\n')

    with open(f'{year}/{day}/prompt.md', 'w') as f:
        f.write(custom_markdownify(part1_html))
    print(f'Downloaded prompt to {year}/{day}/prompt.md')

    

    r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}/input',
                     cookies={'session': conf['session_cookie']})
    with open(f'{year}/{day}/input.txt', 'w') as f:
        f.write(r.text)
    print(f'Downloaded input to {year}/{day}/input.txt')

    with open(f'{year}/{day}/solution.py', 'w') as f:
        f.write(f'## advent of code {year}\n'
                f'## https://adventofcode.com/{year}\n'
                f'## day {day}\n\n')
        f.write(template)
    print(f'Created {year}/{day}/solution.py')


def stats(year):
    today = dt.today()
    if today.year <= int(year) and today.month < 12:
        print(colored(f'Defaulting to previous year ({today.year - 1}).', 'red'))
        year = str(today.year - 1)

    conf = config.get_config()
    r = requests.get(f'https://adventofcode.com/{year}/leaderboard/self',
                     cookies={'session': conf['session_cookie']})
    if '[Log In]' in r.text:
        print(colored('Session cookie is invalid or expired.', 'red'))
        return

    soup = BeautifulSoup(r.text, 'html.parser')

    table = soup.select('article pre')[0].text
    table_rows = [x.split() for x in table.split('\n')[2:-1]]

    stars_per_day = [0] * 25
    for row in table_rows:
        stars_per_day[int(row[0]) - 1] = 2 if row[4:7] != ['-', '-', '-'] \
                                           else 1 if row[1:4] != ['-', '-', '-'] \
                                           else 0

    print('\n         1111111111222222\n1234567890123456789012345')

    today = dt.now(pytz.timezone('America/New_York'))
    for i, stars in enumerate(stars_per_day):
        if stars == 2:
            print(colored('*', 'yellow'), end='')
        elif stars == 1:
            print(colored('*', 'cyan'), end='')
        elif stars == 0 and today.year == int(year) and today.day < (i + 1):
            print(' ', end='')
        else:
            print(colored('*', 'grey'), end='')

    print(f" ({sum(stars_per_day)}{colored('*', 'yellow')})\n")
    print(f'({colored("*", "yellow")} 2 stars) '
          f'({colored("*", "cyan")} 1 star) '
          f'({colored("*", "grey")} 0 stars)\n')

    print(tabulate(table_rows, stralign='right', headers=[
        '\nDay',
        *['\n'.join([colored(y, 'cyan') for y in x.split('\n')])
            for x in ['----\nTime', '(Part 1)\nRank', '----\nScore']],
        *['\n'.join([colored(y, 'yellow') for y in x.split('\n')])
            for x in ['----\nTime', '(Part 2)\nRank', '----\nScore']]
    ]), '\n')

    if conf['private_leaderboards']:
        num_private_leaderboards = len(conf['private_leaderboards'])
        print(colored(f'You are a member of {num_private_leaderboards} '
                      f'private leaderboard(s).', 'grey'))
        print(colored(f'Use "advent stats {year} --private" to see them.\n', 'grey'))


def private_leaderboard_stats(year):
    today = dt.today()
    if today.year <= int(year) and today.month < 12:
        print(colored(f'Defaulting to previous year ({today.year - 1}).', 'red'))
        year = str(today.year - 1)

    conf = config.get_config()
    if conf['private_leaderboards']:
        for board_id in conf['private_leaderboards']:
            r = requests.get(
                f'https://adventofcode.com/{year}/leaderboard/private/view/{board_id}',
                cookies={'session': conf['session_cookie']}
            )
            if '[Log In]' in r.text:
                print(colored('Session cookie is invalid or expired.', 'red'))
                return

            soup = BeautifulSoup(r.text, 'html.parser')

            intro_text = soup.select('article p')[0].text
            board_owner = soup.find('div', class_='user').contents[0].strip() \
                if 'This is your' in intro_text \
                else re.findall(r'private leaderboard of (.*) for', intro_text)[0]

            rows = soup.find_all('div', class_='privboard-row')[1:]

            top_score_len = len(rows[0].find_all(text=True, recursive=False)[0].strip())
            print(f"\n{board_owner}'s private leaderboard {colored(f'({board_id})', 'grey')}")
            print(f'\n{" "*(top_score_len+14)}1111111111222222'
                  f'\n{" "*(top_score_len+5)}1234567890123456789012345')

            for row in rows:
                position = row.find('span', class_='privboard-position').text
                if len(position) == 2:
                    position = " " + position
                stars = row.find_all('span', class_=re.compile('privboard-star-*'))
                name = row.find('span', class_='privboard-name').text
                name_link = row.select('.privboard-name a')[0].attrs['href'] \
                    if len(row.select('.privboard-name a')) else None
                score = row.find_all(text=True, recursive=False)[0].strip()

                print(f'{position} {score:>{top_score_len}}', end=' ')
                for span in stars:
                    class_ = span.attrs['class'][0]
                    if 'both' in class_:
                        print(colored('*', 'yellow'), end='')
                    elif 'firstonly' in class_:
                        print(colored('*', 'cyan'), end='')
                    elif 'unlocked' in class_:
                        print(colored('*', 'grey'), end='')
                    elif 'locked' in class_:
                        print(' ', end='')

                print(f' {name}', end=' ')
                print(f'({colored(name_link, "blue")})' if name_link is not None else '')

            print()
            print(f'({colored("*", "yellow")} 2 stars) '
                  f'({colored("*", "cyan")} 1 star) '
                  f'({colored("*", "grey")} 0 stars)\n')
    else:
        print(colored('You are not a member of any private leaderboards '
                      'or you have not configured them.', 'red'))
        print(colored('Set the environment variable ADVENT_PRIV_BOARDS to '
                      'a comma-separated list of private leaderboard IDs.', 'red'))

def check_and_print_result(part, solution, time, expected):
    if solution is None:
        return False
    
    if part == 1:
        color = "cyan"
    else:
        color = "magenta"
    failed = False
    print(f'{colored("Part {} (Time: {}ms):".format(part, time), color)} {solution}')
    if expected is not None:
        if expected == str(solution):
            print(f'{colored("Part {} Output {} matches expected {}".format(part, solution, expected), "green")}')
        else:
            failed = True
            print(f'{colored("Part {} Output {} does NOT match expected {}".format(part, solution, expected), "red")}')
    return failed

def check_and_print_results(solution1, time1, expected1, solution2, time2, expected2):
    if solution1 is None and solution2 is None:
        print(colored('No solution implemented', 'red'))
        return True
    failed = False
    failed = failed or check_and_print_result(1, solution1, time1, expected1)
    failed = failed or check_and_print_result(2, solution2, time2, expected2)
    return failed

def test(year, day, solution_file='solution', example=False, part='0'):
    print(colored(f"Testing {year}/{day}", "yellow"))    
    part = int(part)
    if part == 0:
        print("\tTesting all parts")
    else:
        print("\tTesting part", part)
    if (year == None):
        year = get_year()
    if (day == None):
        day = get_day()

    if not os.path.exists(f'{year}/{day}/'):
        print(colored('Directory does not exist:', 'red'))
        print(colored(f'  "{os.getcwd()}/{year}/{day}/"', 'red'))
        return

    if solution_file != 'solution':
        if not os.path.exists(f'{year}/{day}/{solution_file}.py'):
            print(colored('Solution file does not exist:', 'red'))
            print(colored(f'  "{os.getcwd()}/{year}/{day}/{solution_file}.py"', 'red'))
            return
        print(colored(f'(Using {solution_file}.py)', 'red'))

    if not example:

        with open(f'{year}/{day}/input.txt', 'r') as f:
            input = [
                line.replace('\r', '').replace('\n', '') for line in f.readlines()
            ]
        part1_answer, part2_answer, part1_time, part2_time = compute_answers(year, day, input,
                                                    solution_file=solution_file,
                                                    example=example, part=part)
        part1_expected, part2_expected = get_expected_from_from_saved(year, day)
        check_and_print_results(part1_answer, part1_time, part1_expected, part2_answer, part2_time, part2_expected)

    else:
        path = f'{year}/{day}/'
        failed = False

        for filename in os.listdir(path):
            if filename.startswith("test_part1_"):
                if part == 2:
                    continue
                test_part = 1
            elif filename.startswith("test_part2_"):
                if part == 1:
                    continue
                test_part = 2
            else:
                continue

            print(f'{colored("Executing with test input file {}".format(filename), "yellow")}')

            with open(f'{year}/{day}/{filename}', 'r') as f:
                lines = f.readlines()                
                lines.pop(0)
                expected_result = lines.pop(0).strip()
                lines.pop(0)
                                
                input = [line.replace('\r', '').replace('\n', '') for line in lines]
                                
                part1_answer, part2_answer, part1_time, part2_time = compute_answers(year, day, input,
                                                    solution_file=solution_file,
                                                    example=example,
                                                    part = test_part)
                if (check_and_print_results(part1_answer, part1_time, expected_result, part2_answer, part2_time, expected_result)):
                    failed = True
                        
        if failed:
            print(colored('!!!!!TEST FAILED!!!!!', 'red'))
        else:
            print(colored('*****ALL TESTS PASSED*****', 'green'))


    if solution_file != 'solution':
        part1_answer_orig, part2_answer_orig, part1_time_orig, part2_time_orig = compute_answers(year, day, example=example)
        if part1_answer == part1_answer_orig and part2_answer == part2_answer_orig:
            print(colored('Output matches solution.py', 'green'))
        else:
            print(colored('Output does not match solution.py', 'red'))

def record_result(year, day, success, part, solution, time):
    date = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    if success:
        with open(f'{year}/{day}/correct_results.txt', 'a') as f:            
                f.write(f'Puzzle {year}/{day} Part {part} : Result for {date}\n')
                f.write(f'Part{part} Answer: {solution}\n')
                f.write(f'Execution Time: {time}ms\n\n')
                f.close()  
    else:
         with open(f'{year}/{day}/incorrect_results.txt', 'a') as f:                
                f.write(f'Puzzle {year}/{day} Part {part} : Failed Result for {date}\n')
                f.write(f'Part{part} Incorrect Answer: {solution}\n')
                f.write(f'Execution Time: {time}ms\n\n')
                f.close()

def save_results_from_prompt(year, day):
    
    if not os.path.exists(f'{year}/{day}/prompt_results.txt'):
        conf = config.get_config()
        r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}',
                    cookies={'session': conf['session_cookie']})

        soup = BeautifulSoup(r.text, 'html.parser')
        with open(f'{year}/{day}/prompt_results.txt', 'w') as f:
            date = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f'Puzzle {year}/{day} : Correct Answers retrieved from prompt on {date}\n')            
            ps = soup.find_all('p')
            part_id = 1
            for p in ps:            
                line = p.decode_contents()
                if "Your puzzle answer was" in line:
                    f.write(f"Part{part_id}: {line}\n")                    
                    part_id += 1

            f.write("\n\n")     
            f.close()   

answer_re = re.compile(r'<code>(.*?)</code>')
def get_expected_from_from_saved(year, day):
    part1_answer = None
    part2_answer = None
    if os.path.exists(f'{year}/{day}/prompt_results.txt'):
        with open(f'{year}/{day}/prompt_results.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if f"Part1" in line:
                    part1_answer = answer_re.findall(line)[0]
                elif f"Part2" in line:
                    part2_answer = answer_re.findall(line)[0]

    elif os.path.exists(f'{year}/{day}/correct_results.txt'):
        with open(f'{year}/{day}/correct_results.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if f"Part1" in line:
                    part1_answer = line.split(":")[1].strip()
                elif f"Part2" in line:
                    part2_answer = line.split(":")[1].strip()
                    
    return part1_answer, part2_answer
    


def submit(year, day, solution_file='solution', part='0'):
    # TODO: Check for previous failure or success
    print(colored(f"Submit {year}/{day}", "yellow"))    
    part = int(part)
    if (year == None):
        year = get_year()
    if (day == None):
        day = get_day()

    if not os.path.exists(f'{year}/{day}/'):
        print(colored('Directory does not exist:', 'red'))
        print(colored(f'  "{os.getcwd()}/{year}/{day}/"', 'red'))
        return

    if solution_file != 'solution':
        if not os.path.exists(f'{year}/{day}/{solution_file}.py'):
            print(colored('Solution file does not exist:', 'red'))
            print(colored(f'  "{os.getcwd()}/{year}/{day}/{solution_file}.py"', 'red'))
            return
        print(colored(f'(Using {solution_file}.py)', 'red'))

    with open(f'{year}/{day}/input.txt', 'r') as f:
        input = [
            line.replace('\r', '').replace('\n', '') for line in f.readlines()
        ]

    part1_answer, part2_answer, part1_time, part2_time = compute_answers(year, day, input, solution_file=solution_file, part=part)
    part1_expected, part2_expected = get_expected_from_from_saved(year, day)
    check_and_print_results(part1_answer, part1_time, part1_expected, part2_answer, part2_time, part2_expected)
    
    status, response = None, None
    if part2_answer is not None:
        print('Submitting part 2...')
        status, response = submit_answer(year, day, 2, part2_answer)
    elif part1_answer is not None:
        print('Submitting part 1...')
        status, response = submit_answer(year, day, 1, part1_answer)
    else:
        print(colored('No solution implemented', 'red'))
        return

    if status == Status.PASS:
        print(colored('Correct!', 'green'), end=' ')
        if part2_answer is not None:
            print(colored('**', 'yellow'))
            print(f'Day {int(day)} complete!')
            record_result(year, day, True, 2, part2_answer, part2_time)
            save_results_from_prompt(year, day)
            
        elif part1_answer is not None:
            print(colored('*', 'cyan'))
          
            record_result(year, day, True, 1, part1_answer, part1_time)
            conf = config.get_config()
            r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}',
                             cookies={'session': conf['session_cookie']})
            soup = BeautifulSoup(r.text, 'html.parser')
            part2_html = soup.find_all('article', class_='day-desc')[1].decode_contents()

            # remove hyphens from title sections, makes markdown look nicer
            part2_html = re.sub('--- (.*) ---', r'\1', part2_html)

            # also makes markdown look better
            part2_html = part2_html.replace('\n\n', '\n')

            with open(f'{year}/{day}/prompt.md', 'a') as f:
                f.write(custom_markdownify(part2_html))
            print(f'Appended part 2 prompt to {year}/{day}/prompt.md')

    elif status == Status.FAIL:
        print(colored('Incorrect!', 'red'))
        if part2_answer is not None:
            record_result(year, day, False, 2, part2_answer, part2_time)
            
        elif part1_answer is not None:
            print(colored('*', 'cyan'))
            record_result(year, day, False, 1, part1_answer, part1_time)

    elif status == Status.RATE_LIMIT:
        print(colored('Rate limited! Please wait before submitting again.', 'yellow'))

    elif status == Status.COMPLETED:
        save_results_from_prompt(year, day)
        print(colored("You've already completed this question.", 'yellow'))

    elif status == Status.NOT_LOGGED_IN:
        print(colored('Session cookie is invalid or expired.', 'red'))

    elif status == Status.UNKNOWN:
        print(colored('Something went wrong. Please view the output below:', 'red'))
        print(response)


def countdown(year, day):

    now = dt.now().astimezone(pytz.timezone('EST'))

    if now.year != int(year):
        print(colored(f'Date must be from the current year ({now.year}).', 'red'))
        return

    if now > dt(int(year), 12, int(day)).astimezone(pytz.timezone('EST')):
        print(colored('That puzzle has already been unlocked.', 'red'))
        return

    def curses_countdown(stdscr):  # pragma: no cover
        curses.cbreak()
        curses.halfdelay(2)
        curses.use_default_colors()
        if config.get_config()['disable_color']:
            for i in range(1, 4):
                curses.init_pair(i, -1, -1)
        else:
            curses.init_pair(1, curses.COLOR_MAGENTA, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)
        hours, minutes, seconds = get_time_until_unlock(year, day)
        while any((hours, minutes, seconds)):
            stdscr.erase()
            stdscr.addstr('advent-cli', curses.color_pair(1))
            stdscr.addstr(' countdown\n\n')
            stdscr.addstr(f'  {year} day {int(day)} will unlock in:\n', curses.color_pair(2))
            stdscr.addstr(f'  {hours} hours, {minutes} minutes, {seconds} seconds\n\n')
            stdscr.addstr('(press Q or CTRL+C to exit)', curses.color_pair(3))
            stdscr.refresh()
            stdscr.nodelay(1)
            key = stdscr.getch()
            if key == 27 or key == 113:
                raise KeyboardInterrupt
            hours, minutes, seconds = get_time_until_unlock(year, day)

    try:  # pragma: no cover
        curses.wrapper(curses_countdown)
        print(colored('Countdown finished', 'green'))
        time.sleep(1)  # wait an extra second, just in case the timing is slightly early
    except KeyboardInterrupt:  # pragma: no cover
        print(colored('Countdown cancelled', 'red'))
        sys.exit(1)
