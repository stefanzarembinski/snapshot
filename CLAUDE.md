### Folder structure
- Python scripts are located in the "src" folder
- Input and output data is located in the "data" folder
- Generated charts are stored in the "charts" folder

Do not try to read or access files in the following locations:
- inside the ".internal" folder
- outside the working directory, i.e. /media/dataphora/kingstone/Workspaces/FX/snapshot

### Goal
This project aims to generate input data which will be utilized for machine learning.

### Currency trading
A candlestick is a vector of 4 values describing the various price levels within a given timestamp:
- open (i.e. the initial level recorded within a given timestamp)
- high (i.e. the highest level within a given timestamp)
- low (i.e. the lowest level within a given timestamp)
- close (i.e. the last level recorded within a given timestamp)

There are 2 sets of levels for prices in currency trading:
- "Ask" side is applicable when entering a long position, i.e. buying EUR against USD
- "Bid" side is applicable when entering a short position, i.e. selling EUR against USD

Price levels are usually expressed in floating point numbers.
However, spans between 2 different price levels (or increments of price levels) are usually expressed in "pipettes", which is the 5-th decimal place of a price quote, e.g. an increment 0.00085 translates into 85 pipettes.

There are 3 possible positions in currency trading:
- Long (denoted as "L") which brings a profit if the price goes up or a loss if the price goes down
- Short (denoted as "S") which brings a profit if the price goes down or a loss if the price goes up
- Neutral (denoted as "N") which brings neither profit nor loss, no matter how the price changes

### Timeshots
Timeshot is a custom data structure containing a timestamp and corresponding numeric data.
Timeshots are used to store the history of exchange rates for a currency pair (e.g. EUR/USD).

Each timeshot has the following structure:
- timestamp (the Unix epoch)
- tuple with 2 items inside of it: the first item describes a candlestick for the ask side, whereas the second item describes a candlestick for the bid side 
- transaction volume
- ordinal number

Here is an example of a single timeshot:
(1735768800.0, ([1.03591, 1.03591, 1.03585, 1.03585], [1.03503, 1.03514, 1.03503, 1.03514]), 5.94, 12)

And here is the corresponding data structure:
(timestamp, [ask-open, ask-high, ask-low, ask-close], [bid-open, bid-high, bid-low, bid-close], volume, ordinal)

As described above, each timeshot contains 2 candlesticks (i.e. ask-side candlestick and bid-side candlestick), but the ask-side candlestick is the main one. So unless stated otherwise, whenever we refer to the timeshot's candlestick, we mean the ask-side candlestick.

### Decision points
Timeshot "A" ascends the preceding timeshot "B" when the low level in the candlestick of timeshot "A" is equal or higher than the low level in the candlestick of timeshot "B".
Timeshot "A" descends the preceding timeshot "B" when the high level in the candlestick of timeshot "A" is equal or lower than the high level in the candlestick of timeshot "B".

"Sequence of ascending timeshots" is a sequence of timeshots where each timeshot ascends the previous one.
"Sequence of descending timeshots" is a sequence of timeshots where each timeshot descends the previous one.

Let "monotonic_duration" (denoted as M) be an arbitrary parameter (positive integer), e.g. 10.

"ASC decision point" is a timeshot that meets the following conditions:
- when joined with M previous timeshots it forms a sequence of ascending timeshots
- all timeshots in the sequence of ascending timeshots are unique, i.e. they do not participate in a sequence of ascending timeshots belonging to another "ASC decision point"

"DSC decision point" is a timeshot that meets the following conditions:
- when joined with M previous timeshots it forms a sequence of descending timeshots
- all timeshots in the sequence of descending timeshots are unique, i.e. they do not participate in a sequence of descending timeshots belonging to another "DSC decision point"

### Snapshots
Snapshot is the outcome of compressing information contained in a sequence of timeshots.

The compression discards all information except for the changes in the highest and lowest levels observed in a sequence of timeshots.

As a result of the compression, a snapshot is expressed as a fixed-size array of alternatively signed integers, optionally ending with a sequence of zeros, e.g.
[8, -12, 24, -69, 17, -19, 0, 0, 0, 0]

Positive values in the snapshot array indicate an increment in the observed highest levels, whereas negative values indicate an increment in the observed lowest levels.

Snapshot is always associated with a particular decision point timeshot, as its candlestick provides the reference level for analyzing the snapshot's highest and lowest levels.

There are two types of snapshots:
- A "backward-looking" snapshot is based on a sequence of timeshots preceding the decision point and its goal is to describe what happened prior to the decision point. It is the basis for generating inputs in machine learning.
- A "forward-looking" snapshot is based on a sequence of timeshots following the decision point and its goal is to describe what happened after the decision point. It is the basis for generating target outputs in machine learning.

Snapshot is dependent on 2 parameters:
- "vertical range" (positive integer, denoted in pipettes), i.e. the maximum distance from the reference level allowed in a snapshot, e.g. 160, 
- "snapshot size" (positive integer), i.e. the fixed size of the snapshot array, e.g. 10

### Inputs
Input is always associated with a particular decision point and it is derived from a "backward-looking" snapshot generated for this decision point.

An input consists of a timestamp (derived from the decision point timestamp), a fixed size array, and an ordinal (derived from the decision point ordinal).

An input's array is calculated by dividing the snapshot's integers by the value of the snapshot's "vertical range", i.e. [s / vertical_range for s in snapshot].

Here is an example of a single input:
(1735768800.0, [0.0466, -0.1266, 0.4400, -0.3666, 0.5866, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000], 12)

And here is the corresponding data structure:
(timestamp, array, ordinal)

### Outputs
Output is always associated with a particular decision point.

There are 2 types of outputs:
- A "target" output, which is the desired output derived from the "forward-looking" snapshot
- A "actual" output, which is the outcome of predictions made by machine learning

An output consists of a timestamp (derived from the decision point timestamp), a fixed size array, and an ordinal (derived from the decision point ordinal).

In case of a "target" output, its array is calculated by dividing the snapshot's integers by the value of the snapshot's "vertical range", i.e. [s / vertical_range for s in snapshot].

Here is an example of a single output:
(1735768800.0, [0.0466, -0.3456, 0.1218, -0.4732, 0.0178, 0.0000, 0.0000], 19)

And here is the corresponding data structure:
(timestamp, array, ordinal)

### Trading decisions
Outputs (both "target" and "actual") need to be translated into one of the following trading decisions:
- open an "L" position
- open an "S" position
- do nothing, i.e. keep the existing "N" position

Let "adversity" (denoted as A) be an arbitrary parameter ranging from 0 to 1, e.g. 0.5

Here is how a trading decision is determined from an output:
- "L" if the output's last non-zero value is positive and the absolute value of the sum of all negative values is less or equal the value of A
- "S" if the output's last non-zero value is negative and the absolute value of the sum of all positive values is less or equal the value of A
- "N" otherwise

### Financial simulation
To avoid discrepancies related to rounding floating numbers, all financial calculations should be performed using pipettes.

Opening a position ("L" or "S") is always based on a trading decision.

Here are the price levels used for opening a position:
- for "L": the close level (converted to pipettes) from the timeshot's ask-side candle.
- for "S": the close level (converted to pipettes) from the timeshot's bid-side candle.

Closing a position ("L" or "S") is always automatic and it is based on observing a "stop-loss / take-profit" event.

Let "stop-loss / take-profit" (denoted as "SLTP") be an arbitrary parameter (positive integer, denoted in pipettes), e.g. 100.

Based on the value of SLTP, the following levels are derived:
- "stop-loss level" (denoted as "SLL")
- "take-profit level" (denoted as "TPL")

And here is how they are calculated:
- "SLL" for "L" positions: position entry level (in pipettes) - SLTP
- "TPL" for "L" positions: position entry level (in pipettes) + SLTP
- "SLL" for "S" positions: position entry level (in pipettes) + SLTP
- "TPL" for "S" positions: position entry level (in pipettes) - SLTP

An "L" position is closed when either of the following events happens:
- "take-profit" event, i.e. the high level (converted to pipettes) in the current timeshot's bid-side candle is higher or equal "TPL"
- "stop-loss" event, i.e. the low level (converted to pipettes) in the current timeshot's bid-side candle is lower or equal "SLL"

An "S" position is closed when either of the following events happens:
- "take-profit" event, i.e. the low level (converted to pipettes) in the current timeshot's ask-side candle is lower or equal "TPL"
- "stop-loss" event, i.e. the high level (converted to pipettes) in the current timeshot's ask-side candle is higher or equal "SLL"

Here is how financial outcome (in pipettes) is calculated for a single position being opened and then closed:
- profit equal to "SLTP" whenever a position is closed by "take-profit" event
- loss equal to "SLTP" whenever a position is closed by "stop-loss" event