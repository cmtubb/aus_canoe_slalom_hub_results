#!/usr/bin/env python3
"""
Check the published points for each season in seasons.json (<dir>/points.json):

  - recompute the points from the season's race results and compare
  - check that tied entries share a rank and the following rank is skipped
  - rebuild the pdf and compare its text with the published pdf in _archive/
"""

import os
import sys
import json
import difflib
import argparse
import subprocess
import tempfile

import compute_points
import render_pdf

ARCHIVE_DIR = os.path.join(compute_points.REPO_DIR, "_archive")

# These were published with surnames in title case ("Crosbee") rather than
# upper case ("CROSBEE"), so their text is compared ignoring case
CASE_INSENSITIVE = {"australian_canoe_slalom_hub_series_2023_final",
                    "australian_canoe_slalom_hub_series_2024_final"}

def pdf_stem(results, season_dir):
    """ Name of the published pdf, named by the season folder (the year the
    season starts), e.g. australian_canoe_slalom_hub_series_2024_final """

    return f"{results['series']['name'].lower().replace(' ', '_')}_{season_dir}_final"

def pdf_text(filename, ignore_case):

    text = subprocess.check_output(["pdftotext", "-layout", filename, "-"], text=True)

    lines = [" ".join(line.split()) for line in text.splitlines()]
    if ignore_case:
        lines = [line.lower() for line in lines]
    return lines

def check_pdf(results, season_dir, tmpdir):

    stem = pdf_stem(results, season_dir)
    published_pdf = os.path.join(ARCHIVE_DIR, stem + ".pdf")
    if not os.path.exists(published_pdf):
        print(f"  no published pdf ({os.path.relpath(published_pdf, compute_points.REPO_DIR)})")
        return []

    ignore_case = stem in CASE_INSENSITIVE

    render_pdf.render(results, os.path.join(tmpdir, stem + ".tex"), quiet=True)

    published = pdf_text(published_pdf, ignore_case)
    rendered = pdf_text(os.path.join(tmpdir, stem + ".pdf"), ignore_case)

    diff = list(difflib.unified_diff(published, rendered, "published", "rendered", lineterm="", n=1))

    how = "ignoring case" if ignore_case else "exactly"
    if diff:
        return [f"rendered pdf text differs from the published pdf ({how}):"] + diff[:40]

    print(f"  pdf text matches the published pdf ({how})")
    return []

def check_recompute(results):

    source = results["generated"]["source"]
    recomputed = compute_points.compute(os.path.join(compute_points.REPO_DIR, source),
                                        results["rules"]["min_n"], results)

    errors = [f"'{key}' differs when recomputed from '{source}'"
              for key in results.keys() | recomputed.keys()
              if key != "generated" and results.get(key) != recomputed.get(key)]

    if not errors:
        print(f"  matches points recomputed from '{source}'")
    return errors

def check_ranks(name, standings, points_key):

    errors = []
    for pos, entry in enumerate(standings):

        if pos == 0:
            expected = 1
        elif entry[points_key] > standings[pos-1][points_key]:
            errors.append(f"{name}: '{compute_points.entry_name(entry)}' is not in points order")
            continue
        elif entry[points_key] == standings[pos-1][points_key]:
            expected = standings[pos-1]["rank"]
        else:
            expected = pos+1

        if entry["rank"] != expected:
            errors.append(f"{name}: '{compute_points.entry_name(entry)}' has rank {entry['rank']}, expected {expected}")

    return errors

def check_all_ranks(results):

    errors = []
    for cl, class_results in results["classes"].items():
        errors.extend(check_ranks(cl, class_results["standings"], "total"))
    for group, combined in results["combined"].items():
        errors.extend(check_ranks(f"{group} combined", combined["standings"], "avg"))

    if not errors:
        print("  ranks are consistent with the points")
    return errors

def main():

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("json_files", type=str, nargs="*",
                        help="Points JSON files to check (default: every season in seasons.json)")
    values = parser.parse_args()

    json_files = values.json_files
    if not json_files:
        with open(os.path.join(compute_points.REPO_DIR, "seasons.json"), "rt") as fed:
            json_files = [os.path.join(compute_points.REPO_DIR, season["dir"], compute_points.POINTS_FILE)
                          for season in json.load(fed)]

    failed = False
    for json_file in json_files:

        print(os.path.relpath(json_file, compute_points.REPO_DIR))

        with open(json_file, "rt") as fed:
            results = json.load(fed)

        errors = check_all_ranks(results)
        errors.extend(check_recompute(results))
        with tempfile.TemporaryDirectory() as tmpdir:
            season_dir = os.path.basename(os.path.dirname(os.path.abspath(json_file)))
            errors.extend(check_pdf(results, season_dir, tmpdir))

        for error in errors:
            print(f"  {error}")
        failed = failed or bool(errors)

    if failed:
        print("FAILED")
        sys.exit(1)

    print("All published points OK")

if __name__ == "__main__":
    main()
