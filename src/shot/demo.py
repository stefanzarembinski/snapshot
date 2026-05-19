import os
import pickle
from shot.utils import *
from shot.bridge import Bridge

TIMESHOTS_FILE = '/media/dataphora/kingstone/Workspaces/FX/snapshot/snapshot-bridge/timeshots/timeshots.pkl'
DATA_DIR = '/media/dataphora/kingstone/Workspaces/FX/snapshot/data'
CHARTS_DIR = '/media/dataphora/kingstone/Workspaces/FX/snapshot/snapshot-bridge/charts'
FILE_NAME_PREFIX = 'xxx'
INPUTS_TRAIN_FILE_NAME = 'inputs_train.pkl'
INPUTS_VALID_FILE_NAME = 'inputs_valid.pkl'
OUTPUTS_TRAIN_FILE_NAME = 'outputs_train.pkl'
OUTPUTS_VALID_FILE_NAME = 'outputs_valid.pkl'
TRAIN_VS_VALID = 0.8

bridge = None

def main(monotonic_duration=10, vertical_range={Direction.BWD: 150, Direction.FWD: 100}, snapshot_size={Direction.BWD: 12, Direction.FWD: 10}, adversity=0.5, sltp=90):

    global bridge

    raw = input(f'Enter the value of parameter Monotonic Duration [{monotonic_duration}]: ').strip()
    monotonic_duration = int(raw) if raw else monotonic_duration
    if monotonic_duration < 1:
        raise SystemExit('Monotonic Duration must be a positive integer.')

    for direction in Direction:
        raw = input(f'Enter the value of parameter Vertical Range (in pipettes) for {direction} [{vertical_range[direction]}]: ').strip()
        vertical_range[direction] = int(raw) if raw else vertical_range[direction]
        if vertical_range[direction] < 1:
            raise SystemExit('Vertical Range must be a positive integer.')

        raw = input(f'Enter the value of parameter Snapshot Size for {direction} [{snapshot_size[direction]}]: ').strip()
        snapshot_size[direction] = int(raw) if raw else snapshot_size[direction]
        if snapshot_size[direction] < 1:
            raise SystemExit('Snapshot Size must be a positive integer.')

    raw = input(f'Enter the value of parameter Adversity [{adversity}]: ').strip()
    adversity = float(raw) if raw else adversity
    if not 0 <= adversity <= 1:
        raise SystemExit('Adversity must be a number between 0 and 1.')

    raw = input(f'Enter the value of parameter SLTP (in pipettes) [{sltp}]: ').strip()
    sltp = int(raw) if raw else sltp
    if sltp < 1:
        raise SystemExit('SLTP must be a positive integer.')
    

    with open(TIMESHOTS_FILE, 'rb') as file:
        timeshots = pickle.load(file)
    bridge = Bridge(timeshots, monotonic_duration, vertical_range, snapshot_size, adversity, sltp)
    

    generate_inputs_and_outputs()
    evaluate_outputs()
    generate_input_array()
    generate_trading_decision()


# ############################################################################
# Generating inputs and outputs
# ############################################################################
def generate_inputs_and_outputs():
    inputs, outputs, _ = bridge.generate_inputs_and_outputs()

    assert len(inputs) == len(outputs), 'Mismatched number of inputs and outputs'

    cutoff = round(len(inputs) * TRAIN_VS_VALID)
    inputs_train = inputs[:cutoff]
    inputs_valid = inputs[cutoff:]
    outputs_train = outputs[:cutoff]
    outputs_valid = outputs[cutoff:]

    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{INPUTS_TRAIN_FILE_NAME}'), 'wb') as f:
        pickle.dump(inputs_train, f)
    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{INPUTS_VALID_FILE_NAME}'), 'wb') as f:
        pickle.dump(inputs_valid, f)
    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{OUTPUTS_TRAIN_FILE_NAME}'), 'wb') as f:
        pickle.dump(outputs_train, f)
    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{OUTPUTS_VALID_FILE_NAME}'), 'wb') as f:
        pickle.dump(outputs_valid, f)

    print(f'Saved {len(inputs_train)} input samples to {FILE_NAME_PREFIX}_{INPUTS_TRAIN_FILE_NAME}')
    print(f'Saved {len(inputs_valid)} input samples to {FILE_NAME_PREFIX}_{INPUTS_VALID_FILE_NAME}')
    print(f'Saved {len(outputs_train)} output samples to {FILE_NAME_PREFIX}_{OUTPUTS_TRAIN_FILE_NAME}')
    print(f'Saved {len(outputs_valid)} output samples to {FILE_NAME_PREFIX}_{OUTPUTS_VALID_FILE_NAME}')


# ############################################################################
# Generating financial evaluation for a list of outputs
# ############################################################################
def evaluate_outputs():
    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{OUTPUTS_TRAIN_FILE_NAME}'), 'rb') as file:
        outputs_train = pickle.load(file)
    bridge.financial_simulation(outputs_train, verbose=True)
    bridge.evaluate_outputs_utilization(outputs_train, outputs_train, verbose=True)

    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{OUTPUTS_VALID_FILE_NAME}'), 'rb') as file:
        outputs_valid = pickle.load(file)
    bridge.financial_simulation(outputs_valid, verbose=True)
    bridge.evaluate_outputs_utilization(outputs_valid, outputs_valid, verbose=True)


# ############################################################################
# Generating a new input array from the current timeshot
# ############################################################################
def generate_input_array():
    with open(TIMESHOTS_FILE, 'rb') as file:
        timeshots = pickle.load(file)
    print(f'\nGenerating input arrays for the last 10k timeshots:')
    for timeshot in list(reversed(timeshots[-10000:-1])):
        try:
            array, monotonic = bridge.add_timeshot(timeshot)
            print(f'Input for {monotonic} decision point: {format_decorated_array(decorate_array(array, timeshot))}')
        except ValueError:
            continue


# ############################################################################
# Generating a new trading decision from the current output scalar
# ############################################################################
def generate_trading_decision():
    with open(os.path.join(DATA_DIR, f'{FILE_NAME_PREFIX}_{OUTPUTS_VALID_FILE_NAME}'), 'rb') as file:
        outputs = pickle.load(file)
    print(f'\nEvaluating trading decisions for the first 10 output scalars:')
    for output in outputs[:10]:
        _, scalar, _ = output
        try:
            position, stop_loss, take_profit = bridge.trading_decision(scalar)
        except ValueError:
            print(f'No trading decision')
            continue
        print(f'Trading decision: {position}, stop-loss: {stop_loss}, take-profit: {take_profit}')


if __name__ == '__main__':
    main()