import os
import pickle
import random
import pandas as pd
import mplfinance as mpf
from datetime import datetime
# from enum import StrEnum
import enum
class StrEnum(str, enum.Enum):
    pass

class Side(StrEnum):
    ASK = 'ASK'
    BID = 'BID'

class Monotonic(StrEnum):
    ASC = 'ASC'
    DSC = 'DSC'

class Direction(StrEnum):
    BWD = 'BWD'
    FWD = 'FWD'

class Position(StrEnum):
    L = 'L'
    S = 'S'

class SnapshotOverflowError(ValueError):
    def __init__(self, message, horizon):
        super().__init__(message)
        self.horizon = horizon


CHARTS_DIR = './charts'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
PIPETTE_SCALE = 100000
SIDE = Side.ASK
    

def format_candle(candle) -> str:
    return '[' + ', '.join(f'{v:.5f}' for v in candle) + ']'

def format_timeshot(timeshot) -> str:
    timestamp, (ask, bid), _, ordinal = timeshot
    when = datetime.fromtimestamp(timestamp).strftime(DATE_FORMAT)
    return (f'  #{ordinal} {when}  '
            f'ask={format_candle(ask)}  bid={format_candle(bid)}')

def format_snapshot(snapshot) -> str:
    return '[' + ', '.join(f'{d:>4}' for d in snapshot) + ']'

def format_decorated_array(decorated_array):
    timestamp, array, ordinal = decorated_array
    when = datetime.fromtimestamp(timestamp).strftime(DATE_FORMAT)
    if isinstance(array, list):
        arr = '[' + ', '.join(f'{v:>7.4f}' for v in array) + ']'
    else:
        arr = f'{array:>7.4f}'
    return f'#{ordinal}\t{when} array={arr}'

def validate_snapshot(snapshot) -> None:
    seen_zero = False
    prev_sign = 0
    for v in snapshot:
        if v == 0:
            seen_zero = True
            continue
        if seen_zero:
            raise ValueError(f'Invalid snapshot: non-zero value after zero in {snapshot}')
        curr_sign = 1 if v > 0 else -1
        if curr_sign == prev_sign:
            raise ValueError(f'Invalid snapshot: consecutive same-signed values in {snapshot}')
        prev_sign = curr_sign

def retrieve_candle(timeshot) -> list[float]:
    if SIDE == Side.ASK:
        _, (candle, _), _, _ = timeshot
    else:
        _, (_, candle), _, _ = timeshot
    return candle

def retrieve_dataframe(timeshots, idx, horizon_past, horizon_future) -> pd.DataFrame:
    rows = []
    start = max(idx - horizon_past, 0)
    end = min(idx + horizon_future, len(timeshots) - 1)
    for j in range(start, end + 1):
        timestamp, (_, _), _, _ = timeshots[j]
        candle = retrieve_candle(timeshots[j])
        rows.append({
            'timestamp': datetime.fromtimestamp(timestamp),
            'Open': candle[0], 'High': candle[1], 'Low': candle[2], 'Close': candle[3],
        })
    return pd.DataFrame(rows).set_index('timestamp').sort_index()

def retrieve_reference_level(timeshot) -> float:
    return retrieve_candle(timeshot)[3]

def retrieve_spans(timeshot, reference_pipettes) -> tuple[int, int]:
    candle = retrieve_candle(timeshot)
    upward_span = convert_to_pipettes(candle[1]) - reference_pipettes
    downward_span = convert_to_pipettes(candle[2]) - reference_pipettes
    return upward_span, downward_span

def convert_to_pipettes(level) -> int:
    return round(level * PIPETTE_SCALE)

def convert_to_array(snapshot, vertical_range) -> list[float]:
    return [round(max(-1, min(1, s / vertical_range)), 4) for s in snapshot]

def decorate_array(array, timeshot) -> tuple[float, list[float] | float, int]:
    return (timeshot[0], array, timeshot[3])

def reduce_array(array) -> float:
        last_non_zero = 0
        for v in reversed(array):
            if v != 0:
                last_non_zero = v
                break
        if last_non_zero != 0:
            positive_sum = sum(v for v in array if v > 0)
            negative_sum = sum(v for v in array if v < 0)
            if last_non_zero > 0:
                return 1 - abs(negative_sum)
            if last_non_zero < 0:
                return abs(positive_sum) - 1
        raise 0

def randomize_outputs(outputs) -> list[tuple[float, float, int]]:
    all_outputs = range(len(outputs))
    randomized_outputs = []
    for output in outputs:
        timestamp, _, idx = output
        _, scalar, _ = outputs[random.choice(all_outputs)]
        randomized_outputs.append((timestamp, scalar, idx))
    return randomized_outputs


class Bridge:
    def __init__(self, timeshots, monotonic_duration, vertical_range, snapshot_size, adversity, sltp):
        self.timeshots = timeshots
        self.monotonic_duration = monotonic_duration
        self.vertical_range = vertical_range
        self.snapshot_size = snapshot_size
        self.adversity = adversity
        self.sltp = sltp

        print(f'\nReceived {len(self.timeshots )} timeshots')

        self.decision_points = {}
        for monotonic in Monotonic:
            self.decision_points[monotonic] = self.generate_decision_points(monotonic)
            print(f'{monotonic} decision points: {len(self.decision_points[monotonic])} found')

    def generate_decision_points(self, monotonic) -> list[int]:
        def is_ascending(prev_candle, curr_candle):
            return curr_candle[2] >= prev_candle[2]
        def is_descending(prev_candle, curr_candle):
            return curr_candle[1] <= prev_candle[1]
        if monotonic == Monotonic.ASC:
            ordered = is_ascending
        elif monotonic == Monotonic.DSC:
            ordered = is_descending
        points = []
        streak = 0
        skip = False
        for i in range(1, len(self.timeshots)):
            if skip:
                streak = 0
                skip = False
                continue
            if ordered(retrieve_candle(self.timeshots[i - 1]), retrieve_candle(self.timeshots[i])):
                streak += 1
                if streak >= self.monotonic_duration:
                    points.append(i)
                    streak = 0
                    skip = True
            else:
                streak = 0
        return points

    def is_decision_point(self, idx) -> Monotonic | None:
        if idx < self.monotonic_duration:
            return None
        if max(self.decision_points[Monotonic.ASC] + self.decision_points[Monotonic.DSC]) >= idx - self.monotonic_duration:
            return None
        candles = [retrieve_candle(self.timeshots[j]) for j in range(idx - self.monotonic_duration, idx + 1)]
        if all(candles[k][2] >= candles[k - 1][2] for k in range(1, len(candles))):
            return Monotonic.ASC
        if all(candles[k][1] <= candles[k - 1][1] for k in range(1, len(candles))):
            return Monotonic.DSC
        return None

    def print_sample_of_decision_points(self, monotonic, n=3) -> None:
        print()
        os.makedirs(CHARTS_DIR, exist_ok=True)
        for idx in self.decision_points[monotonic][:n]:
            ordinal = self.timeshots[idx][3]
            print(f'\n{monotonic} decision point at ordinal {ordinal}:')
            print(f'  Preceding {self.monotonic_duration} timeshot(s):')
            for j in range(idx - self.monotonic_duration, idx):
                print(format_timeshot(self.timeshots[j]))
            print(f'  {monotonic} decision point:')
            print(format_timeshot(self.timeshots[idx]))
            horizons = {}
            for direction in Direction:
                try:
                    snapshot, array, horizon = self.generate_snapshot(idx, direction)
                    horizons[direction] = horizon
                    print(f'  {direction} snapshot (vertical_range={self.vertical_range[direction]}, snapshot_size={self.snapshot_size[direction]}, horizon={f'{horizon:>3}'}): '
                        f'{format_snapshot(snapshot)}')
                    print(f'  {direction} array: {format_decorated_array(decorate_array(array, self.timeshots[idx]))}')
                except SnapshotOverflowError as e:
                    horizons[direction] = e.horizon
                    print(f'  {direction} snapshot (vertical_range={self.vertical_range[direction]}, snapshot_size={self.snapshot_size[direction]}, horizon={e.horizon}): '
                        f'ERROR — {e}')
            self.print_decision_point_chart(idx, horizons[Direction.BWD], horizons[Direction.FWD], monotonic.value)
        print()

    def print_decision_point_chart(self, idx, horizon_past, horizon_future, prefix) -> None:
        ohlc = retrieve_dataframe(self.timeshots, idx, horizon_past, horizon_future)
        ordinal = self.timeshots[idx][3]
        timestamp = datetime.fromtimestamp(self.timeshots[idx][0])
        filename = os.path.join(CHARTS_DIR, f'{prefix}_@_{ordinal}.png')
        mpf.plot(
            ohlc,
            type='ohlc',
            style='mike',
            title=f'{prefix} decision point #{ordinal} (side={SIDE.value}, past={horizon_past}, future={horizon_future})',
            ylabel='',
            volume=False,
            vlines=dict(vlines=[timestamp], colors='magenta', linewidths=0.1, alpha=0.7),
            hlines=dict(hlines=[retrieve_reference_level(self.timeshots[idx])], colors='magenta', linewidths=0.1, alpha=0.7),
            savefig=dict(fname=filename, dpi=300, bbox_inches='tight'),
            warn_too_much_data=999
        )
        print(f'  Saved {filename}')

    def generate_snapshot(self, idx, direction) -> tuple[list[int], list[float] | float, int]:
        reference_level = convert_to_pipettes(retrieve_reference_level(self.timeshots[idx]))
        max_span, min_span = retrieve_spans(self.timeshots[idx], reference_level)
        delta = 0
        deltas = []
        horizon = 0

        if direction == Direction.BWD:
            indices = range(idx - 1, -1, -1)
        elif direction == Direction.FWD:
            indices = range(idx + 1, len(self.timeshots))

        for j in indices:
            horizon += 1
            upward_span, downward_span = retrieve_spans(self.timeshots[j], reference_level)

            if delta >= 0:
                if upward_span > max_span + delta:
                    delta = upward_span - max_span
                    if upward_span >= self.vertical_range[direction]:
                        deltas.append(delta)
                        break
                elif delta > 0 and downward_span < min_span:
                    max_span += delta
                    deltas.append(delta)
                    delta = downward_span - min_span

            if delta <= 0:
                if downward_span < min_span + delta:
                    delta = downward_span - min_span
                    if downward_span <= -self.vertical_range[direction]:
                        deltas.append(delta)
                        break
                elif delta < 0 and upward_span > max_span:
                    min_span += delta
                    deltas.append(delta)
                    delta = upward_span - max_span

        if len(deltas) > self.snapshot_size[direction]:
            raise SnapshotOverflowError(
                f'Snapshot exceeds snapshot_size={self.snapshot_size[direction]}: produced {len(deltas)} deltas',
                horizon,
            )

        snapshot = deltas + [0] * (self.snapshot_size[direction] - len(deltas))
        validate_snapshot(snapshot)
        array = convert_to_array(snapshot, self.vertical_range[direction])
        if direction == Direction.FWD:
            return snapshot, reduce_array(array), horizon
        return snapshot, array, horizon

    def generate_inputs_and_outputs(self) -> tuple[list[tuple[float, list[float], int]], list[tuple[float, float, int]], int]:
        inputs, outputs, skipped = [], [], 0
        for idx in sorted(set(self.decision_points[Monotonic.ASC] + self.decision_points[Monotonic.DSC])):
            try:
                _, array, _ = self.generate_snapshot(idx, Direction.BWD)
                inputs.append(decorate_array(array, self.timeshots[idx]))
                _, array, _ = self.generate_snapshot(idx, Direction.FWD)
                outputs.append(decorate_array(array, self.timeshots[idx]))
            except SnapshotOverflowError:
                skipped += 1
        if skipped:
            print(f'Skipped {skipped} decision point(s) due to snapshot overflow')
        return inputs, outputs, skipped

    def trading_decision(self, scalar) -> tuple[Position, int, int]:
        stop_loss = self.sltp
        take_profit = self.sltp
        if scalar >= 1.0 * self.adversity:
            return Position.L, stop_loss, take_profit
        if scalar >= 0.5 * self.adversity:
            return Position.L, 1.5 * stop_loss, take_profit
        if scalar <= -1.0 * self.adversity:
            return Position.S, stop_loss, take_profit
        if scalar <= -0.5 * self.adversity:
            return Position.S, 1.5 * stop_loss, take_profit
        raise ValueError(f'No trading decision could be made for value: {scalar}')
    
    def financial_simulation(self, outputs, verbose=False) -> float:
        total_outcome = 0
        opened = {Position.L: 0, Position.S: 0}
        take_profit_count = 0
        stop_loss_count = 0
        unresolved = 0
        
        for output in outputs:
            _, scalar, idx = output
            try:
                position, stop_loss, take_profit = self.trading_decision(scalar)
            except ValueError:
                continue
            opened[position] += 1
            _, (ask_candle, bid_candle), _, _ = self.timeshots[idx]
            if position == Position.L:
                entry = convert_to_pipettes(ask_candle[3])
                stop_loss_level = entry - stop_loss
                take_profit_level = entry + take_profit
            elif position == Position.S:
                entry = convert_to_pipettes(bid_candle[3])
                stop_loss_level = entry + stop_loss
                take_profit_level = entry - take_profit

            closed = False
            for j in range(idx + 1, len(self.timeshots)):
                _, (next_ask, next_bid), _, _ = self.timeshots[j]
                if position == Position.L:
                    bid_high = convert_to_pipettes(next_bid[1])
                    bid_low = convert_to_pipettes(next_bid[2])
                    if bid_high >= take_profit_level:
                        total_outcome += take_profit
                        take_profit_count += 1
                        closed = True
                        break
                    if bid_low <= stop_loss_level:
                        total_outcome -= stop_loss
                        stop_loss_count += 1
                        closed = True
                        break
                elif position == Position.S:
                    ask_high = convert_to_pipettes(next_ask[1])
                    ask_low = convert_to_pipettes(next_ask[2])
                    if ask_low <= take_profit_level:
                        total_outcome += take_profit
                        take_profit_count += 1
                        closed = True
                        break
                    if ask_high >= stop_loss_level:
                        total_outcome -= stop_loss
                        stop_loss_count += 1
                        closed = True
                        break
            if not closed:
                unresolved += 1

        if verbose:
            print()
            print(f'Opened positions: L={opened[Position.L]}, S={opened[Position.S]}')
            print(f'Closed by take-profit: {take_profit_count}')
            print(f'Closed by stop-loss: {stop_loss_count}')
            if unresolved:
                print(f'Unresolved positions (no SL/TP within timeshots): {unresolved}')
            print(f'Total outcome: {total_outcome} pipettes')
        return total_outcome

    def evaluate_outputs_nonrandomness(self, outputs_predicted, outputs_ideal, n=100, verbose=False) -> float:
        outcome_randomized = 0
        for _ in range(n):
            outcome_randomized += self.financial_simulation(randomize_outputs(outputs_ideal))

        outcome_predicted = self.financial_simulation(outputs_predicted)
        outcome_ideal = self.financial_simulation(outputs_ideal)

        nonrandomness = max(0, 1 - ((outcome_ideal - outcome_predicted) / (outcome_ideal - outcome_randomized / n)))
        
        if verbose:
            print(f'\nEvaluation of predicted outputs against ideal outputs:')
            print(f'  Non-randomness:\t{nonrandomness:.2f} (0.00 is bad, 1.00 is ideal)')

        return nonrandomness
    
    def evaluate_outputs_utilization(self, outputs_predicted, outputs_ideal, verbose=False) -> float:
        outcome_predicted = self.financial_simulation(outputs_predicted)
        outcome_ideal = self.financial_simulation(outputs_ideal)

        utilization = max(0, outcome_predicted / outcome_ideal)
        
        if verbose:
            print(f'\nEvaluation of predicted outputs against ideal outputs:')
            print(f'  Utilization:\t\t{utilization:.2f} (0.00 is bad, 1.00 is ideal)')

        return utilization

    def add_timeshot(self, timeshot) -> tuple[list[float], Monotonic]:
        self.timeshots.append(timeshot)
        idx = len(self.timeshots) - 1
        monotonic = self.is_decision_point(idx)
        if monotonic is None:
            raise ValueError(f'Index {idx} is not a decision point')
        self.decision_points[monotonic].append(idx)
        _, array, _ = self.generate_snapshot(idx, Direction.BWD)
        return array, monotonic


def main(monotonic_duration=10, vertical_range={Direction.BWD: 150, Direction.FWD: 100}, snapshot_size={Direction.BWD: 12, Direction.FWD: 10}, adversity=0.5, sltp=90):

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
    

    TIMESHOTS_DIR = './timeshots'
    TIMESHOTS_FILE = 'timeshots.pkl'
    DATA_DIR = '../data'
    FILE_PREFIX = 'xxx'
    INPUTS_TRAIN_FILE = 'inputs_train.pkl'
    INPUTS_VALID_FILE = 'inputs_valid.pkl'
    OUTPUTS_TRAIN_FILE = 'outputs_train.pkl'
    OUTPUTS_VALID_FILE = 'outputs_valid.pkl'
    TRAIN_VS_VALID = 0.8


    # ############################################################################
    # Class initialization
    # ############################################################################
    with open(os.path.join(TIMESHOTS_DIR, TIMESHOTS_FILE), 'rb') as file:
        timeshots = pickle.load(file)
    bridge = Bridge(timeshots, monotonic_duration, vertical_range, snapshot_size, adversity, sltp)
    

    # ############################################################################
    # Generating inputs and outputs
    # ############################################################################
    inputs, outputs, _ = bridge.generate_inputs_and_outputs()

    assert len(inputs) == len(outputs), 'Mismatched number of inputs and outputs'

    cutoff = round(len(inputs) * TRAIN_VS_VALID)
    inputs_train = inputs[:cutoff]
    inputs_valid = inputs[cutoff:]
    outputs_train = outputs[:cutoff]
    outputs_valid = outputs[cutoff:]

    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{INPUTS_TRAIN_FILE}'), 'wb') as f:
        pickle.dump(inputs_train, f)
    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{INPUTS_VALID_FILE}'), 'wb') as f:
        pickle.dump(inputs_valid, f)
    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{OUTPUTS_TRAIN_FILE}'), 'wb') as f:
        pickle.dump(outputs_train, f)
    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{OUTPUTS_VALID_FILE}'), 'wb') as f:
        pickle.dump(outputs_valid, f)

    print(f'Saved {len(inputs_train)} input samples to {FILE_PREFIX}_{INPUTS_TRAIN_FILE}')
    print(f'Saved {len(inputs_valid)} input samples to {FILE_PREFIX}_{INPUTS_VALID_FILE}')
    print(f'Saved {len(outputs_train)} output samples to {FILE_PREFIX}_{OUTPUTS_TRAIN_FILE}')
    print(f'Saved {len(outputs_valid)} output samples to {FILE_PREFIX}_{OUTPUTS_VALID_FILE}')


    # ############################################################################
    # Generating financial evaluation for a list of outputs
    # ############################################################################
    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{OUTPUTS_TRAIN_FILE}'), 'rb') as file:
        outputs_train = pickle.load(file)
    bridge.financial_simulation(outputs_train, verbose=True)
    bridge.evaluate_outputs_utilization(outputs_train, outputs_train, verbose=True)

    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{OUTPUTS_VALID_FILE}'), 'rb') as file:
        outputs_valid = pickle.load(file)
    bridge.financial_simulation(outputs_valid, verbose=True)
    bridge.evaluate_outputs_utilization(outputs_valid, outputs_valid, verbose=True)


    # ############################################################################
    # Generating a new input array from the current timeshot
    # ############################################################################
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
    with open(os.path.join(DATA_DIR, f'{FILE_PREFIX}_{OUTPUTS_VALID_FILE}'), 'rb') as file:
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
