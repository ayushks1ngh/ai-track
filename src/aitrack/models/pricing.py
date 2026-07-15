from pydantic import BaseModel


class ModelPricing(BaseModel):
    provider: str
    model_id: str
    input_price_per_1k: float
    output_price_per_1k: float
    cache_read_price_per_1k: float = 0.0
    cache_write_price_per_1k: float = 0.0


class PricingConfig(BaseModel):
    models: list[ModelPricing]

    def find(self, provider: str, model_id: str) -> ModelPricing | None:
        for m in self.models:
            if m.provider.lower() == provider.lower() and m.model_id.lower() == model_id.lower():
                return m
        return None
