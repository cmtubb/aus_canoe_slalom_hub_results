#!/usr/bin/env python3
"""
Create the hub series results pdf from a points.json written by compute_points.py.
"""

import os
import json
import argparse

import latex
from compute_points import entry_name

def display_ranks(standings):
    """ Rank to print for each row, a tie with the row above is shown as " - " """

    ranks = []
    for pos, entry in enumerate(standings):
        if pos > 0 and entry["rank"] == standings[pos-1]["rank"]:
            ranks.append(" - ")
        else:
            ranks.append(f"{entry['rank']}")
    return ranks

def write_combined(doc, title, combined):

    doc.newpage()
    doc.add_section_title(title)

    c1, k1 = [cl[:2].lower() for cl in combined["classes"]]

    data = []
    for rank, entry in zip(display_ranks(combined["standings"]), combined["standings"]):
        data.append([rank, entry_name(entry), f"{entry[c1]}", f"{entry[k1]}", f"{entry['avg']}"])

    doc.totals_table(data)

def write_race_summary(doc, cl, races, class_results):

    doc.write("\\begin{landscape}")
    doc.write("\\pagestyle{empty}")

    doc.write("\\subsection*{Race Rankings}\n")

    placings = [class_results["races"][race["id"]]["placings"] for race in races]

    max_n = max(len(race_placings) for race_placings in placings)

    data = []
    for ind in range(max_n):

        dataline = []
        for race_placings in placings:

            if ind < len(race_placings):
                dataline.append(entry_name(race_placings[ind]))
                dataline.append("{:d}".format(race_placings[ind]["points"]))
            else:
                dataline.extend([" "," "])

        data.append(dataline)

    doc.race_summary_table(cl, [race["short"] for race in races], data)
    doc.write("\\end{landscape}")

    doc.write("\\pagestyle{fancy}")

def render(results, filename, debug=False, quiet=False):
    """ Write the LaTeX for the results to filename (.tex) and build the pdf """

    races = [race for race in results["races"] if race["status"] == "completed"]

    doc = latex.LaTeX(filename, results["series"]["name"], results["series"]["year"], quiet)

    doc.add_section_title("Races in the series", False)

    doc.write("\\begin{tabular}{lll}\n")
    doc.write("& & \\\\\n")
    for race in results["races"]:
        status = "Completed" if race["status"] == "completed" else "Pending"
        doc.write(f"{race['name']} & {race['dates_display']} & {status} \\\\\n")
        doc.write("& & \\\\\n")
    doc.write("\\end{tabular}\n")

    ranking_headers = ["Rank", "Athelete"]
    ranking_headers.extend([race["short"] for race in races])
    ranking_headers.append("Total")

    write_combined(doc, "Women Combined Rankings", results["combined"]["women"])
    write_combined(doc, "Men Combined Rankings", results["combined"]["men"])

    for cl, class_results in results["classes"].items():
        doc.newpage()
        doc.add_section_title(cl)

        if debug:
            doc.write("\\subsection*{Overall Rankings}\n")

        standings = class_results["standings"]

        data = []
        for rank, entry in zip(display_ranks(standings), standings):

            data_line = [rank, entry_name(entry)]

            for race in races:
                data_line.append(f"{entry['points'][race['id']]:5d}")

            data_line.append(f"{entry['total']:4d}")

            data.append(data_line)

        doc.ranking_table(ranking_headers, data)

        doc.newpage()
        if debug:
            write_race_summary(doc, cl, races, class_results)

    doc.clearpage()
    doc.close()

def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=str, help="Points JSON written by compute_points.py, e.g. 2025/points.json")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output pdf (default: <series>_<season folder>.pdf in the current directory)")
    parser.add_argument("--debug", action="store_true", help="Add the race break down tables for debugging")
    values = parser.parse_args()

    with open(values.json_file, "rt") as fed:
        results = json.load(fed)

    output = values.output
    if output is None:
        season_dir = os.path.basename(os.path.dirname(os.path.abspath(values.json_file)))
        output = f"{results['series']['name'].lower().replace(' ', '_')}_{season_dir}.pdf"

    stem = os.path.splitext(output)[0]

    # Protect the published pdfs from being overwritten
    archive_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_archive")
    assert os.path.dirname(os.path.abspath(stem)) != archive_dir, \
        "Refusing to write into _archive, copy the pdf there by hand"

    render(results, stem + ".tex", values.debug)

    print(f"Written '{stem}.pdf'")

if __name__ == "__main__":
    main()
