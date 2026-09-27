# Australian Canoe Slalom Hub Series Results

Results for the Australian Canoe Slalom Hub Series, published as a static web page on GitHub Pages and embedded in Google Sites.

The points are calculated in the [aus_canoe_slalom_hub_series](../aus_canoe_slalom_hub_series) repo. This repo only displays them. The JSON files are unchanged copies of that repo's `official_results/*_final.json`, and the page never recalculates points.

## Repository layout

```
index.html      The results page (plain HTML/CSS/JS, no build step)
seasons.json    The seasons shown on the page, newest first
2023/           2023/2024 season
2024/           2024/2025 season
2025/           2025 season
```

Each season folder holds the official results JSON for that season. Folders are named after the year the season starts. Later, the folders will also hold the individual race results.

### `seasons.json`

A static page can't list directories, so the seasons are listed here. The first entry is the default season.

```json
{"dir": "2025", "label": "2025", "file": "australian_canoe_slalom_hub_series_2025_final.json"}
```

`label` is the season name shown in the selector. It should match `series.year` in the JSON.

The results JSON format is documented in the hub series repo README.

## The page

- **Standings:** women's and men's combined, then C1M, K1M, C1W and K1W, with each race's points and the total.
- **Races:** the races in the season, with dates and status.
- **How it works:** the points rules.
- **Paddler page:** select any name to see that paddler across every season:
  - a summary of their combined, C1 and K1 ranks and points in each season
  - their place and points at each race

  Names are matched across seasons by first name and surname, ignoring case. The browser back button returns to the page the name was selected from.
- **Search** filters every table by name.
- **Show details** adds the working behind the standings, which is what the debug pdf shows:
  - each race's placings and points for each class
  - the field size and the N used in the points formula

Equal ranks are shown as "=13". The "Show details" setting is remembered in the browser.

Useful page URLs for testing:

- `?season=2023&cls=K1M&detail=1`: a season and class, with details
- `?q=watson`: search every table
- `?paddler=lucy+casserley`: a paddler page
- `?view=races`: the races tab
- `?view=about`: the "How it works" tab

## Adding or updating a season

1. Publish the results in the hub series repo, following its README.
2. Copy the `_final.json` into the season folder unchanged, and check the copy:
   ```
   cp ../aus_canoe_slalom_hub_series/official_results/australian_canoe_slalom_hub_series_2026_final.json 2026/
   cmp 2026/australian_canoe_slalom_hub_series_2026_final.json ../aus_canoe_slalom_hub_series/official_results/australian_canoe_slalom_hub_series_2026_final.json
   ```
3. For a new season, add it to the top of `seasons.json`.
4. Check the page locally against the published pdf.
5. Commit and push. GitHub Pages updates the live site.

## Running locally

Requires [uv](https://docs.astral.sh/uv/). The project uses only the Python standard library.

```
uv sync                                  # first time only; creates .venv
uv run python -m http.server 8000
```

Open <http://localhost:8000>. The page has to be served over HTTP to load its JSON files, so opening `index.html` directly from disk will not work.

## Publishing

The site is served by GitHub Pages from the root of the `main` branch. To embed it in Google Sites, use **Insert → Embed → By URL** with the GitHub Pages address. The Google Sites page then updates whenever the repo is pushed.
