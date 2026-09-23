# Method notes

What the README leaves out: the specification choices, the things that did not
work, and where I think this is thin.

## Why fixed effects rather than a rating system

The obvious alternative is to build a team rating (an SRS, a Pythagorean
expectation, an Elo) and then regress residuals on schedule variables. That
works, but it makes the schedule terms depend on how well the rating system
happened to fit, and it introduces a generated-regressor problem in the standard
errors that nobody ever corrects for.

Estimating team strength and schedule effects in the same regression avoids
both. Team-season effects and schedule terms are identified jointly, and the
standard errors come out of the same covariance matrix.

The cost is a 619-column design matrix, which for 23,838 games is a rounding
error on a laptop.

## Why differenced schedule terms

The restriction is that a burden is worth the same in absolute value to whoever
is carrying it: the home team on a back-to-back loses what the away team on a
back-to-back loses.

That is testable. `symmetry_test()` fits home and away burdens as separate
coefficients and reports their sum, which the restriction says should be zero:

| Term | Home | Away | Sum | t on the sum |
|---|---|---|---|---|
| Back-to-back | −0.97 | +2.08 | +1.11 | 1.72 |
| One day off | +0.43 | +0.16 | +0.58 | 0.98 |
| Two days off | +0.39 | +0.26 | +0.65 | 1.05 |
| Miles (thousands) | +0.39 | −0.27 | +0.12 | 0.30 |
| Time zones | −0.46 | +0.24 | −0.22 | −0.77 |
| Games in past week | −0.41 | +0.31 | −0.10 | −0.49 |
| Altitude | −0.38 | +0.54 | +0.16 | 0.30 |
| Nth road game | −0.00 | −0.12 | −0.12 | −1.76 |

Nothing rejects at conventional levels. The back-to-back row is the closest, and
its direction is worth noting: it hints that a back-to-back may hurt the home
team slightly less than the away team, which is plausible — the home team slept
in its own bed — but at t = 1.7 across twenty seasons it is not something to
build a rotation on.

## What did not work

**Continuous altitude.** Covered in the README. The per-venue fit is in
`output/altitude_check.csv`. The short version: Denver and Salt Lake City show
the same bonus despite a thousand feet between them, and nothing near a thousand
feet shows anything, so a linear term in feet is imposing a shape the data does
not have.

**Direction of time-zone travel.** I fit eastward and westward shifts separately,
expecting the westward-to-eastward direction (losing hours, playing on a body
clock that thinks it is later) to be worse. The two coefficients were not
distinguishable, so the model keeps the absolute value. With a season of games
per team and a maximum of three zones, there is not enough variation to resolve
the asymmetry that the sleep-science literature would predict.

**Road trip length.** The Nth-straight-road-game term comes out slightly
*positive* (+0.11, t = 1.8). I do not believe road trips help. The likeliest
explanation is that this term is picking up something about which teams take long
trips and when — the annual rodeo road trip in San Antonio, western swings
scheduled around building conflicts — that the team-season effect cannot absorb
because it varies within the season. It is kept in the model as a control and I
would not quote it as a finding.

**Attendance.** The schedule files carry it. It is close to capacity for most
games in most seasons, so there is almost no variation to use, and what variation
exists is a function of team quality, which the fixed effects have already taken.

## Possessions

The standard estimator: FGA + 0.44×FTA − OREB + TOV, averaged across the two
teams because a game's possession count is shared to within one.

The 0.44 is a league-average guess at what fraction of free throw attempts end a
possession. Over a full game the error averages out to well under a possession.
It would not be acceptable at the level of a stint or a quarter, and this
project never uses it at that level.

An alternative is to count possessions directly from the play-by-play. That is
more accurate and it costs the twenty-season sample: the play-by-play mirror is
missing games in several seasons, while the box scores are essentially complete.
For a question about the *calendar*, having every game matters more than having
exact possessions, so this project takes the box score and its sibling project on
plus-minus takes the log.

## Where I think this is thin

**Rest is measured, load is not.** Days between games is a proxy for how tired a
team is. Minutes played, overtime, blowouts that emptied the bench, and who
actually traveled are all invisible here. A team coming off a 25-point win with
its starters resting the fourth quarter is not the same as one coming off double
overtime, and this model calls them identical.

**The back-to-back coefficient is a treated effect.** Teams already manage
back-to-backs — that is what load management is. So −1.52 is what remains after
the mitigation, and it will shrink further as teams get better at it, which means
this number is not stable across the sample and I have not tested whether it
drifts.

**Selection into rest.** A team's rest is set by the schedule maker, which is
close to exogenous. Which players take that rest is not. The model cannot
separate "the team is tired" from "the team sat two starters", and those have
opposite implications for what a front office should do about it.

**Two buildings.** The altitude finding rests on Denver and Salt Lake City. It is
the largest coefficient in the model and it has the thinnest identification, and
those two facts belong in the same sentence every time it is quoted.
