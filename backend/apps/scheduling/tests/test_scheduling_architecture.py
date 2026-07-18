from apps.core.quality.rules.scheduling import validate_scheduling_architecture


def test_scheduling_architecture_is_valid():
    errors: list[str] = []

    validate_scheduling_architecture(errors)

    assert errors == []
