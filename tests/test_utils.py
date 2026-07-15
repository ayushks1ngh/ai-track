from aitrack.utils.formatters import format_cost, format_tokens


class TestFormatters:
    def test_format_tokens_thousands(self):
        assert format_tokens(1500) == "1.5K"

    def test_format_tokens_millions(self):
        assert format_tokens(2_500_000) == "2.5M"

    def test_format_tokens_small(self):
        assert format_tokens(500) == "500"

    def test_format_cost_zero(self):
        assert format_cost(0) == "$0.00"

    def test_format_cost_small(self):
        val = format_cost(0.000123)
        assert val.startswith("$0.000")

    def test_format_cost_dollars(self):
        assert format_cost(12.34) == "$12.34"
