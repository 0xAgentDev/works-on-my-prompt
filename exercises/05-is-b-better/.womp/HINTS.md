# Hints · Is B better?

## Run it more than once
`python3 run.py` repeats the same comparison twenty times. Nothing differs between the runs except which answers the model happened to sample. What does that say about a five-point gap seen once?

## How big is the noise?
One pass is one sample per question. With 60 questions, the gap between two single passes moves by about 13 points in either direction from sampling alone. You are allowed 1,200 calls and the current rule spends 120. Repeat each question, and work with each question's average.

## Say how sure you are
For every question, take B's accuracy minus A's. The mean of those differences is your estimate, and their spread gives its standard error. Roughly the mean plus or minus two standard errors is the interval the estimate has to be read against. Ship only when the whole interval is above zero.

## Find out how often your rule is wrong
`simulate(effect=0.0, seed=s)` builds an experiment in which B is exactly as good as A. Run your rule on a hundred of them and count how often it says ship. Then try `effect=0.1`, and check how often your interval contains `truth(lab)["delta"]`.

## An average can hide a slice
Try `simulate(effect=0.2, slice_effects={"billing": -0.5})`: better overall, far worse on billing. Estimate the difference for each slice, with its own interval, and do not ship while any slice is clearly worse.
