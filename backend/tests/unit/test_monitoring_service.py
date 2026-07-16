from stromwart.monitoring.service import DriftService


def test_psi_detects_distribution_shift():
    baseline = [10.0] * 50 + [20.0] * 50
    observed = [90.0] * 100

    result = DriftService().population_stability_index(baseline, observed)

    assert result.drifted is True


def test_psi_is_stable_for_same_distribution():
    values = [float(index) for index in range(100)]

    result = DriftService().population_stability_index(values, values)

    assert result.drifted is False
    assert result.score == 0.0