## INSTALLATION

### Add the package to the Python path

To build wheel:

PS .... snapshot> python -m build

To install from wheel:

PS .... snapshot> pip install dist\shot-0.1-py3-none-any.whl

To uninstall:

    PS ... snapshot> pip uninstall shot

To install in editable mode:

    PS ... snapshot> pip install -e .
## IN/OUT

- generate_inputs_and_outputs()                                       -> tuple[list[tuple[float, list[float], int]], list[tuple[float, float, int]], int]
- evaluate_outputs_utilization(outputs_predicted, outputs_ideal)      -> float
- bridge.add_timeshot(timeshot)                                       -> tuple[list[float], Monotonic]
- trading_decision(scalar)                                            -> tuple[Position, int, int]:
