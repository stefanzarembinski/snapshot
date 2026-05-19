import random
import pandas as pd
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


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
PIPETTE_SCALE = 100000
DEFAULT_SIDE = Side.ASK


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
    if DEFAULT_SIDE == Side.ASK:
        _, (candle, _), _, _ = timeshot
    elif DEFAULT_SIDE == Side.BID:
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
