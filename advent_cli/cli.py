import argparse
from datetime import datetime as dt

from . import commands
from ._version import __version__
from .utils import CustomHelpFormatter


def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'advent-cli {__version__}'
    )
    command_subparsers = parser.add_subparsers(
        dest='command', description='use advent {subcommand} --help for arguments'
    )
    parser_get = command_subparsers.add_parser(
        'get',
        help='download prompt and input, generate solution template',
        formatter_class=CustomHelpFormatter
    )
    parser_get.add_argument(
        '-d', '--date',
        dest='date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_stats = command_subparsers.add_parser(
        'stats',
        help='show personal stats or private leaderboards',
        formatter_class=CustomHelpFormatter
    )
    parser_stats.add_argument(
        'year',
        nargs='?',
        default=dt.now().year,
        help='year to show stats for, defaults to current year'
    )
    parser_stats.add_argument(
        '-p', '--private',
        dest='show_private',
        action='store_true',
        help='show private leaderboard(s)'
    )
    parser_test = command_subparsers.add_parser(
        'test',
        help='run solution and output answers without submitting',
        formatter_class=CustomHelpFormatter
    )
    parser_test.add_argument(
        '-d', '--date',
        dest='date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_test.add_argument(
        '-e', '--example',
        dest='run_example',
        action='store_true',
        help='use example_input.txt for input'
    )
    parser_test.add_argument(
        '-p', '--part',
        dest='puzzle_part',
        default='0',
        help='only run a specific part (1 or 2)',        
    )
    parser_test.add_argument(
        '-f', '--solution-file',
        dest='solution_file',
        default='solution',
        help='solution file to run instead of solution.py\n'
             '(e.g. "solution2" for solution2.py)'
    )
    parser_submit = command_subparsers.add_parser(
        'submit',
        help='run solution and submit answers',
        formatter_class=CustomHelpFormatter
    )
    parser_submit.add_argument(
        '-d', '--date',
        dest='date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_submit.add_argument(
        '-f', '--solution-file',
        dest='solution_file',
        default='solution',
        help='solution file to run instead of solution.py\n'
             '(e.g. "solution2" for solution2.py)\n'
             '*only works if answers not yet submitted*'
    )
    parser_submit.add_argument(
        '-p', '--part',
        dest='puzzle_part',
        default='0',
        help='only run a specific part (1 or 2)'
    )        
    parser_countdown = command_subparsers.add_parser(
        'countdown',
        help='display countdown to puzzle unlock',
        formatter_class=CustomHelpFormatter
    )
    parser_countdown.add_argument(
        'date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_year = command_subparsers.add_parser(
        'year',
        help='set the current year',
        formatter_class=CustomHelpFormatter
    )
    parser_year.add_argument(
        'year',
        help='the year YYYY format (e.g. "2021")'
    )
    parser_day = command_subparsers.add_parser(
        'day',
        help='set the current day',
        formatter_class=CustomHelpFormatter
    )
    parser_day.add_argument(
        'day',
        help='the day in DD format (e.g. "03")'
    )
    args = parser.parse_args()
    print()
    if args.command == 'get':
        
        if args.date:
            year, day = args.date.split('/')
            commands.get(year, day)
        else:
            commands.get(None, None)

    elif args.command == 'stats':
        if args.show_private:
            commands.private_leaderboard_stats(args.year)
        else:
            commands.stats(args.year)

    elif args.command == 'test':
        if args.date:
            year, day = args.date.split('/')
            commands.test(year, day, solution_file=args.solution_file, example=args.run_example, part=args.puzzle_part)
        else:
            commands.test(None, None, solution_file=args.solution_file, example=args.run_example, part=args.puzzle_part)

    elif args.command == 'submit':
        if args.date:
            year, day = args.date.split('/')
            commands.submit(year, day, solution_file=args.solution_file, part=args.puzzle_part)
        else:
            commands.submit(None, None, solution_file=args.solution_file, part=args.puzzle_part)

    elif args.command == 'countdown':
        year, day = args.date.split('/')
        commands.countdown(year, day)
    elif args.command == 'year':
        commands.set_year(args.year)
    elif args.command == 'day':
        commands.set_day(args.day)
    print()