import os
import pickle
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

DATA_FILE = './data/timeshots.pkl'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
CHARTS_DIR = 'charts'


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


def candlestick_frame(df, side):
    return df[[f'{side}_open', f'{side}_high', f'{side}_low', f'{side}_close']].rename(
        columns={
            f'{side}_open': 'Open',
            f'{side}_high': 'High',
            f'{side}_low': 'Low',
            f'{side}_close': 'Close',
        }
    )


def save_candlestick(df, side, filename):
    ohlc = candlestick_frame(df, side)
    mpf.plot(
        ohlc,
        type='candle',
        style='charles',
        title=f'EUR/USD {side.upper()} candlestick',
        ylabel='Price',
        volume=False,
        savefig=dict(fname=filename, dpi=150, bbox_inches='tight'),
    )
    print(f'Saved {filename}')


def save_close_lines(df, filename):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['ask_close'], label='Ask close', color='tab:blue')
    ax.plot(df.index, df['bid_close'], label='Bid close', color='tab:orange')
    ax.set_title('EUR/USD close prices (ask vs bid)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Price')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.4)
    fig.autofmt_xdate()
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {filename}')


def parse_date(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return datetime.strptime(raw, DATE_FORMAT)
        except ValueError:
            print(f"Invalid format. Expected '{DATE_FORMAT}'.")


def main():
    timeshots = load_timeshots(DATA_FILE)
    df = to_dataframe(timeshots)

    begin = parse_date(f"Begin date  ({DATE_FORMAT}): ")
    finish = parse_date(f"Finish date ({DATE_FORMAT}): ")
    if finish < begin:
        raise SystemExit('Finish date must be on or after begin date.')

    window = df.loc[begin:finish]
    if window.empty:
        raise SystemExit('No timeshots fall within the requested range.')

    print(f'Selected timeshots: {len(window)}')

    os.makedirs(CHARTS_DIR, exist_ok=True)
    save_candlestick(window, 'ask', os.path.join(CHARTS_DIR, 'ask_candlestick.png'))
    save_candlestick(window, 'bid', os.path.join(CHARTS_DIR, 'bid_candlestick.png'))
    save_close_lines(window, os.path.join(CHARTS_DIR, 'close_lines.png'))


if __name__ == '__main__':
    main()
