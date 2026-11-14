#!/usr/bin/env python3
"""
Compute the hub series points for a season from its race results
(<YEAR>/series.json and the race files it lists) and write <YEAR>/points.json.

Points already published in points.json are never changed unless --force is
given. Use render_pdf.py to create the pdf from points.json.
"""

import os
import sys
import json
import argparse
import datetime
import subprocess

import ranking

SCHEMA_VERSION = 1

MAX_POINTS = 1000
DEFAULT_MIN_N = 5

CLASSES = ["C1M", "K1M", "C1W", "K1W"]

COMBINED = {"women": ["C1W", "K1W"],
            "men": ["C1M", "K1M"]}

# Edit distance below which two names in the same class are reported as
# possible duplicates
DUPLICATE_DISTANCE = 4

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

POINTS_FILE = "points.json"

# ---- Names ----
#
# A person is matched on surname and first name, ignoring upper/lower case and
# spaces at either end. The spelling of the first appearance in the season is
# the one shown.

def person_key(entry):

    return (entry["surname"].strip().lower(), entry["firstname"].strip().lower())

def display_name_parts(entry):
    """ e.g. {"firstname": "Chris", "surname": "TUBB"} """

    firstname = entry["firstname"].strip()
    return {"firstname": firstname[0].upper() + firstname[1:],
            "surname": entry["surname"].strip().upper()}

def entry_name(entry):
    """ Display name, e.g. "Chris TUBB" """

    return f"{entry['firstname']} {entry['surname']}"

def min_edit_distance(word1, word2):
    """ Edit distance with a substitution counting as 2 """

    prev = list(range(len(word2) + 1))
    for m in range(1, len(word1) + 1):
        cur = [m] + [0] * len(word2)
        for n in range(1, len(word2) + 1):
            cur[n] = min(prev[n] + 1, cur[n-1] + 1, prev[n-1] + (2 if word1[m-1] != word2[n-1] else 0))
        prev = cur
    return prev[-1]

def find_possible_duplicates(people):
    """ Pairs of people whose names are close enough to be spelling variants """

    pairs = []
    for n, first in enumerate(people):
        for second in people[n+1:]:
            if min_edit_distance(first["surname"] + first["firstname"],
                                 second["surname"] + second["firstname"]) < DUPLICATE_DISTANCE:
                pairs.append((first, second))
    return pairs

# ---- Points ----

def round_half_up(value):

    return int(value + 0.5)

def get_points(rank, N, mult):

    if rank < 1:
        return 0

    return round_half_up(mult * (MAX_POINTS - (rank-1) * (MAX_POINTS / N)))

def get_ranks(ordered_points):
    """ Rank of each entry in an already sorted (highest first) list of points,
    equal points share a rank and the following rank is skipped: 1, 2, 2, 4 """

    ranks = []
    for pos, points in enumerate(ordered_points):
        if pos > 0 and points == ordered_points[pos-1]:
            ranks.append(ranks[-1])
        else:
            ranks.append(pos+1)
    return ranks

def order_by_points(keys, points, published_standings):
    """ Indexes of people (keys from person_key), highest points first. Equal
    points keep the order of the published standings, so a published tie order
    never changes, and anyone not published is listed alphabetically """

    published_pos = {person_key(entry): pos for pos, entry in enumerate(published_standings)}

    return sorted(range(len(keys)),
                  key=lambda ind: (-points[ind], published_pos.get(keys[ind], len(published_pos)), keys[ind]))

def format_dates(start_date, end_date):
    """ e.g. "26 - 27 August 2023", "31 August 2025" or "30 August - 1 September 2025" """

    start = datetime.date.fromisoformat(start_date)
    end = datetime.date.fromisoformat(end_date)

    assert start.year == end.year and end.month - start.month in (0, 1), \
        f"Race dates {start_date} to {end_date} not supported"

    if start.month != end.month:
        return f"{start.day} {start:%B} - {end.day} {end:%B %Y}"

    if start.day == end.day:
        return f"{start.day} {start:%B %Y}"

    return f"{start.day} - {end.day} {start:%B %Y}"

def get_git_commit():

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_DIR,
                                         text=True, stderr=subprocess.DEVNULL).strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_DIR,
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    # Uncommitted changes mean the commit alone doesn't reproduce the results
    return commit + ("-dirty" if status else "")

def apply_overrides(ranked, overrides):
    """ Replace the rank of the paddlers named in the points overrides for one
    race and class, returning the ranked list re-sorted by rank. A place of
    None leaves the paddler out of the points (and out of N) """

    ranked = list(ranked)
    for override in overrides:
        for place in override["places"]:
            matches = [n for n, (entry, _) in enumerate(ranked) if person_key(entry) == person_key(place)]
            assert len(matches) == 1, \
                f"Points override for '{place['firstname']} {place['surname']}' in {override['race']} " \
                f"{override['class']} matches {len(matches)} ranked paddlers"
            ranked[matches[0]] = (ranked[matches[0]][0], place["place"])

    ranked = [(entry, rank) for entry, rank in ranked if rank is not None]
    return sorted(ranked, key=lambda entry_rank: entry_rank[1])

def load_race_rankings(series_dir, race_info, overrides):
    """ The ranked [(entry, rank)] for each class of a race, None if it has no results yet """

    if race_info["results"] is None:
        return None

    with open(os.path.join(series_dir, race_info["results"]), "rt") as fed:
        race = json.load(fed)

    rankings = {}
    for cl in CLASSES:
        ranked, _ = ranking.rank_class(race["format"], race["classes"].get(cl, []))

        cl_overrides = [o for o in overrides if o["race"] == race_info["id"] and o["class"] == cl]
        if cl_overrides:
            ranked = apply_overrides(ranked, cl_overrides)

        rankings[cl] = ranked

    return rankings

def compute(series_file, min_n=DEFAULT_MIN_N, published=None):
    """ Compute the hub series points for a season (<YEAR>/series.json),
    returning everything needed to publish the results as a dict. published is
    the points already published for the season, if any, and only sets the
    order of tied paddlers """

    published = published or {}

    with open(series_file, "rt") as fed:
        series_info = json.load(fed)

    series_dir = os.path.dirname(os.path.abspath(series_file))
    overrides = series_info.get("points_overrides", [])

    race_mult = {info["id"]: info["scaling"] for info in series_info["races"]}
    for race_id, mult in race_mult.items():
        assert mult == 1.0, f"Only expect 1.0 scaling for all races ('{race_id}' is {mult})!"

    race_rankings = {info["id"]: load_race_rankings(series_dir, info, overrides) for info in series_info["races"]}
    complete_races = [info["id"] for info in series_info["races"] if race_rankings[info["id"]] is not None]

    for override in overrides:
        assert override["race"] in complete_races, f"Points override for unknown race '{override['race']}'"

    def race_points(key, cl, race):
        """ Points from the first matching paddler in the race (only matters for duplicated names) """

        ranked = race_rankings[race][cl]
        for entry, rank in ranked:
            if person_key(entry) == key:
                return get_points(rank, max(min_n, len(ranked)), race_mult[race])
        return 0

    results = {
        "schema_version": SCHEMA_VERSION,
        "series": {"name": series_info["name"],
                   "year": str(series_info["year"])},
        "generated": {"source": os.path.relpath(os.path.abspath(series_file), REPO_DIR),
                      "git_commit": get_git_commit(),
                      "date": datetime.datetime.now().isoformat(timespec="seconds")},
        "rules": {"max_points": MAX_POINTS,
                  "min_n": min_n,
                  "race_points": "round_half_up(scaling * (max_points - (place - 1) * max_points / max(min_n, field_size)))",
                  "combined": "round_half_up((C1 total + K1 total) / 2)"},
        "races": [],
        "classes": {},
        "combined": {},
        "points_overrides": overrides,
        "possible_duplicates": {},
    }

    for info in series_info["races"]:
        results["races"].append({
            "id": info["id"],
            "short": info["short"],
            "name": info["name"],
            "start_date": info["start_date"],
            "end_date": info["end_date"],
            "dates_display": format_dates(info["start_date"], info["end_date"]),
            "status": "completed" if info["id"] in complete_races else "pending",
            "scaling": info["scaling"],
        })

    # Everyone in each class, in order of first appearance: race order, then rank order
    class_people = {}
    class_totals = {}
    for cl in CLASSES:

        people = {}
        for race in complete_races:
            for entry, _ in race_rankings[race][cl]:
                people.setdefault(person_key(entry), display_name_parts(entry))
        class_people[cl] = people

        keys = list(people)
        points = [[race_points(key, cl, race) for race in complete_races] for key in keys]
        totals = [sum(row) for row in points]
        class_totals[cl] = dict(zip(keys, totals))

        order = order_by_points(keys, totals, published.get("classes", {}).get(cl, {}).get("standings", []))
        standings = []
        for rank, ind in zip(get_ranks([totals[ind] for ind in order]), order):
            entry = {"rank": rank}
            entry.update(people[keys[ind]])
            entry["points"] = dict(zip(complete_races, points[ind]))
            entry["total"] = totals[ind]
            standings.append(entry)

        races = {}
        for race in complete_races:
            ranked = race_rankings[race][cl]

            placings = []
            for entry, rank in ranked:
                placing = {"place": rank}
                placing.update(display_name_parts(entry))
                placing["points"] = race_points(person_key(entry), cl, race)
                placings.append(placing)

            races[race] = {"field_size": len(ranked), "n_used": max(min_n, len(ranked)), "placings": placings}

        results["classes"][cl] = {"standings": standings, "races": races}

    for group, classes in COMBINED.items():
        results["combined"][group] = get_combined(classes, class_people, class_totals,
                                                  published.get("combined", {}).get(group, {}).get("standings", []))

    for cl in CLASSES:
        results["possible_duplicates"][cl] = [
            [first, second] for first, second in find_possible_duplicates(list(class_people[cl].values()))]

    return results

def get_combined(classes, class_people, class_totals, published_standings):
    """ Combined standings: the average of the C1 and K1 totals, a class not raced counts as 0 """

    people = {}
    for cl in classes:
        for key, name in class_people[cl].items():
            people.setdefault(key, name)

    keys = list(people)
    per_class = [[class_totals[cl].get(key, 0) for cl in classes] for key in keys]
    avgs = [round_half_up(sum(row) / len(classes)) for row in per_class]

    order = order_by_points(keys, avgs, published_standings)

    standings = []
    for rank, ind in zip(get_ranks([avgs[ind] for ind in order]), order):
        entry = {"rank": rank}
        entry.update(people[keys[ind]])
        for cl, total in zip(classes, per_class[ind]):
            # "c1"/"k1" from "C1W"/"K1M" etc...
            entry[cl[:2].lower()] = total
        entry["avg"] = avgs[ind]
        standings.append(entry)

    return {"classes": classes, "standings": standings}

# ---- Command line ----

def print_standings(results):

    races = [race for race in results["races"] if race["status"] == "completed"]

    for cl, class_results in results["classes"].items():

        print("=====")
        print(cl)
        print("")
        print(" " * 34 + "".join(f"{title:5s} " for title in [race["short"] for race in races] + ["Total"]))

        for entry in class_results["standings"]:
            print(f"{entry['rank']:3d} {entry_name(entry):30s}"
                  + "".join(f"{entry['points'][race['id']]:5d} " for race in races)
                  + f"{entry['total']:4d}")

        print("")

def print_possible_duplicates(results):

    for cl, pairs in results["possible_duplicates"].items():
        if pairs:
            print(f"Possible duplicate names in class '{cl}'")
            for first, second in pairs:
                print(f"'{entry_name(first)}' == '{entry_name(second)}' ?")

def print_overrides(results):

    for override in results["points_overrides"]:
        places = ", ".join(f"{entry_name(place)} " + ("left out" if place["place"] is None else str(place["place"]))
                           for place in override["places"])
        print(f"Points override for {override['race']} {override['class']}: {places} ({override['reason']})")

def published_points_changes(published, results):
    """ List any race points in the published results that would change """

    changes = []
    for cl, class_results in published["classes"].items():

        new_points = {person_key(entry): entry for entry in results["classes"].get(cl, {}).get("standings", [])}

        for entry in class_results["standings"]:
            new_entry = new_points.get(person_key(entry))

            for race, points in entry["points"].items():
                new = 0 if new_entry is None else new_entry["points"].get(race, 0)
                if new != points:
                    changes.append(f"{race} {cl} {entry_name(entry)}: {points} -> {new}")

    return changes

def write_json(filename, data):

    with open(filename, "wt") as fed:
        json.dump(data, fed, indent=2, ensure_ascii=False)
        fed.write("\n")

def main():

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("series_file", type=str, help="Season series file, e.g. 2025/series.json")
    parser.add_argument("--minn", type=int, default=DEFAULT_MIN_N,
                        help="Minimum field size used in the points calculation")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help=f"Output JSON file (default: {POINTS_FILE} next to the series file)")
    parser.add_argument("--force", action="store_true",
                        help="Write the output even if published points would change")
    values = parser.parse_args()

    output = values.output or os.path.join(os.path.dirname(values.series_file), POINTS_FILE)

    published = None
    if os.path.exists(output):
        with open(output, "rt") as fed:
            published = json.load(fed)

    results = compute(values.series_file, values.minn, published)

    print_standings(results)
    print_overrides(results)

    if published is not None:
        changes = published_points_changes(published, results)
        if changes:
            print("Published points would change" + ("" if values.force else " (use --force to overwrite)") + ":")
            for change in changes:
                print(f"  {change}")
            if not values.force:
                sys.exit(1)

    write_json(output, results)
    print(f"Written '{output}'")

    print_possible_duplicates(results)

if __name__ == "__main__":
    main()
