from stromwart.simulation.engine import compute_simulation_progress


def test_first_batch_of_long_phase_has_positive_progress() -> None:
    # FIFA phase 1: 0–75 of 95 total minutes
    progress = compute_simulation_progress(0, 75, batches_completed=1, batch_count=225, total_minutes=95)
    assert progress > 0.0


def test_mid_phase_progress_between_bounds() -> None:
    progress = compute_simulation_progress(0, 75, batches_completed=112, batch_count=225, total_minutes=95)
    assert 0.3 < progress < 0.5


def test_last_batch_reaches_phase_end() -> None:
    progress = compute_simulation_progress(0, 75, batches_completed=225, batch_count=225, total_minutes=95)
    assert progress == 75 / 95


def test_progress_clamped_to_one() -> None:
    progress = compute_simulation_progress(90, 95, batches_completed=10, batch_count=1, total_minutes=95)
    assert progress == 1.0


def test_fractional_first_batch_has_positive_progress() -> None:
    progress = compute_simulation_progress(0, 75, batches_completed=0.1, batch_count=225, total_minutes=95)
    assert progress > 0.0


def test_fractional_less_than_one_full_batch() -> None:
    p1 = compute_simulation_progress(0, 75, 0.5, 225, 95)
    p2 = compute_simulation_progress(0, 75, 1.0, 225, 95)
    assert 0 < p1 < p2
