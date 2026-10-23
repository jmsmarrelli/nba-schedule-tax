"""Stage 3 - adding the calendar up over a season, in wins.

    python src/run_03_luck.py

The coefficients from stage 2 price a single night. Applying them to every game
a team played, and subtracting what its opponents were carrying that night, gives
the total the schedule handed to or took from each team across a season.

Converting to wins uses the empirical exchange rate in this data: regress
team-season wins on team-season net rating and read the slope.

Writes output/schedule_luck.csv and two figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BUBBLE_CITY, FIG, LAST_SEASON, OUT, PROC  # noqa: E402
import model as M  # noqa: E402
import style as S  # noqa: E402


def wins_per_net_point(panel: pd.DataFrame) -> tuple[float, float]:
    """Slope of wins on net rating, per 82 games, fit on team-seasons."""
    t = panel.assign(win=(panel["net"] > 0).astype(int))
    ts = t.groupby(["season", "team"]).agg(
        g=("win", "size"), wins=("win", "sum"), net=("net", "mean"))
    ts = ts[ts["g"] >= 50]
    ts["win_pct"] = ts["wins"] / ts["g"]
    b, a = np.polyfit(ts["net"], ts["win_pct"], 1)
    r = float(np.corrcoef(ts["net"], ts["win_pct"])[0, 1])
    return b * 82, r


# Altitude is not schedule luck. Every team plays in Denver, every year, and
# Denver plays there 41 times. It is a permanent property of a franchise's
# building, so it is priced separately rather than folded into the calendar.
CALENDAR_TERMS = [t for t in M.OWN if t != "d_alt"]
VENUE_TERMS = ["d_alt"]


def burden_cost(panel: pd.DataFrame, coef: pd.DataFrame, terms) -> pd.Series:
    """Points per 100 that a team's own situation cost it, per game."""
    b = M.own_burden(panel)
    weights = coef.set_index("term")["beta"]
    cost = pd.Series(0.0, index=panel.index)
    for term in terms:
        cost += weights[term] * b[M.OWN[term]]
    return cost


def main() -> None:
    panel = pd.read_csv(PROC / "team_games.csv.gz", low_memory=False)
    panel = panel[panel["city"] != BUBBLE_CITY].reset_index(drop=True)
    coef = pd.read_csv(OUT / "coefficients.csv")

    key = pd.MultiIndex.from_arrays([panel["game_id"], panel["opp"]])
    for name, terms in (("cal", CALENDAR_TERMS), ("alt", VENUE_TERMS)):
        panel[f"own_{name}"] = burden_cost(panel, coef, terms)
        panel[f"opp_{name}"] = key.map(
            panel.set_index(["game_id", "team"])[f"own_{name}"])
    panel = panel.dropna(subset=["opp_cal", "opp_alt"])
    panel["net_schedule"] = panel["own_cal"] - panel["opp_cal"]
    panel["net_altitude"] = panel["own_alt"] - panel["opp_alt"]

    wpp, r = wins_per_net_point(panel)
    print(f"wins per point of net rating, over 82 games: {wpp:.2f}  (r = {r:.3f})")

    luck = panel.groupby(["season", "team"]).agg(
        games=("game_id", "size"),
        net_schedule=("net_schedule", "mean"),
        net_altitude=("net_altitude", "mean"),
        b2b=("b2b", "sum"),
        miles=("miles", "sum"),
    ).reset_index()
    luck["wins_effect"] = luck["net_schedule"] * wpp * luck["games"] / 82
    luck["wins_altitude"] = luck["net_altitude"] * wpp * luck["games"] / 82
    luck = luck.sort_values(["season", "wins_effect"])
    luck.round(4).to_csv(OUT / "schedule_luck.csv", index=False)

    fig_season(luck[luck["season"] == LAST_SEASON], LAST_SEASON)
    fig_distribution(luck)

    print(f"\nspread in schedule-driven wins within a season: "
          f"{luck.groupby('season')['wins_effect'].agg(lambda s: s.max() - s.min()).mean():.2f} "
          "wins on average between the most and least favoured team")
    print(f"standard deviation across all team-seasons: {luck['wins_effect'].std():.2f} wins")
    print(f"\n--- {LAST_SEASON - 1}-{str(LAST_SEASON)[2:]}, hardest and easiest ---")
    d = luck[luck["season"] == LAST_SEASON]
    print(pd.concat([d.head(5), d.tail(5)])[
        ["team", "games", "b2b", "miles", "net_schedule", "wins_effect"]].round(2)
        .to_string(index=False))
    worst = luck.nsmallest(5, "wins_effect")[["season", "team", "b2b", "miles", "wins_effect"]]
    best = luck.nlargest(5, "wins_effect")[["season", "team", "b2b", "miles", "wins_effect"]]
    print("\nheaviest calendars since 2004")
    print(worst.round(2).to_string(index=False))
    print("\nlightest")
    print(best.round(2).to_string(index=False))

    alt = (luck.groupby("team")["wins_altitude"].mean()
           .sort_values(ascending=False).head(4))
    print("\naltitude, priced separately (mean wins per season)")
    print(alt.round(2).to_string())


def fig_season(d: pd.DataFrame, season: int) -> None:
    d = d.sort_values("wins_effect")
    fig, ax = plt.subplots(figsize=(8.4, 7.0))
    colours = [S.SERIES[0] if v >= 0 else S.SERIES[1] for v in d["wins_effect"]]
    ax.barh(np.arange(len(d)), d["wins_effect"], color=colours, height=0.66)
    for i, v in enumerate(d["wins_effect"]):
        ax.text(v + (0.03 if v >= 0 else -0.03), i, f"{v:+.2f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=8.4, color=S.INK_2)
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=3)
    ax.set_yticks(np.arange(len(d)), d["team"])
    ax.set_ylim(-0.8, len(d) - 0.2)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=8.8)
    ax.set_xlabel("Wins the schedule was worth")
    ax.set_title(f"Who the calendar helped, {season - 1}-{str(season)[2:]}", loc="left")
    S.caption(fig, "Rest, density, travel and time zones only. A team's own burden priced "
                   "against what its opponents were carrying on the same nights, summed over "
                   "the season and converted at the empirical wins-per-net-point rate. "
                   "Altitude is excluded here and priced separately: it is a property of a "
                   "building, not of a calendar.")
    fig.tight_layout()
    fig.savefig(FIG / "04_schedule_luck_season.png")
    plt.close(fig)


def fig_distribution(luck: pd.DataFrame) -> None:
    alt = (luck.groupby("team")["wins_altitude"].mean().sort_values(ascending=False))
    mountain = alt.head(2)

    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.hist(luck["wins_effect"], bins=40, color=S.SERIES[0], alpha=0.9, zorder=2)
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=3)

    top = ax.get_ylim()[1]
    x = float(mountain.mean())
    ax.annotate("", xy=(x, 0), xytext=(x, top * 0.72),
                arrowprops=dict(arrowstyle="-|>", color=S.SERIES[1], lw=2.2))
    ax.text(x, top * 0.75, f"{mountain.index[0]} and {mountain.index[1]},\n"
                           f"from altitude alone: {x:+.2f} wins",
            ha="center", va="bottom", fontsize=9.5, color=S.SERIES[1],
            fontweight="semibold", linespacing=1.5)

    sd = luck["wins_effect"].std()
    ax.text(0.015, 0.94, f"Calendar luck: standard deviation {sd:.2f} wins,\n"
                         f"full range {luck['wins_effect'].min():+.2f} to "
                         f"{luck['wins_effect'].max():+.2f} across "
                         f"{len(luck):,} team-seasons",
            transform=ax.transAxes, va="top", fontsize=9, color=S.INK_2,
            linespacing=1.6)

    S.strip(ax)
    ax.set_xlim(-1.0, x + 1.1)
    ax.set_ylim(0, top * 1.16)
    ax.set_xlabel("Wins per season")
    ax.set_ylabel("Team-seasons")
    ax.set_title("Schedule luck is a rounding error. Elevation is not.", loc="left")
    S.caption(fig, "Blue: what rest, density, travel and time zones were worth to each team "
                   "across a season, net of what its opponents were carrying. Orange: what "
                   "the two mountain arenas were worth to the teams that live in them, from "
                   "the altitude term alone, in an average season.")
    fig.tight_layout()
    fig.savefig(FIG / "05_schedule_luck_distribution.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
