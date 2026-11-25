"""Count-only audit of the pinned PuntersEdge CC BY 4.0 research sample."""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

PIN = 'c07364381341bf7d1f1c6f29fd40fd0b984d87d95507b1ad75c336e575a7ee60'


def inventory(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != PIN:
        raise ValueError('PuntersEdge sample hash mismatch')
    races = defaultdict(set)
    books = defaultdict(dict)
    bad = set()
    exclusions, status, references = Counter(), Counter(), Counter()
    total = runners = 0
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as source:
        for row in csv.DictReader(source):
            total += 1
            if (row['country'], row['category']) != ('AU', 'horse'):
                continue
            runners += 1
            key = row['race_id'], row['bookmaker_key']
            runner = row['runner_number']
            price, age = float(row['close_win_price']), int(row['close_secs_to_jump'])
            races[key[0]].add(runner)
            if runner in books[key]:
                exclusions['duplicate_saddlecloth_rows'] += 1
                bad.add(key)
            if not runner or not math.isfinite(price) or price <= 1 or not 0 <= age <= 300:
                exclusions['invalid_or_outside_pre_advertised_jump_rows'] += 1
                bad.add(key)
            books[key][runner] = price, age
            status[row['result_status']] += 1
            references[row['horse_ref'].partition(':')[0] or '(blank)'] += 1
    summary = defaultdict(Counter)
    for key, field in books.items():
        race, operator = key
        counts = summary[operator]
        counts['race_vectors'] += 1
        if key in bad:
            counts['quarantined_vectors'] += 1
            continue
        if set(field) == races[race]:
            counts['provider_union_complete'] += 1
            counts['same_integer_capture_offset'] += len({age for _, age in field.values()}) == 1
            counts['underround'] += math.fsum(1/price for price, _ in field.values()) < 1
    return dict(source='PuntersEdge Australian racing closing-line sample (puntersedge.online)',
                licence='CC BY 4.0', version='2026-09.3', sha256=PIN,
                total_rows=total, au_thoroughbred_rows=runners, au_thoroughbred_races=len(races),
                books=summary, excluded_rows=exclusions, result_status_rows=status,
                horse_ref_namespaces=references,
                limitation='Provider-union completeness and integer offsets do not prove independent field, registered identity or simultaneous executable prices.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_gz', type=Path)
    args = parser.parse_args()
    print(json.dumps(inventory(args.csv_gz), indent=2))
