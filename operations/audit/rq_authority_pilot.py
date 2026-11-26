"""Audit permissioned historical Racing Queensland captures. No network or model fitting."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import pandas as pd
from monty.integrity import verify_artifacts
from monty.normalization import normal

MEETINGS = (
    ("doomben", "123804", "2025-06-04", "Doomben", "DOOM"),
    ("ipswich", "123809", "2025-06-06", "Ipswich", "IPSW"),
    ("ef", "123816", "2025-06-07", "Eagle Farm", "E FM"),
)
RACE_HEADER = re.compile(r"^\s*(\d{1,2})\s+\d{1,2}:\d{2}[AP]M\s+.+")
ENTRY = re.compile(r"^\s*(\d{1,2})\.\s+(?:\(Em\)\s+)?(.+?)\s{2,}\((\d+)\)\s+(\d+(?:\.\d+)?)\s*(.*)$")
PAGE = re.compile(r"\bPage\s+(\d+)\s+of\s+(\d+)\b")
TITLES = re.compile(r"^(?:(?:mr|mrs|ms|miss)\.?\s+)", re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def role_name(value):
    return normal(TITLES.sub("", value.strip()))


def unique_index(values, key):
    grouped = defaultdict(list)
    for value in values:
        grouped[key(value)].append(value)
    return grouped


def format_name(value):
    # Strip these documented display marks only. Never strip a country suffix.
    return normal(re.sub(r"\s+(?:\(BLKS\)|\*)$", "", value.strip()))


def form_pages(pdf):
    pages = {}
    totals = set()
    for x in (0, 420):
        output = subprocess.check_output(["pdftotext","-layout","-r","72","-x",str(x),
                                          "-y","0","-W","420","-H","595",str(pdf),"-"], text=True)
        for page in output.split("\f"):
            m = PAGE.search(page)
            if not page.strip():
                continue
            if m is None:
                raise ValueError("Unsupported booklet layout")
            number, total = map(int, m.groups())
            if number in pages:
                raise ValueError("Duplicated printed form page")
            pages[number] = page
            totals.add(total)
    if len(totals) != 1 or set(pages) != set(range(1, totals.pop()+1)):
        raise ValueError("Incomplete printed form pages")
    return "\n".join(pages[k] for k in sorted(pages))


def parse_card(text, date, track_code):
    races = defaultdict(list)
    race = None
    edition = pd.Timestamp(date)
    date_header = rf"^\s*0?{edition.day}/0?{edition.month}/{edition.year}\s+Page\s+1\s+of"
    if not re.search(date_header, text[:1000], re.M):
        raise ValueError("Booklet date mismatches meeting")
    date_parts = date.split("-")
    outcome_pattern = (r"^\s*\d+-\d+\s+"+re.escape(track_code)+r"\s+\d+\s+\w+\s+"
                       +rf"0?{int(date_parts[2])}/0?{int(date_parts[1])}/{date_parts[0]}\b")
    current_day_rows = 0
    for line in text.splitlines():
        current_day_rows += bool(re.match(outcome_pattern,line))
        if header := RACE_HEADER.match(line):
            race = int(header[1])
        elif race and (entry := ENTRY.match(line)):
            races[race].append((int(entry[1]), format_name(entry[2]), int(entry[3]),
                                Decimal(entry[4]), "(a" in entry[5].casefold()))
    return races, current_day_rows


def match_runner(row, field, horses):
    pdf = field.get(int(row.TAB_NUMBER), [])
    key = normal(row.SELECTION_NAME)
    if len(pdf) != 1 or pdf[0][1] != key:
        return None,"booklet_saddlecloth_or_name"
    authority = horses.get(key, [])
    if len(authority) != 1:
        return None,"authority_horse_name_missing_or_ambiguous"
    result = authority[0]
    weight = result.findtext("Weight")
    if not weight or Decimal(weight) != pdf[0][3]:
        return None,"as_printed_weight_mismatch"
    horse_id = result.get("Id")
    if not horse_id or not horse_id.isdecimal():
        return None,"authority_horse_id_missing"
    matched = dict(
        book_barrier_equal=pdf[0][2] == row.barrier,
        claim_mark_in_booklet=pdf[0][4], horse_id=horse_id)
    for role in ("Jockey","Trainer"):
        entry = result.find(role)
        identifier = entry.get("Id") if entry is not None else None
        label = entry.findtext("FullName","") if entry is not None else ""
        matched[role.lower()+"_id_present"] = bool(identifier and identifier.isdecimal())
        matched[role.lower()+"_verified"] = bool(identifier and identifier.isdecimal() and
                                                label and role_name(label) == getattr(row,role.lower()))
        if matched[role.lower()+"_verified"]:
            matched[role.lower()+"_id"] = identifier
    return matched,None


def audit(directory, archive, private_output=None):
    captures = json.loads((directory/"receipts-private.json").read_text())
    successful = {}
    report_attempts = []
    for r in captures:
        public = {k:v for k,v in r.items() if k in (
            "file","url","sha256","bytes","requested_at","retrieved_at","status","error")}
        report_attempts.append(public)
        if r.get("status") == 200 and r.get("sha256"):
            successful[r["file"]] = r
    for file,r in successful.items():
        if Path(file).name != file or digest((directory/file).read_bytes()) != r["sha256"]:
            raise ValueError("Source capture digest mismatch")
    def xml(file):
        if file not in successful:
            raise ValueError("Missing source capture")
        data = (directory/file).read_bytes()
        if b"<!DOCTYPE" in data.upper():
            raise ValueError("Unexpected DTD")
        return ET.fromstring(data)

    meetings = xml("meetings.xml")
    if meetings.tag != "Meetings":
        raise ValueError("Unexpected meeting response")
    meeting_index = unique_index(meetings,lambda m:m.get("Id"))
    frozen_count=verify_artifacts(archive.parent.parent)
    rows=pd.read_csv(archive,dtype={"WIN_MARKET_ID":str,"SELECTION_ID":str})
    totals=Counter()
    exclusions=Counter()
    published=[]
    private_links=[]
    linked_runner_keys=defaultdict(set)
    reverse_horse_ids=defaultdict(set)
    linked_exchange_ids=defaultdict(set)
    for stem,mid,date,track,track_code in MEETINGS:
        meeting = meeting_index.get(mid,[])
        if (len(meeting)!=1 or meeting[0].findtext("TrackName")!=track or
                meeting[0].findtext("MeetingDate")!=date or meeting[0].findtext("IsBarrierTrial")!="false"):
            raise ValueError("Meeting identity mismatch")
        cards,current_outcomes=parse_card(form_pages(directory/f"{stem}-fra.pdf"),date,track_code)
        totals["current_day_form_outcome_rows"]+=current_outcomes
        race_xml=xml(f"{stem}-races.xml")
        if race_xml.tag!="Races":
            raise ValueError("No race records")
        totals["race_ids_returned"]+=len(race_xml)
        indexed=unique_index(race_xml,lambda race:race.findtext("RaceNumber"))
        for number in (1,2,3):
            if len(indexed.get(str(number),[]))!=1:
                raise ValueError("Ambiguous numbered race")
            race=indexed[str(number)][0]
            horses=xml(f"{stem}-horses-{number}.xml")
            if horses.tag!="Horses":
                raise ValueError("No horse records")
            if any(h.get("Id") is None for h in horses):
                raise ValueError("Authority horse ID absent")
            if len({h.get("Id") for h in horses}) != len(horses):
                raise ValueError("Authority ID duplicated within race")
            source=successful[f"{stem}-horses-{number}.xml"]
            if not source["url"].endswith(f"?raceId={race.attrib['Id']}"):
                raise ValueError("Race/horse response mismatch")
            total=Counter(asmx_rows=len(horses))
            total["asmx_trainer_ids_present"]=sum(bool(h.find("Trainer") is not None and
                h.find("Trainer").get("Id","").isdecimal()) for h in horses)
            total["asmx_jockey_ids_present"]=sum(bool(h.find("Jockey") is not None and
                h.find("Jockey").get("Id","").isdecimal()) for h in horses)
            candidates=rows[rows.date.eq(date)&rows.TRACK.eq(track)&rows.RACE_NO.eq(number)]
            total["checkpoint_runners"]=len(candidates)
            metres=re.fullmatch(r"(\d+) metres",race.findtext("Distance",""))
            if (not metres or not candidates.DISTANCE.eq(int(metres[1])).all() or
                    candidates.WIN_MARKET_ID.nunique()!=1 or candidates.TAB_NUMBER.duplicated().any()):
                raise ValueError("Archive race identity or number ambiguity")
            pdf=unique_index(cards[number],lambda entry:entry[0])
            authority=unique_index(horses,lambda h:normal(h.findtext("HorseName","")))
            for row in candidates.itertuples():
                matched,reason=match_runner(row,pdf,authority)
                if reason:
                    exclusions[reason]+=1
                    continue
                key=(row.WIN_MARKET_ID,row.SELECTION_ID)
                linked_runner_keys[key].add(matched["horse_id"])
                linked_exchange_ids[matched["horse_id"]].add(row.SELECTION_ID)
                reverse_horse_ids[row.SELECTION_ID].add(matched["horse_id"])
                private_links.append(dict(date=date, meeting=track, race=number, saddlecloth=int(row.TAB_NUMBER),
                    rq_meeting_id=mid, rq_race_id=race.attrib["Id"], betfair_market_id=row.WIN_MARKET_ID,
                    betfair_runner_id=row.SELECTION_ID, rq_horse_id=matched["horse_id"],
                    rq_trainer_id=matched.get("trainer_id"), rq_jockey_id=matched.get("jockey_id"),
                    provider_sha256=source["sha256"], booklet_sha256=successful[f"{stem}-fra.pdf"]["sha256"],
                    received_at=source["retrieved_at"], historical_publication_at=None,
                    verified_asof=False, identity_scope="same_event_only"))
                total["race_scoped_horse_ids_linked"]+=1
                for label in ("book_barrier_equal","claim_mark_in_booklet","jockey_id_present",
                              "trainer_id_present","jockey_verified","trainer_verified"):
                    total[label]+=matched[label]
            totals.update(total)
            published.append(dict(date=date,meeting=track,number=number,
                                  rq_meeting_id=mid,rq_race_id=race.attrib["Id"],**total))
    if any(len(v)!=1 for v in (*linked_runner_keys.values(),*reverse_horse_ids.values())):
        raise ValueError("Conflicting same-event identity")
    if private_output is not None:
        fd = os.open(private_output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd,"w") as file:
            json.dump(private_links,file,indent=2,allow_nan=False)
            file.write("\n")
    bad=xml("kilcoy-races.xml")
    totals["calendar_meetings"]=len(meetings)
    totals["calendar_nontrial_meetings"]=sum(m.findtext("IsBarrierTrial")=="false" for m in meetings)
    return dict(schema="monty.rq_authority_pilot.v1",capture_attempts=report_attempts,
                reference_archive_sha256=digest(archive.read_bytes()),frozen_v6_hashes=frozen_count,
                publication_time_status="Historical as-of evidence unavailable; authority aggregates are retrospective.",
                admissible_asof_runner_rows=0, official_finish_joins=0, named_fixed_win_joins=0,
                races=published, totals=dict(totals), exclusions=dict(exclusions),
                distinct_rq_horses=len(linked_exchange_ids),
                distinct_verified_rq_trainers=len({r["rq_trainer_id"] for r in private_links if r["rq_trainer_id"]}),
                distinct_verified_rq_jockeys=len({r["rq_jockey_id"] for r in private_links if r["rq_jockey_id"]}),
                rows_with_both_verified_roles=sum(bool(r["rq_trainer_id"] and r["rq_jockey_id"])
                                                   for r in private_links),
                rq_horses_with_multiple_exchange_ids=sum(len(v)>1 for v in linked_exchange_ids.values()),
                kilcoy_status="service_application_error" if bad.tag=="Error" else "not_used_in_sample")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures",type=Path,required=True)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--private-output",type=Path,help="Optional private local ID crosswalk")
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    a.output.write_text(json.dumps(audit(a.captures,a.archive,a.private_output),indent=2,allow_nan=False)+"\n")
