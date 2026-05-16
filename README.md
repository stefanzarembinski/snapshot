## INSTALLATION

### Add the package to the Python path

To build wheel:

PS .... snapshot> python -m build

To install from wheel:

PS .... snapshot> pip install dist\shot-0.1-py3-none-any.whl

To uninstall:

    PS ... > pip uninstall shot

To install in editable mode:

    PS ... > snapshot> pip install -e .

## IN/OUT

in:     timeshots
out:	features file: timestamp, f1, f2, ... ,fn

in:     timeshots
out:	targets file: timestamp, f1, f2, ... ,fm

in:     timeshot
out:	features or None

in:     targets
out:	L | S | N