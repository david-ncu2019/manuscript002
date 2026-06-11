"""TimeOracle — single owner of 'now'. Encodes Do-Not-Regress rule 11 (no temporal leakage)."""
import pandas as pd

class LeakageError(RuntimeError):
    pass

class TimeOracle:
    def __init__(self, now: pd.Timestamp):
        self.now = pd.Timestamp(now)

    def advance(self, to) -> None:
        to = pd.Timestamp(to)
        if to < self.now:
            raise LeakageError(f"time cannot run backward: {self.now} -> {to}")
        self.now = to

    def view(self, df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        return df[df[date_col] <= self.now]

    def assert_no_future(self, df: pd.DataFrame, date_col: str = "date") -> None:
        if (df[date_col] > self.now).any():
            raise LeakageError(f"future rows present past {self.now}")
