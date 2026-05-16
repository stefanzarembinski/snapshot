import pickle
from datetime import datetime

import pandas as pd

DATA_FILE = './data/timeshots.pkl'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
OHLC = ('open', 'high', 'low', 'close')


def load_timeshots(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def to_dataframe(timeshots):
    rows = []
    for ts, (ask, bid), volume, _ in timeshots:
        rows.append({
            'timestamp': datetime.fromtimestamp(ts),
            'ask_open': ask[0], 'ask_high': ask[1], 'ask_low': ask[2], 'ask_close': ask[3],
            'bid_open': bid[0], 'bid_high': bid[1], 'bid_low': bid[2], 'bid_close': bid[3],
            'volume': volume,
        })
    df = pd.DataFrame(rows).set_index('timestamp').sort_index()
    return df


def statistics(df):
    print(f'Start date:        {df.index.min().strftime(DATE_FORMAT)}')
    print(f'End date:          {df.index.max().strftime(DATE_FORMAT)}')
    print(f'Total timeshots:   {len(df)}')
    print()

    ask_cols = [f'ask_{c}' for c in OHLC]
    bid_cols = [f'bid_{c}' for c in OHLC]
    print(f'Ask highest: {df[ask_cols].values.max():.5f}')
    print(f'Ask lowest:  {df[ask_cols].values.min():.5f}')
    print(f'Bid highest: {df[bid_cols].values.max():.5f}')
    print(f'Bid lowest:  {df[bid_cols].values.min():.5f}')
    print()

    print('Bid-ask spread per candlestick value:')
    print(f"  {'value':<6} {'avg':>12} {'highest':>12} {'lowest':>12}")
    for c in OHLC:
        spread = df[f'ask_{c}'] - df[f'bid_{c}']
        print(f'  {c:<6} {spread.mean():>12.6f} {spread.max():>12.6f} {spread.min():>12.6f}')
    print()


def validate(df):
    errors = []

    for c in OHLC:
        spread = df[f'ask_{c}'] - df[f'bid_{c}']
        negative = spread[spread < 0]
        if not negative.empty:
            errors.append(f'Negative bid-ask spread on {c}: {len(negative)} timeshot(s); '
                          f'first at {negative.index[0]} (spread={negative.iloc[0]:.6f})')

    for side in ('ask', 'bid'):
        high = df[f'{side}_high']
        low = df[f'{side}_low']
        for c in ('open', 'close', 'low'):
            bad = df[high < df[f'{side}_{c}']]
            if not bad.empty:
                errors.append(f'{side}_high < {side}_{c} in {len(bad)} timeshot(s); '
                              f'first at {bad.index[0]}')
        for c in ('open', 'close', 'high'):
            bad = df[low > df[f'{side}_{c}']]
            if not bad.empty:
                errors.append(f'{side}_low > {side}_{c} in {len(bad)} timeshot(s); '
                              f'first at {bad.index[0]}')

    if errors:
        print('Validation FAILED:')
        for e in errors:
            print(f'  - {e}')
        raise SystemExit(1)
    print('Validation OK: spreads non-negative, highs/lows consistent.')


def main():
    timeshots = load_timeshots(DATA_FILE)
    df = to_dataframe(timeshots)
    statistics(df)
    validate(df)


if __name__ == '__main__':
    main()
