Create a Python script which will do the following:
1. Load the timeshot history data from the "./data/timeshots.pkl" file
2. Print out the following statistics for the entire timeshot history:
- the start date and end date
- the total number of timeshots
3. Ask the user for the following input (in the '%Y-%m-%d %H:%M:%S' format):
- begin date
- finish date
And then create PNG files containing the following charts:
- candlestick chart for the "ask" side
- candlestick chart for the "bid" side
- line chart for the close value of both "ask" or "bid" sides

---

Improve the "chart.py" script:
1. Add the following statistics:
- the highest and lowest value both ask and bid sides  
- for all 4 candlestick values, include the bid-ask spread: average spread, highest spread, lowest spread

2. Add the following validation after the statistics:
- for all 4 candlestick values (i.e. open, high, low, close), verify that the bid-ask spread is never negative
- verify that the high value is always equal or above any other value in a candlestick
- verify that the low value is always equal or below any other value in a candlestick

3. Store the generated charts in the "charts" folder.

---

Remove statistics and validation from the "chart.py" file and move them to a separate Python script file named "stats.py".

---

Preliminary definitions:
- "pipette" is the 5-th decimal place of a price quote, e.g. the level of 1.03585 translates into 103585 pipettes
- "reference level" is the "close" level in the "ask" candlestick of the decision point timeshot
- "upward span" is the difference (expressed in pipettes) between the "high" level in the "ask" candlestick of a given timeshot and the "reference level" (it's always a positive integer)
- "downward span" is difference (expressed in pipettes) between the "low" level in the "ask" candlestick of a given timeshot and the "reference level" (it's always a negative integer)
- "vertical range" (denoted as V) is the vertical limit (expressed in pipettes) used when generating a snapshot
- "horizontal size" (denoted as H) is the fixed size of the snapshot array

Parameter definitions:
- let V be an arbitrary parameter for the value of "vertical range" , e.g. 200
- let H be an arbitrary parameter for the value of "horizontal size" , e.g. 10

Here is the workflow for generating a snapshot ("backward-looking" or "forward-looking") for a given decision point and a given value of V and H:
1. Establish the initial value for the following variables:
- "max" is initially equal to the "upward span" for the decision point timeshot
- "min" is initially equal to the "downward span" for the decision point timeshot
- "delta" is initially equal to zero
- "deltas" is initially an empty list
2. Starting from the decision point timeshot, iterate backward through the timeshots that precede the decision point timeshot (in case of "backward-looking" snapshot) or iterate forward through the timeshots that follow the decision point timeshot.
3. In each iteration perform the following steps:
- Calculate the value of "upward span" and "downward span" for the current timeshot
- If "delta" is greater or equal zero:
   - if the "upward span" for the current timeshot is greater than the sum of "max" and "delta", then:
     - set "delta" = "upward span" - "max"
     - if the value of "upward span" is greater or equal V, then insert the current value of delta to the "deltas" list and exit the iteration loop
   - if "delta" is greater than zero and the "downward span" for the current timeshot is less the value of "min", then:
     - insert the current value of delta to the "deltas" list,
     - set "delta" = "downward span" - "min",
     - and then set "min" = "downward span"
- If "delta" is less or equal zero:
   - if the "downward span" for the current timeshot is less than the sum of "min" and "delta", then:
     - set "delta" = "downward span" - "min"
     - if absolute value of "downward span" is greater or equal V, then insert the current value of delta to the "deltas" list and exit the iteration loop
   - if "delta" is less than zero and the "upward span" for the current timeshot is greater the value of "max", then:
     - insert the current value of delta to the "deltas" list,
     - set "delta" = "upward span" - "max",
     - and then set "max" = "upward span"
4. The resulting snapshot array should be populated with the values stored in the "deltas" list:
- in case the length of the "deltas" list is smaller than H, the array should be patched with zeros
- in case the length of the "deltas" list is exceeds H, return an error

Create a Python script named "dataphora.py" which will do the following:
1. Load the timeshot history data from the "./data/timeshots.pkl" file
2. Ask the user for the following input: the value of parameter N
3. Iterate along the timeshot history and using the value of parameter N build 2 lists:
- list of all ASC decision points
- list of all DSC decision points
4. Print the first 3 timeshots in each list, and for each decision point timeshot also print N proceeding timeshots.

---

Improve the "dataphora.py" script:
- when printing out timeshots make sure the OHLC values are uniformly formatted with 5 decimal points
- do not print out the timeshot volume

---

Improve the "dataphora.py" script:
- when printing out the decision points always label them with the ASC or DSC prefix
- make sure that the decision point timeshot itself meets the condition of sequence of ascending or descending timeshots i.e. it ascends the preceding timeshot in case of "ASC decision point" or it descends the preceding timeshot in case of "DSC decision point"

---

Improve the "dataphora.py" script by adding candlestick charts for the first 3 ASC decision points and the first 3 DSC decision points. Each chart should contain the "ask" candlesticks for the decision point timeshot and the corresponding sequence of ascending or descending timeshots.

---

Improve the "dataphora.py" script by adding the ability to generate snapshots for selected decision points. Then generate snapshots and print the outcome for the first 3 ASC decision points and the first 3 DSC decision points

---

Improve the "dataphora.py" script:
- The "generate_snapshot" method should return not only the snapshot but also an integer called "horizon" calculated as the number of timeshots which were needed to be iterated over before the loop exited.
- Include the snapshot's horizon when printing out the snapshot details.
- When generating a chart for a decision point, make sure it covers N timeshots in the past (counting from the decision point) and M timeshots in the future (counting from the decision point), where N equals to the horizon of the "backward-looking" snapshot and M equals to the horizon of the "forward-looking" snapshot. Also, add a vertical line on the chart to indicate the decision point timeshot.

---

Improve the "dataphora.py" script by introducing default values for the following parameters in the "main" method:
- n = 10
- v = 120
- h = 12
Don't remove the input prompts. Instead keep the prompts while using default values as the suggested input.

---

Improve the "dataphora.py" script:
- Add a new method named "generate_inputs" which will generate inputs (both "feature" input and "target" input) for a decision point.
- Enhance the "print_decision_points" method so that it also prints out inputs (both "feature" and "target") for the first 3 ASC decision points and the first 3 DSC decision points.
- Use this newly created "generate_inputs" method in the "main" method to generate inputs for all the decision points and store the result in the pickle format in the "data" folder. Make sure that "feature" inputs and "target" inputs are saved in two separate files.

---

Improve the "make_input" method in "dataphora.py" script by making sure the values in the input array are always in the (-1, 1) range. If a value in the array exceeds 1, it should be replaced by 1. If a value in the array is below -1, it should be replaced by -1.

---

Improve the "generate_snapshot" method in "dataphora.py" script by adding validation which ensures that the generated snapshot meets the following conditions:
- it contains integers which are alternatively signed, so that the following snapshot is not valid [-1, 1, 1, -1, 1, 0, 0]
- there can be no non-zero integer after the first zero appears, so that the following snapshot is not valid [-1, 1, -1, 0, 1, 0, 0]


---

Improve the "dataphora.py" script by adding in the "Dataphora" class a new method named "is_decision_point" which takes an index of a timeshot ("idx") and returns a boolean indicating if the timeshot is a valid decision point (either ASC decision point or DSC decision point). This method should not rely on the self.decision_points variable. Instead, it should make the judgment based on the preceding sequence of timeshots.

---

Improve the "dataphora.py" script by adding in the "Dataphora" class the following methods:
- A method named "trading_decision" which converts a "target" input into one of the positions, i.e. "L", "S" or "N" 
- A method named "financial_simulation" which creates a financial simulation by iterating through all the decision points and calculating total the outcome (in pipettes) of all trading decisions (derived from the "target" inputs)

---

Improve the "financial_simulation" method in "dataphora.py" script:
- Use StrEnum for handling position, instead of 'L', 'S' and 'N' literals
- Turn the "adversity" and "sltp" arguments into class properties. Also, make sure their values are handled in the "main" method, just like monotonic_duration or vertical_range.

---

Improve the "financial_simulation" method in "dataphora.py" script by adding a boolean parameter called "randomized" which will have the following effect:
- If "randomized" is set to "False" keep the method's workflow as it is now, i.e. we iterate through indices of all decision points and the current "idx" is used both for generating the target input and for setting the timeshot where the position is entered.
- If "randomized" is set to "True" change the workflow so that we still iterate through indices of all decision points but the current "idx" is used only for setting the timeshot where the position is entered while the target input is generated based on a random decision point taken from the list of all existing decision points (both ASC and DSC decision points).