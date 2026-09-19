import pytest
import pandas as pd
import numpy as np


def compute_zero_leakage_skip_rate(series: pd.Series, prior_weight: float = 10.0, global_mean: float = 0.104) -> pd.Series:
    """
    Computes zero-leakage expanding window smoothed skip rate.
    Each row N uses only the cumulative sum and count of rows 0 to N-1.
    """
    cum_sum = series.cumsum().shift(1).fillna(0)
    cum_count = pd.Series(np.arange(len(series)), index=series.index)  # row N has exactly N prior items (0..N-1)
    
    smoothed_rate = (cum_sum + prior_weight * global_mean) / (cum_count + prior_weight)
    return smoothed_rate


def test_expanding_window_zero_leakage(synthetic_streaming_df):
    """
    Verifies that the expanding window calculation for row N uses strictly rows 0..N-1
    and does NOT leak row N's own target value or future target values.
    """
    df = synthetic_streaming_df.copy()
    
    # Calculate zero-leakage target encoding
    df["artist_smoothed"] = compute_zero_leakage_skip_rate(df["skipped"])
    
    # 1. Row 0 must be purely equal to prior default (global mean) since 0 prior rows exist
    global_mean = 0.104
    prior_weight = 10.0
    expected_row_0 = (0 + prior_weight * global_mean) / (0 + prior_weight)
    assert np.isclose(df.loc[0, "artist_smoothed"], expected_row_0)
    
    # 2. Mutate row 0's actual skip label and verify that row 0's smoothed value does NOT change
    original_row_0_val = df.loc[0, "skipped"]
    df_mutated = df.copy()
    df_mutated.loc[0, "skipped"] = 1 - original_row_0_val  # flip label
    
    df_mutated["artist_smoothed"] = compute_zero_leakage_skip_rate(df_mutated["skipped"])
    
    # Row 0 value must remain IDENTICAL despite row 0 label flip (zero self-leakage)
    assert np.isclose(df.loc[0, "artist_smoothed"], df_mutated.loc[0, "artist_smoothed"])
    
    # Row 1 value MUST change because row 1 depends on row 0's historical label
    assert not np.isclose(df.loc[1, "artist_smoothed"], df_mutated.loc[1, "artist_smoothed"])


def test_micro_mood_momentum(synthetic_streaming_df):
    """
    Tests rolling time window calculation for skips_last_3m.
    """
    df = synthetic_streaming_df.copy()
    
    # Set up specific time deltas
    df["time_stamp"] = [
        pd.Timestamp("2025-01-01 10:00:00"),
        pd.Timestamp("2025-01-01 10:01:00"),  # 1m later
        pd.Timestamp("2025-01-01 10:02:00"),  # 2m later
        pd.Timestamp("2025-01-01 10:10:00"),  # 10m later (outside 3m window)
    ] + list(pd.date_range(start="2025-01-01 11:00:00", periods=len(df)-4, freq="3min"))
    
    df["skipped"] = [1, 1, 0, 1] + [0] * (len(df) - 4)
    
    # Compute rolling 3-minute skips excluding current row
    indexed_df = df.set_index("time_stamp")
    # Shift by 1 to prevent current row inclusion
    past_skips = indexed_df["skipped"].shift(1).fillna(0)
    rolling_3m = past_skips.rolling("3min").sum()
    
    # Index 0 (10:00:00): 0 past skips
    assert rolling_3m.iloc[0] == 0
    # Index 1 (10:01:00): 1 past skip (from 10:00:00)
    assert rolling_3m.iloc[1] == 1
    # Index 2 (10:02:00): 2 past skips (from 10:00:00 and 10:01:00)
    assert rolling_3m.iloc[2] == 2
    # Index 3 (10:10:00): 0 past skips within 3min (10:00 and 10:01 dropped out)
    assert rolling_3m.iloc[3] == 0


def test_cold_start_fallback_handling():
    """
    Verifies cold start logic when encountering unknown artists/songs.
    """
    artist_lookup = {"coldplay": 0.15, "radiohead": 0.40}
    default_fallback = 0.104
    
    # Test known artist
    artist_name = "Coldplay"
    rate = artist_lookup.get(artist_name.lower().strip(), default_fallback)
    is_cold_start = 1 if artist_name.lower().strip() not in artist_lookup else 0
    assert rate == 0.15
    assert is_cold_start == 0
    
    # Test unknown artist (cold start)
    unknown_artist = "Unknown Indie Band"
    rate_cold = artist_lookup.get(unknown_artist.lower().strip(), default_fallback)
    is_cold_start_unknown = 1 if unknown_artist.lower().strip() not in artist_lookup else 0
    assert rate_cold == default_fallback
    assert is_cold_start_unknown == 1
