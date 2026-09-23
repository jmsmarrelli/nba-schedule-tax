"""Paths, constants and the handful of knobs the pipeline exposes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
OUT = ROOT / "output"

for d in (RAW, PROC, FIG, OUT):
    d.mkdir(parents=True, exist_ok=True)

# Season label is the year the season ends: 2023 == 2022-23.
FIRST_SEASON = 2004
LAST_SEASON = 2023
SEASONS = list(range(FIRST_SEASON, LAST_SEASON + 1))

# Rest is capped here. Beyond three days off the marginal effect is flat and the
# cells get thin, so 3+ is one bucket.
REST_CAP = 3

# Venues at or above this elevation count as high altitude. Denver (5,280) and
# Salt Lake City (4,226) clear it; Phoenix, Oklahoma City and Atlanta, all around
# a thousand feet, do not, and show no effect.
HIGH_ALTITUDE_FT = 4000

# The 2019-20 restart was played by twenty-two teams in one Florida complex with
# no travel, no crowd and three months off. It is a different sport for these
# purposes and is excluded from the model, not silently averaged into it.
BUBBLE_CITY = "Lake Buena Vista"

SEED = 20240117
