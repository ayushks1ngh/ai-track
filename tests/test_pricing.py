from aitrack.utils.pricing import calculate_cost, get_pricing


class TestPricing:
    def test_get_pricing(self):
        config = get_pricing()
        assert len(config.models) > 0

    def test_calculate_cost_free_model(self):
        cost = calculate_cost("opencode", "big-pickle", 1000, 500)
        assert cost == 0.0

    def test_calculate_cost_paid_model(self):
        cost = calculate_cost("anthropic", "claude-sonnet-4", 1000, 500)
        assert cost > 0
        # 1000 input * 0.003/1k = 0.003, 500 output * 0.015/1k = 0.0075
        assert cost == 0.0105

    def test_calculate_cost_with_cache(self):
        cost = calculate_cost("anthropic", "claude-sonnet-4", 1000, 500, cache_read_tokens=2000)
        # 1000*0.003/1k + 500*0.015/1k + 2000*0.0003/1k = 0.003 + 0.0075 + 0.0006
        assert abs(cost - 0.0111) < 1e-6

    def test_pricing_find(self):
        config = get_pricing()
        found = config.find("anthropic", "claude-sonnet-4")
        assert found is not None
        assert found.model_id == "claude-sonnet-4"

    def test_pricing_find_wildcard(self):
        cost = calculate_cost("openrouter", "some-unknown-model", 1000, 500)
        assert cost == 0.0
