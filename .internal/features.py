import pickle
from datetime import datetime

DATA_FILE = './data/timeshots.pkl'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def load_timeshots(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def find_decision_points(timeshots, n):
    asc, dsc = [], []
    for i in range(n + 1, len(timeshots)):
        window = timeshots[i - n - 1:i]

        is_asc = all(
            window[k + 1][1][1][2] >= window[k][1][1][2]
            for k in range(n)
        )
        is_dsc = all(
            window[k + 1][1][1][1] <= window[k][1][1][1]
            for k in range(n)
        )

        if is_asc:
            asc.append(i)
        if is_dsc:
            dsc.append(i)
    return asc, dsc


def format_timeshot(ts):
    timestamp, (ask, bid), volume, ordinal = ts
    dt = datetime.fromtimestamp(timestamp).strftime(DATE_FORMAT)
    return (f'  [{ordinal}] {dt}  '
            f'ask=({ask[0]:.5f}, {ask[1]:.5f}, {ask[2]:.5f}, {ask[3]:.5f})  '
            f'bid=({bid[0]:.5f}, {bid[1]:.5f}, {bid[2]:.5f}, {bid[3]:.5f})  '
            f'vol={volume}')


def print_decision_points(label, indices, timeshots, n, limit=5):
    print(f'{label} decision points: {len(indices)} found')
    print()
    for idx in indices[:limit]:
        print(f'{label} decision point at index {idx}:')
        print('  preceding timeshots:')
        for j in range(idx - n, idx):
            print(format_timeshot(timeshots[j]))
        print('  decision point:')
        print(format_timeshot(timeshots[idx]))
        print()


def main():
    timeshots = load_timeshots(DATA_FILE)
    print(f'Loaded {len(timeshots)} timeshots from {DATA_FILE}')

    n = int(input('Enter the value of parameter N: '))
    if n < 1:
        raise SystemExit('N must be a positive integer')

    asc, dsc = find_decision_points(timeshots, n)
    print()
    print_decision_points('ASC', asc, timeshots, n)
    print_decision_points('DSC', dsc, timeshots, n)


if __name__ == '__main__':
    main()
