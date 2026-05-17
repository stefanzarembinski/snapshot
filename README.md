## INSTALLATION

#### Build module
```
$ python -m build
```

#### Install from wheel
```
$ pip install dist\xxx-0.1-py3-none-any.whl
```
#### Uninstall
```
$ pip uninstall xxx
```
#### Install in editable mode
```
$ pip install -e .
```
## IN/OUT

- generate_inputs_and_outputs()                                       -> tuple[list[tuple[float, list[float], int]], list[tuple[float, float, int]], int]
- evaluate_outputs_utilization(outputs_predicted, outputs_ideal)      -> float
- bridge.add_timeshot(timeshot)                                       -> tuple[list[float], Monotonic]
- trading_decision(scalar)                                            -> tuple[Position, int, int]:
