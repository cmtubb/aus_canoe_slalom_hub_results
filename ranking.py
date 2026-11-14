"""
Ranking of the paddlers in one class of a race, from the race results JSON
(results/<YEAR>/<race id>.json). Three race formats are supported:

  best_of_two   Two runs, ranked on the best run total (time + penalty).
  heats_finals  Two heat runs, then an A final and a B final. Ranked in order
                of the A final, the B final and then the heats. A paddler
                without a completed final run is ranked on their heats.
  placings      Only the finishing places are known (older results).

Equal totals (to 0.01 s) share a rank and the next rank is skipped: 1, 2, 2, 4.
A paddler without any completed run is not ranked.
"""

FORMATS = ["best_of_two", "heats_finals", "placings"]

FINALS = ["A", "B"]

def run_total(run):
    """ Total (time + penalty) of a completed run, None if the run wasn't completed """

    if run is None or run.get("status") or run.get("time") is None:
        return None

    return run["time"] + run.get("penalty", 0)

def best_total(runs):

    totals = [total for total in (run_total(run) for run in runs) if total is not None]

    return min(totals) if totals else None

def _hundredths(total):
    """ Totals are compared to 0.01 s, avoiding floating point differences """

    return round(total * 100)

def _rank_groups(groups):
    """ Rank a list of groups, each a list of (entry, total) already in order.
    Ties share a rank within a group, the groups themselves never tie """

    ranked = []
    for group in groups:
        for n, (entry, total) in enumerate(group):
            if n > 0 and _hundredths(total) == _hundredths(group[n-1][1]):
                rank = ranked[-1][1]
            else:
                rank = len(ranked) + 1
            ranked.append((entry, rank))
    return ranked

def _sorted_by_total(entries_totals):

    # sorted() is stable, so ties keep the order of the results file
    return sorted(entries_totals, key=lambda et: _hundredths(et[1]))

def rank_best_of_two(entries):

    totals = [(entry, best_total(entry.get("runs", []))) for entry in entries]

    placed = _sorted_by_total([(entry, total) for entry, total in totals if total is not None])
    unplaced = [entry for entry, total in totals if total is None]

    return _rank_groups([placed]), unplaced

def final_total(entry):

    final = entry.get("final")
    if final is None:
        return None, None

    return final["name"], run_total(final)

def rank_heats_finals(entries):

    groups = {name: [] for name in FINALS}
    heats = []
    unplaced = []

    for entry in entries:
        name, total = final_total(entry)
        if total is not None:
            groups[name].append((entry, total))
            continue

        total = best_total(entry.get("heats", []))
        if total is not None:
            heats.append((entry, total))
        else:
            unplaced.append(entry)

    ordered = [_sorted_by_total(groups[name]) for name in FINALS]
    ordered.append(_sorted_by_total(heats))

    return _rank_groups(ordered), unplaced

def rank_placings(entries):

    placed = sorted([entry for entry in entries if entry.get("place") is not None],
                    key=lambda entry: entry["place"])
    unplaced = [entry for entry in entries if entry.get("place") is None]

    return [(entry, entry["place"]) for entry in placed], unplaced

def rank_class(race_format, entries):
    """ Rank the entries for one class of a race, returns ([(entry, rank)], [unplaced entries]).
    The ranked entries are in rank order """

    if race_format == "best_of_two":
        return rank_best_of_two(entries)
    elif race_format == "heats_finals":
        return rank_heats_finals(entries)
    elif race_format == "placings":
        return rank_placings(entries)

    assert 0, f"Race format '{race_format}' not supported, expected one of {FORMATS}"
