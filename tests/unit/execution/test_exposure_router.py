# tests/unit/execution/test_exposure_router.py
# Coverage target: jarvis/execution/exposure_router.py -> 95%+
# Missing line: 68

import pytest

from jarvis.execution.exposure_router import route_exposure_to_positions


class TestRouteExposureToPositions:
    def test_basic_routing(self):
        positions = route_exposure_to_positions(
            total_capital=100000.0,
            exposure_fraction=0.5,
            asset_prices={"BTC": 50000.0, "ETH": 2000.0},
        )
        assert isinstance(positions, dict)
        assert "BTC" in positions
        assert "ETH" in positions

    def test_zero_exposure(self):
        positions = route_exposure_to_positions(
            total_capital=100000.0,
            exposure_fraction=0.0,
            asset_prices={"BTC": 50000.0},
        )
        assert positions["BTC"] == 0.0

    def test_full_exposure(self):
        positions = route_exposure_to_positions(
            total_capital=100000.0,
            exposure_fraction=1.0,
            asset_prices={"SPY": 500.0},
        )
        assert positions["SPY"] == 200.0

    def test_negative_exposure_raises(self):
        # line 68
        with pytest.raises(ValueError, match="exposure_fraction"):
            route_exposure_to_positions(
                total_capital=100000.0,
                exposure_fraction=-0.1,
                asset_prices={"BTC": 50000.0},
            )

    def test_exposure_above_one_raises(self):
        # line 68
        with pytest.raises(ValueError, match="exposure_fraction"):
            route_exposure_to_positions(
                total_capital=100000.0,
                exposure_fraction=1.1,
                asset_prices={"BTC": 50000.0},
            )

    def test_delegates_to_allocate_positions(self):
        result = route_exposure_to_positions(
            total_capital=100000.0,
            exposure_fraction=0.3,
            asset_prices={"A": 100.0, "B": 200.0},
        )
        assert all(v >= 0 for v in result.values())
