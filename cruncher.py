#!/usr/bin/env python3
"""Process system call status in Unikraft from spreadsheet and
system call support in different applications from JSON file.

JSON file is outputted by system call analysis tool.
"""

import os
import sys
import json
import argparse
import xlrd


# Folder storing application JSON files from syscall analysis tool:
# one JSON file per-application
APPLICATION_JSON_FOLDER = 'to_aggregate'

# Excel file that contains the syscall implementation
# TODO: Use Google DOC API.
SHEET_FILENAME = 'Unikraft - Syscall Status.xls'

# Columns to consider in the excel file
NB_COLS = 3

INDEX_RAX = 0 #syscall number (col: 0)
INDEX_NAME = 1 #syscall name   (col: 1)
INDEX_STATUS = 2 #syscall status (col: 2)

# Keys in JSON files
STATIC_DATA = "static_data"
DYNAMIC_DATA = "dynamic_data"
SYSCALLS_DATA = "system_calls"


# Applications dictionary, indexed by application name
# Each item in the dictionary is another dictionary with list of system calls
# in the various states. Each inner dictionary uses the status as key: "OKAY",
# "ABSENT", "NOT_IMPL", "INCOMPLETE", "REG_MISS", "STUBBED", "BROKEN",
# "IN_PROGRESS", "PLANNED".
apps = {}

# System calls dictionary, indexed by syscall name
# Each item in the dictionary is another dictionary with the fields:
#   "id": system call id (number)
#   "name": system call name (again - also used as dictionary key)
#   "status": system call status
#   "apps" list of application names
syscalls = {}

# Undefined system calls dictionary, indexed by syscall name
# System calls that are undefined in the current system call list.
# This is the case with 32bit system calls - resulting from the investigation,
# but not as part of the system call status document.
# Each item in the dictionary is another dictionary with the fields:
#   "name": system call name (again - also used as dictionary key)
#   "apps" list of application names
undefined_syscalls = {}


def process_application_json(app_name, json_data):
    """Fill apps, syscalls and undefined_syscalls dictionaries.

    Extract syscall related information from each application JSON file.
    Application name and application JSON data are passed as arguments.
    """

    # Extract all system calls in the JSON file in local_set.
    local_set = set()

    # First parse static data.
    if STATIC_DATA in json_data:
        static_data = json_data[STATIC_DATA][SYSCALLS_DATA]
        for symbol in static_data:
            local_set.add(symbol)

    # Then parse dynamic data.
    if DYNAMIC_DATA in json_data:
        dynamic_data = json_data[DYNAMIC_DATA][SYSCALLS_DATA]
        for symbol in dynamic_data:
            local_set.add(symbol)

    # Construct application dictionary (apps).
    apps[app_name] = {
        "OKAY": [],
        "ABSENT": [],
        "NOT_IMPL": [],
        "INCOMPLETE": [],
        "REG_MISS": [],
        "STUBBED": [],
        "BROKEN": [],
        "IN_PROGRESS": [],
        "PLANNED": []
        }
    for symbol in local_set:
        if symbol in syscalls.keys():
            status = syscalls[symbol]['status']
        else:
            status = "ABSENT"
        apps[app_name][status].append(symbol)

    # Update syscall dictionary with application list.
    # Construct undedefine_syscalls dictionary.
    for symbol in local_set:
        found = False
        for s in syscalls:
            if s == symbol:
                found = True
                break
        if found:
            syscalls[symbol]['apps'].append(app_name)
        else:
            if not symbol in undefined_syscalls:
                undefined_syscalls[symbol] = {
                    'name': symbol,
                    'apps': []
                    }
            undefined_syscalls[symbol]['apps'].append(app_name)


def walk_application_json_folder(path):
    """Walk folder with application JSON files.

    Read each per-application JSON file and process it.
    """

    for subdir, _, files in os.walk(path):
        for file in sorted(files):
            filepath = subdir + os.sep + file

            if filepath.endswith(".json"):
                with open(filepath) as json_file:
                    json_data = json.load(json_file)
                    process_application_json(file[:-5], json_data)


def process_syscall_spreadsheet(filename):
    """Interpret syscall status spreadsheet (.xls).

    Only extract the first three columns (cols: [0-2]).
    Columns are:
      * column 0 (INDEX_RAX): system call id (number)
      * column 1 (INDEX_NAME): system call name
      * column 2 (INDEX_STATUS): system call status

    Return value is data_sheet, a list of three lists, one for each column.
    """

    data_sheet = list()

    book = xlrd.open_workbook(filename)
    worksheet = book.sheet_by_index(0)

    # Init the data_sheet with 3 sublists
    for _ in range(NB_COLS):
        data_sheet.append(list())

    # Populate data_sheet with cell values (COLS: 0, 1, 2)
    for row in range(1, worksheet.nrows):
        try:
            data_sheet[INDEX_RAX].append(int(
                worksheet.cell_value(row, INDEX_RAX)))
        except ValueError:
            # This is not a number, change it to -1
            data_sheet[INDEX_RAX].append(-1)

        data_sheet[INDEX_NAME].append(
            worksheet.cell_value(row, INDEX_NAME))

        status_str = worksheet.cell_value(row, INDEX_STATUS)
        if len(status_str) == 0:
            status_str = 'NOT_IMPL'
        elif 'incomplete' in status_str:
            status_str = "INCOMPLETE"
        elif 'registration missing' in status_str:
            status_str = "REG_MISS"
        elif 'stubbed' in status_str:
            status_str = "STUBBED"
        elif 'planned' in status_str:
            status_str = "PLANNED"
        elif 'progress' in status_str:
            status_str = "IN_PROGRESS"
        elif 'broken' in status_str:
            status_str = "BROKEN"
        elif 'okay' in status_str:
            status_str = "OKAY"
        data_sheet[INDEX_STATUS].append(status_str)

    return data_sheet


def print_apps():
    """Print apps dictionary as comma-separated values (CSV).
    """
    print("{},{},{},{},{},{},{},{},{},{},{}".format(
        "app", "total", "okay", "not_impl", "reg_miss", "incomplete",
        "stubbed", "planned", "broken", "in_progress", "absent"))
    for a in apps:
        okay = len(apps[a]['OKAY'])
        not_impl = len(apps[a]["NOT_IMPL"])
        incomplete = len(apps[a]["INCOMPLETE"])
        reg_miss = len(apps[a]["REG_MISS"])
        stubbed = len(apps[a]["STUBBED"])
        planned = len(apps[a]["PLANNED"])
        in_progress = len(apps[a]["IN_PROGRESS"])
        broken = len(apps[a]["BROKEN"])
        absent = len(apps[a]["ABSENT"])
        total = okay + not_impl + incomplete + reg_miss + stubbed + planned + in_progress + broken
        print("{},{},{},{},{},{},{},{},{},{},{}".format(
            a, total, okay, not_impl, reg_miss, incomplete,
            stubbed, planned, broken, in_progress, absent))


def print_syscalls():
    """Print system calls from syscalls and undefined_syscalls dictionary
    as comma-separated values (CSV).
    """
    print("{},{},{}".format("syscall", "status", "num_apps"))
    for s in syscalls:
        print("{},{},{}".format(s, syscalls[s]['status'], len(syscalls[s]['apps'])))
    for s in undefined_syscalls:
        print("{},{},{}".format(s, 'ABSENT', len(undefined_syscalls[s]['apps'])))


def main():
    """Process system call status spreadsheet (SHEET_FILENAME) and
    application JSON folder (APPLICATION_JSON_FOLDER).
    Print application and / or system call statistics depending on arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--apps', action='store_true',
                        help='Print system call support in applications')
    parser.add_argument('-s', '--syscalls', action='store_true',
                        help='Print system call usage / popularity in apps')
    args = parser.parse_args()

    data_sheet = process_syscall_spreadsheet(SHEET_FILENAME)
    ids = data_sheet[0]
    names = data_sheet[1]
    stats = data_sheet[2]

    for i in range(len(ids)):
        syscalls[names[i]] = {
            "id": ids[i],
            "name": names[i],
            "status": stats[i],
            "apps": []
            }
    # Read folder with application JSON files and aggregate the data.
    walk_application_json_folder(APPLICATION_JSON_FOLDER)

    if args.apps:
        print_apps()
    if args.syscalls:
        print_syscalls()


if __name__ == "__main__":
    sys.exit(main())
