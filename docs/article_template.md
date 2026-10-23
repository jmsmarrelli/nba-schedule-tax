# Rest, travel and historical NBA performance

How did schedule context relate to game performance after accounting for team-season strength? This study fits a fixed-effects model to 2003–04 through 2022–23 regular-season games. Coefficients describe adjusted historical associations.

## Model estimates

The outcome and intervals are in points per 100 estimated possessions. Rest and travel terms enter as home-minus-away differences; the label identifies the unit for each row.

{{table:coefficients.csv|label,beta,se,lo,hi}}

![Schedule associations and uncertainty](figures/02_schedule_effects.png)

A nonsignificant distance coefficient does not establish that travel is harmless. Correlated schedule features, unobserved itineraries, injury management and selection into rest can affect the estimates. The model does not identify a biological fatigue mechanism.

## Venue and time effects

The altitude indicator is largely identified by a small set of venues. It cannot separate elevation from all other persistent Denver and Salt Lake City differences. Win-equivalent tables translate fitted associations using a historical relationship between rating and wins; they are not causal wins attributable to altitude.

![Historical home-advantage estimates](figures/01_home_advantage.png)

The change during the pandemic also reflects many simultaneous changes. This design does not isolate the effect of crowds.

## Reproduction and limits

Possessions use FGA + 0.44 × FTA − OREB + TOV. Travel is a distance between recorded venues rather than an observed itinerary. The 2019–20 restart is excluded. Team-season indicators absorb average team quality, but they do not control every within-season availability or roster change. [Unrestricted home/away comparisons](output/symmetry_test.csv) provide a sensitivity check, not proof of the equality restriction.

## Front office implications

Use the estimates as historical context when planning availability review around dense portions of a schedule. Before changing a rotation, examine the actual travel itinerary and player workload. A prospective validation with opponent availability and fixed information dates is needed to turn these associations into an operational forecast.

## Reproduce

The historical analysis used Python 3.12 with the pinned dependencies below. From this repository:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make fetch-data PY=python
make all PY=python
make report site PY=python
```

`make all` verifies source hashes before running the analyses in order. A missing or changed input stops the build. Data downloads need network access; article rendering uses the included result tables. See [the source manifest](data/source_manifest.json), [method notes](docs/method.md) and [current validation record](VALIDATION_CURRENT.md) for the distinction between a source rebuild and checks of delivered outputs.

Season keys in CSV files use the **ending year**: `2025` means 2024–25. Display tables use full season labels. The MIT license covers code; third-party data retain their providers' rights and terms.

[Portfolio](https://github.com/jmsmarrelli/basketball-analytics) · [AI assistance and provenance](PROVENANCE.md)
