from shot.utils import *

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
