"""Validate a locally saved Racing Queensland sectional export for research."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re


def inventory(raw):
    races = {}
    current_date = None
    current_key = None
    missing_segments = 0
    header = re.compile(r'Date,RaceNumber,(\d{2}/\d{2}/\d{4}) .*?;([^;]+);.*;[^;]+;([A-Za-z0-9_]+_TRACK)$')
    for line in raw.decode('utf-8-sig').splitlines():
        if not line.strip():
            continue
        if line.startswith('Date,RaceNumber,'):
            match = header.fullmatch(line)
            if not match:
                raise ValueError('Invalid race header')
            current_date = datetime.strptime(match[1], '%d/%m/%Y').date().isoformat()
            current_key = None
            continue
        day, number, payload = line.split(',', 2)
        day = datetime.strptime(day, '%d/%m/%Y').date().isoformat()
        if day != current_date or not number.isdecimal() or int(number) < 1:
            raise ValueError('Wrong sectional race identity')
        key = day, int(number)
        if current_key is None:
            if key in races:
                raise ValueError('Repeated sectional race')
            current_key = key
            races[key] = {}
        if current_key != key:
            raise ValueError('Missing new race header')
        horse, source_number, *parts = payload.split(';')
        if not horse.strip() or not source_number.isdecimal() or not parts or len(parts) % 3:
            raise ValueError('Invalid sectional runner')
        horse = ' '.join(horse.casefold().split())
        if horse in races[key]:
            raise ValueError('Duplicate sectional runner')
        previous = 0
        usable = 0
        for offset in range(0, len(parts), 3):
            metre, measure, time = parts[offset:offset+3]
            if not metre.isdecimal() or int(metre) <= previous:
                raise ValueError('Invalid sectional distance sequence')
            value = float(measure)
            if not (math.isfinite(value) and value >= 0 and re.fullmatch(r'\d\d:\d\d:\d\d\.\d+', time)):
                raise ValueError('Invalid sectional measurement')
            zero_time = not any(digit in '123456789' for digit in time)
            if (value == 0) != zero_time:
                raise ValueError('Inconsistent missing sectional measurement')
            if zero_time:
                missing_segments += 1
            else:
                usable += 1
            previous = int(metre)
        races[key][horse] = usable
    if not races:
        raise ValueError('No sectional races')
    runners = [count for race in races.values() for count in race.values()]
    return dict(sha256=hashlib.sha256(raw).hexdigest(), dates=sorted({key[0] for key in races}),
                races=len(races), runner_rows=len(runners), segments=sum(runners),
                missing_segments=missing_segments,
                runner_rows_without_measurements=runners.count(0),
                segments_by_runner=dict(sorted(Counter(runners).items())),
                used_in_model=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps({str(path): inventory(path.read_bytes()) for path in args.files}, indent=2))


if __name__ == '__main__':
    main()
