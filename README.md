# Australian Canoe Slalom Hub Series Results

Results and ranking points for the Australian Canoe Slalom Hub Series, published as a static web page on GitHub Pages and embedded in Google Sites.

Race results are created by the converters in the [aus_canoe_slalom_hub_series](../aus_canoe_slalom_hub_series) repo, which write them straight into this repo's season folders. This repo calculates the points from them and publishes everything.

## Repository layout

```
index.html          The results page (plain HTML/CSS/JS, no build step)
seasons.json        The seasons shown on the page, newest first
compute_points.py   Calculates a season's points and writes <YEAR>/points.json
ranking.py          Ranks one class of a race (best of two, heats/finals or placings)
render_pdf.py       Creates the results pdf from points.json (with latex.py)
check_official.py   Checks every season's points.json against its race results and published pdf
tests/              Unit tests
<YEAR>/
  series.json       The races in the season, with any points overrides
  <race id>.json    Results for one race, written by the series repo's convert_race.py
  points.json       Written by compute_points.py; do not edit by hand
_archive/           The published pdfs (not served by GitHub Pages)
```

Season folders are named after the year the season starts: `2025/` is the 2025 series, including the Age Nationals held in April 2026.

### `seasons.json`

A static page can't list directories, so the seasons are listed here. The first entry is the default season.

```json
{"dir": "2025", "label": "2025"}
```

`label` is the season name shown in the selector. It should match `year` in `series.json`.

## Data format

### `series.json`

```jsonc
{
  "name": "Australian Canoe Slalom Hub Series",
  "year": "2025",
  "races": [{"id": "wa_state_champs_2025", "short": "WA", "name": "Western Australia State Championships",
             "start_date": "2025-08-31", "end_date": "2025-08-31", "scaling": 1.0,
             "results": "wa_state_champs_2025.json"}],
  "points_overrides": []
}
```

A race with `"results": null` has not been run yet and is shown as pending.

### Race results (`<race id>.json`)

```jsonc
{
  "id": "nsw_state_champs_2025",
  "venue": "Penrith NSW",
  "format": "best_of_two",
  "source": "2025_NSW_State_Championships.xml",
  "classes": {
    "K1M": [
      {"bib": 2, "firstname": "Timothy", "surname": "ANDERSON", "club": "", "state": "NSW", "age_category": "Open",
       "runs": [{"time": 58.46, "penalty": 2, "gates": [0, 0, 2, 0]}, {"status": "DNS"}]}
    ]
  }
}
```

- Every paddler has `bib`, `firstname`, `surname`, `club`, `state` and `age_category`. Any of `bib`, `club`, `state` and `age_category` can be blank (`null` or `""`) if not known.
- `surname` is in capitals and `firstname` uses normal capitalisation. The page shows names as "Chris TUBB".
- Classes are `C1M`, `K1M`, `C1W` and `K1W`. Paddlers are in the order of the results sheet; `compute_points.py` and the page do the ranking.
- A run without a `status` is complete, with `time` and `penalty` in seconds, and `gates` (the penalty at each gate) when known. Other runs have a `status` of `DNS`, `DNF`, `CAP` (capsize) or `DSQ`, and a `penalty` if the results sheet shows one.
- `source` is the name of the original results file, kept in the series repo.
- The fields that depend on `format`:

  | `format` | Fields |
  |---|---|
  | `best_of_two` | `"runs": [run, run]` |
  | `heats_finals` | `"heats": [run, run]`, `"final": {"name": "A", ...run}` or `null` if not in a final |
  | `placings` | `"place": 1`, no run details (2023/2024 season) |

### Points (`points.json`)

`points.json` has everything needed to show the standings or create the pdf.

```jsonc
{
  "schema_version": 1,
  "series": {"name": "Australian Canoe Slalom Hub Series", "year": "2024/2025"},
  "generated": {"source": "2024/series.json", "git_commit": "...", "date": "..."},
  "rules": {"max_points": 1000, "min_n": 5, "race_points": "...", "combined": "..."},
  "races": [{"id": "wa_state_champs_2024", "short": "WA", "name": "Western Australia State Championships",
             "start_date": "2024-08-31", "end_date": "2024-08-31", "dates_display": "31 August 2024",
             "status": "completed", "scaling": 1.0}],
  "classes": {
    "C1M": {
      "standings": [{"rank": 1, "firstname": "Chris", "surname": "TUBB",
                     "points": {"wa_state_champs_2024": 1000}, "total": 1000}],
      "races": {"wa_state_champs_2024": {"field_size": 7, "n_used": 7,
                 "placings": [{"place": 1, "firstname": "Chris", "surname": "TUBB", "points": 1000}]}}
    }
  },
  "combined": {
    "women": {"classes": ["C1W", "K1W"],
              "standings": [{"rank": 1, "firstname": "Sarah", "surname": "CROSBEE",
                             "c1": 1818, "k1": 1935, "avg": 1877}]},
    "men": {"classes": ["C1M", "K1M"], "standings": []}
  },
  "points_overrides": [],
  "possible_duplicates": {"K1M": [[{"firstname": "Rhys", "surname": "MCRAE"},
                                   {"firstname": "Rhys", "surname": "MACRAE"}]]}
}
```

- `races` lists every race in the series. Pending races (`"status": "pending"`) have no points or placings.
- `standings` lists are in published order. Equal points share a `rank`.
- `placings` are the places used for the points, including any `points_overrides`. Paddlers who share a place have the same `place`.
- `field_size` is the number ranked in the class at that race. `n_used` is the `N` used in the points formula.
- To match a paddler across races, classes or seasons, compare `firstname` and `surname` ignoring upper/lower case.
- `git_commit` ends in `-dirty` if the working tree had uncommitted changes when the file was written.

## Ranking and points rules

These are implemented in `ranking.py` and `compute_points.py`. The page ranks the race results the same way in JavaScript.

### Race ranking (per class)

- **Best of two runs:** a run's total is `time + penalty`. Paddlers are ranked on their best total from their completed runs.
- **Heats and finals** (VIC): paddlers are ranked in the order of the A final, then the B final, then everyone else on their best heat run. A paddler with a DNS, DNF or CAP in a final is ranked on their heats.
- **Placings** (2023/2024): only the finishing order is known.
- **Ties:** equal totals (to 0.01 s) share the rank and the next rank is skipped: 1, 2, 2, 4.
- A paddler without any completed run is not ranked, gets 0 points and isn't counted in N.

### Points

- **Race points:** `round_half_up(1000 - (place - 1) * 1000 / N)`, where `N = max(5, number ranked in the class)`. Paddlers who share a place get the same points. A race the paddler didn't enter scores 0.
- **Class total:** the sum of the race points. Every race counts.
- **Combined:** `round_half_up((C1 total + K1 total) / 2)`. A class the paddler didn't race counts as 0.
- **Ties:** equal points share a rank and the next rank is skipped (1, 2, 2, 4). Tied paddlers keep the order they have in the published `points.json`; anyone not yet published is listed alphabetically. The pdf shows the second and later rows of a tie as "-".
- **Matching paddlers:** paddlers are matched by surname and first name, ignoring upper/lower case and extra spaces. `compute_points.py` lists pairs of names in a class that could be spelling variants (edit distance < 4, a substitution counting as 2).

### Points overrides

Published points are never changed. Where the rules give a different order from what was published, `points_overrides` in `series.json` sets the places used for the points. The race results still show the order given by the rules, and the page marks the overridden points with `*`.

```jsonc
"points_overrides": [
  {"race": "vic_state_champs_2025", "class": "K1W",
   "places": [{"firstname": "Maggie", "surname": "POTUGUNTLA", "place": 15},
              {"firstname": "Elodie", "surname": "HAMMOND", "place": 16}],
   "reason": "The published 2025 points used the A final order for a CAP and a DNS in the final, ..."}
]
```

A `place` of `null` leaves the paddler out of the points, and out of N.

| Race | Class | Published points |
|---|---|---|
| VIC 2024 | K1M | Left out the finalists with a DNS or CAP in the final |
| TAS 2024 | K1M | Ranked on the spreadsheet's run totals, several of which don't equal time + penalty |
| Age Nationals 2024 | K1M | Used the results export, which took the slower run as the best for two paddlers, and gave two tied paddlers consecutive places |
| VIC 2025 | K1W | Kept the A final order for a CAP and a DNS in the final |

## Adding a race

1. In the series repo, put the original results files in `raw_results_<YEAR>/`, add the race to this repo's `<YEAR>/series.json` with `"results": "<race id>.json"`, and convert the results, pointing `--series` at this repo:
   ```
   python convert_race.py siwi raw_results_2025/2025_NSW_State_Championships.xml \
       --series ../aus_canoe_slalom_hub_results/2025/series.json --id nsw_state_champs_2025
   ```
   The race file is written next to `series.json`. See the series repo README for the other formats and the details filled in.
2. Check the warnings, and make any corrections (such as name spellings) in the race file here. From now on it is the source for the points.
3. Calculate the points:
   ```
   uv run compute_points.py 2025/series.json
   ```
   It prints the standings, any points overrides, and pairs of names that could be the same person. A name warning looks like this:
   ```
   Possible duplicate names in class 'K1M'
   'Rhys MCRAE' == 'Rhys MACRAE' ?
   ```
   If they are the same person, fix the spelling in the race file and re-run.
4. Check the page locally (see below).
5. Commit and push. GitHub Pages updates the live site.

For a new season, create `<YEAR>/series.json` and add the season to the top of `seasons.json`.

### Published points are frozen

When `compute_points.py` is re-run, it compares the new points against the existing `points.json`. If any points already published for a race would change, it lists them and stops without writing:

```
Published points would change (use --force to overwrite):
  vic_state_champs_2025 K1W Elodie HAMMOND: 63 -> 125
```

Use `--force` only when a correction to published results is intended. To keep a published result instead, add a points override.

### The pdf

```
uv run render_pdf.py 2025/points.json            # writes australian_canoe_slalom_hub_series_2025.pdf
uv run render_pdf.py 2025/points.json --debug    # adds the race-by-race tables
```

It needs `pdflatex`. To publish a pdf, check it and copy it into `_archive/` as `<series>_<YEAR>_final.pdf`. `render_pdf.py` won't write into `_archive/`, so a published pdf can't be overwritten by accident. GitHub Pages leaves out folders starting with `_`, so the pdfs aren't on the site.

### Checking the published results

`uv run check_official.py` checks every season in `seasons.json`. For each one it:

- recomputes the points from the race results and checks they match `points.json`
- checks that tied entries share a rank and the rank after a tie is skipped
- rebuilds the pdf and compares its text with the published pdf in `_archive/` (needs `pdftotext`)

The 2023/2024 and 2024/2025 pdfs were published with surnames in title case ("Sarah Crosbee"), so those two are compared ignoring case. Every rank and point value still has to match.

Run the unit tests with `uv run python -m unittest discover -s tests`.

## The page

- **Standings:** women's and men's combined, then C1M, K1M, C1W and K1W, with each race's points and the total.
- **Races:** the races in the season, with dates and status. Select a race for its full results.
- **Race results:** each class's runs, penalties, totals, ranks and points. The run that counts is highlighted. The layout follows the race format (best of two, heats and finals, or placings only). Points come from `points.json`, so points overrides are shown (marked `*`).
- **How it works:** the points rules.
- **Paddler page:** select any name to see that paddler across every season:
  - a summary of their combined, C1 and K1 ranks and points in each season
  - their place and points at each race, with links to the race results

  Names are matched across seasons by first name and surname, ignoring case. The browser back button returns to the page the name was selected from.
- **Search** filters every table by name, including the race results.
- **Show details** adds the working behind the standings, which is what the debug pdf shows:
  - each race's placings and points for each class
  - the field size and the N used in the points formula
  - the state and age category in the race results

Equal ranks are shown as "=13". The "Show details" setting is remembered in the browser.

Useful page URLs for testing:

- `?season=2023&cls=K1M&detail=1`: a season and class, with details
- `?q=watson`: search every table
- `?paddler=lucy+casserley`: a paddler page
- `?view=races`: the races tab
- `?race=vic_state_champs_2025&cls=K1W`: a race's results (heats and finals, with an override)
- `?season=2023&race=wa_state_champs_2023`: a race with placings only
- `?view=about`: the "How it works" tab

## Running locally

Requires [uv](https://docs.astral.sh/uv/). The project uses only the Python standard library.

```
uv sync                                  # first time only; creates .venv
uv run python -m http.server 8000
```

Open <http://localhost:8000>. The page has to be served over HTTP to load its JSON files, so opening `index.html` directly from disk will not work.

## Publishing

The site is served by GitHub Pages from the root of the `main` branch. To embed it in Google Sites, use **Insert → Embed → By URL** with the GitHub Pages address. The Google Sites page then updates whenever the repo is pushed.
