"""Stage 2 - what the calendar is worth, in points.

    python src/run_02_model.py

Fits the fixed-effects model in model.py, checks the symmetry restriction it
imposes, and draws the three figures that carry the coefficients.

Writes output/coefficients.csv, output/home_advantage.csv,
output/symmetry_test.csv.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BUBBLE_CITY, FIG, OUT, PROC  # noqa: E402
import model as M  # noqa: E402
import style as S  # noqa: E402


def game_frame(panel: pd.DataFrame) -> pd.DataFrame:
    """Fold the team-game panel back to one row per game with differenced terms."""
    burden = M.own_burden(panel)
    p = pd.concat([panel[["game_id", "season", "team", "is_home", "net", "city",
                          "neutral_site"]], burden], axis=1)
    home = p[p["is_home"] == 1].set_index("game_id")
    away = p[p["is_home"] == 0].set_index("game_id")
    common = home.index.intersection(away.index)
    home, away = home.loc[common], away.loc[common]

    g = pd.DataFrame({
        "season": home["season"], "net_h": home["net"],
        "home": home["team"], "away": away["team"],
        "city": home["city"], "neutral_site": home["neutral_site"],
    })
    for term, col in M.OWN.items():
        g[term] = home[col].to_numpy() - away[col].to_numpy()
        g[f"h_{col}"] = home[col].to_numpy()
        g[f"a_{col}"] = away[col].to_numpy()
    g["ts_home"] = g["home"] + "_" + g["season"].astype(str)
    g["ts_away"] = g["away"] + "_" + g["season"].astype(str)
    return g.reset_index()


def symmetry_test(g: pd.DataFrame) -> pd.DataFrame:
    """Fit home and away burdens separately and compare against the restriction.

    If rest is worth the same to whoever has it, the away coefficient should be
    minus the home coefficient. This reports both and the gap.
    """
    ts = pd.Index(sorted(set(g["ts_home"]) | set(g["ts_away"])))
    seasons = pd.Index(sorted(g["season"].unique()))
    n = len(g)
    cols = [f"h_{c}" for c in M.OWN.values()] + [f"a_{c}" for c in M.OWN.values()]
    X = np.zeros((n, len(ts) + len(seasons) + len(cols)))
    rows = np.arange(n)
    X[rows, ts.get_indexer(g["ts_home"])] += 1.0
    X[rows, ts.get_indexer(g["ts_away"])] -= 1.0
    X[rows, len(ts) + seasons.get_indexer(g["season"])] = 1.0
    for j, c in enumerate(cols):
        X[:, len(ts) + len(seasons) + j] = g[c].to_numpy()
    beta, se, _, _, _ = M.ols(X, g["net_h"].to_numpy())
    k = len(ts) + len(seasons)
    out = []
    for j, col in enumerate(M.OWN.values()):
        bh, bа = beta[k + j], beta[k + len(M.OWN) + j]
        sh, sa = se[k + j], se[k + len(M.OWN) + j]
        out.append({"term": col, "home_beta": bh, "home_se": sh,
                    "away_beta": bа, "away_se": sa,
                    "sum": bh + bа, "sum_se": np.hypot(sh, sa)})
    return pd.DataFrame(out)


def altitude_check(g: pd.DataFrame) -> pd.DataFrame:
    """Is the altitude term really altitude, or is it just Denver?

    The continuous term is identified almost entirely off two buildings. Swapping
    it for a separate dummy per elevated venue and dividing each by that venue's
    elevation gives an implied effect per 1,000 feet from each city on its own.
    If Denver and Salt Lake City land in the same place despite a thousand feet
    between them, altitude is a reasonable reading. If they do not, this is a
    Denver effect wearing an altitude costume.
    """
    import venues as V
    high = {c: V.CITIES[c][2] for c in V.CITIES if V.CITIES[c][2] >= 1000}
    ts = pd.Index(sorted(set(g["ts_home"]) | set(g["ts_away"])))
    seasons = pd.Index(sorted(g["season"].unique()))
    cities = pd.Index(sorted(high))
    base = [t for t in M.TERMS if t != "d_alt"]

    n = len(g)
    X = np.zeros((n, len(ts) + len(seasons) + len(base) + len(cities)))
    rows = np.arange(n)
    X[rows, ts.get_indexer(g["ts_home"])] += 1.0
    X[rows, ts.get_indexer(g["ts_away"])] -= 1.0
    X[rows, len(ts) + seasons.get_indexer(g["season"])] = 1.0
    for j, term in enumerate(base):
        X[:, len(ts) + len(seasons) + j] = g[term].to_numpy()
    k = len(ts) + len(seasons) + len(base)
    idx = cities.get_indexer(g["city"])
    hit = idx >= 0
    X[rows[hit], k + idx[hit]] = 1.0

    beta, se, _, _, _ = M.ols(X, g["net_h"].to_numpy())
    out = []
    for j, c in enumerate(cities):
        ft = high[c] / 1000.0
        out.append({"city": c, "elev_kft": ft, "n_games": int((g["city"] == c).sum()),
                    "home_bonus": beta[k + j], "se": se[k + j],
                    "per_1000ft": beta[k + j] / ft})
    return pd.DataFrame(out).sort_values("elev_kft", ascending=False)


def fig_home_advantage(hca: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.fill_between(hca["season"], hca["beta"] - 1.96 * hca["se"],
                    hca["beta"] + 1.96 * hca["se"],
                    color=S.SERIES[0], alpha=0.14, lw=0, zorder=2)
    ax.plot(hca["season"], hca["beta"], color=S.SERIES[0], zorder=3)
    ax.scatter(hca["season"], hca["beta"], s=20, color=S.SERIES[0],
               edgecolors=S.SURFACE, lw=1.4, zorder=4)
    ax.axhline(0, color=S.INK_3, lw=0.9, zorder=1)
    b, a = np.polyfit(hca["season"], hca["beta"], 1)
    ax.plot(hca["season"], a + b * hca["season"], color=S.INK, lw=1.4,
            ls=(0, (4, 3)), zorder=5)
    ax.text(0.02, 0.06, f"trend: {b:+.2f} points per 100 per season\n"
                        f"{hca['beta'].iloc[0]:.2f} in {hca['season'].iloc[0] - 1}-"
                        f"{str(hca['season'].iloc[0])[2:]}, "
                        f"{hca['beta'].iloc[-1]:.2f} in {hca['season'].iloc[-1] - 1}-"
                        f"{str(hca['season'].iloc[-1])[2:]}",
            transform=ax.transAxes, fontsize=9, color=S.INK_2, linespacing=1.5)
    S.strip(ax)
    ax.set_xticks(range(2004, 2024, 3))
    ax.set_ylabel("Home advantage, points per 100 possessions")
    ax.set_title("Home court has lost about a point", loc="left")
    S.caption(fig, "Season-by-season home advantage from a model with team-season fixed "
                   "effects and schedule controls, so this is home court net of who was "
                   "playing and how they arrived. Band is 95%. The 2019-20 restart and the "
                   "2020-21 crowd restrictions sit inside this window and are visible.")
    fig.tight_layout()
    fig.savefig(FIG / "01_home_advantage.png")
    plt.close(fig)


def fig_coefficients(coef: pd.DataFrame) -> None:
    d = coef.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    colours = [S.SERIES[0] if v < 0 else S.SERIES[1] for v in d["beta"]]
    ax.barh(d.index, d["beta"], color=colours, height=0.56, zorder=2)
    ax.errorbar(d["beta"], d.index, xerr=1.96 * d["se"], fmt="none",
                ecolor=S.INK_2, elinewidth=1.1, capsize=3, zorder=4)
    pad = 0.06 * (d["beta"].abs() + 1.96 * d["se"]).max()
    for i, row in d.iterrows():
        end = row["beta"] + np.sign(row["beta"]) * 1.96 * row["se"]
        ax.text(end + np.sign(row["beta"]) * pad, i, f"{row['beta']:+.2f}",
                va="center", ha="left" if row["beta"] >= 0 else "right",
                fontsize=9, color=S.INK_2, fontweight="semibold")
    span = (d["beta"].abs() + 1.96 * d["se"]).max()
    ax.set_xlim(-span - 6 * pad, span * 0.55 + 6 * pad)
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=3)
    ax.set_yticks(d.index, d["label"])
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=9.2)
    ax.set_xlabel("Effect on net rating, points per 100 possessions")
    ax.set_title("What arriving tired is worth", loc="left")
    S.caption(fig, "Each coefficient is the effect on a team's own net rating, relative to "
                   "three or more days off, holding the opponent's situation fixed. Bars are "
                   "95% intervals. Team-season fixed effects mean these are identified within "
                   "a roster's own season.")
    fig.tight_layout()
    fig.savefig(FIG / "02_schedule_effects.png")
    plt.close(fig)


def fig_schedule_trend(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2))
    ax = axes[0]
    ax.plot(summary.index, 82 * summary["b2b_rate"], color=S.SERIES[0], zorder=3)
    ax.scatter(summary.index, 82 * summary["b2b_rate"], s=18, color=S.SERIES[0],
               edgecolors=S.SURFACE, lw=1.4, zorder=4)
    S.strip(ax)
    ax.set_ylim(0, None)
    ax.set_xticks(range(2004, 2024, 4))
    ax.set_ylabel("Back-to-backs per team")
    ax.set_title("Back-to-backs", loc="left")

    ax = axes[1]
    ax.plot(summary.index, summary["miles_per_team"] / 1000, color=S.SERIES[1], zorder=3)
    ax.scatter(summary.index, summary["miles_per_team"] / 1000, s=18, color=S.SERIES[1],
               edgecolors=S.SURFACE, lw=1.4, zorder=4)
    S.strip(ax)
    ax.set_ylim(0, None)
    ax.set_xticks(range(2004, 2024, 4))
    ax.set_ylabel("Thousands of miles per team")
    ax.set_title("Travel", loc="left")

    S.caption(fig, "Regular season only. The 2011-12 lockout (66 games), the 2019-20 "
                   "suspension and the 2020-21 compressed calendar are the three dips.")
    fig.tight_layout()
    fig.savefig(FIG / "03_schedule_trend.png")
    plt.close(fig)


def main() -> None:
    panel = pd.read_csv(PROC / "team_games.csv.gz", low_memory=False)
    panel = panel[panel["city"] != BUBBLE_CITY]
    g = game_frame(panel)
    print(f"{len(g):,} games after dropping the {BUBBLE_CITY} restart")

    X, y, names, ts, seasons = M.build_design(g)
    beta, se, r2, resid, dof = M.ols(X, y)
    print(f"R² {r2:.4f}   residual SD {resid.std():.2f} points per 100   dof {dof:,}")

    k = len(ts) + len(seasons)
    coef = pd.DataFrame({
        "term": list(M.TERMS), "label": [M.TERMS[t] for t in M.TERMS],
        "beta": beta[k:], "se": se[k:],
    })
    coef["t"] = coef["beta"] / coef["se"]
    coef["lo"], coef["hi"] = coef["beta"] - 1.96 * coef["se"], coef["beta"] + 1.96 * coef["se"]
    coef.round(4).to_csv(OUT / "coefficients.csv", index=False)

    hca = pd.DataFrame({"season": seasons,
                        "beta": beta[len(ts):k], "se": se[len(ts):k]})
    hca.round(4).to_csv(OUT / "home_advantage.csv", index=False)

    strength = pd.DataFrame({"team_season": ts, "strength": beta[:len(ts)]})
    strength[["team", "season"]] = strength["team_season"].str.rsplit("_", n=1, expand=True)
    strength.round(4).to_csv(OUT / "team_strength.csv", index=False)

    sym = symmetry_test(g)
    sym["t_sum"] = sym["sum"] / sym["sum_se"]
    sym.round(4).to_csv(OUT / "symmetry_test.csv", index=False)

    summary = pd.read_csv(OUT / "schedule_summary.csv", index_col="season")
    fig_home_advantage(hca)
    fig_coefficients(coef)
    fig_schedule_trend(summary)

    print("\nschedule coefficients (points per 100 possessions)")
    print(coef[["label", "beta", "se", "t"]].round(3).to_string(index=False))
    print("\nhome advantage, first and last five seasons")
    print(pd.concat([hca.head(5), hca.tail(5)]).round(3).to_string(index=False))
    alt = altitude_check(g)
    alt.round(4).to_csv(OUT / "altitude_check.csv", index=False)
    print("\naltitude: one dummy per elevated venue, instead of the continuous term")
    print(alt.round(3).to_string(index=False))

    print("\nsymmetry check: home and away coefficients should sum to zero")
    print(sym[["term", "home_beta", "away_beta", "sum", "sum_se", "t_sum"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    main()
