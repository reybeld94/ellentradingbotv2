from pydantic import BaseModel, ConfigDict

class PortfolioCreate(BaseModel):
    name: str
    api_key: str
    secret_key: str
    base_url: str
    broker: str | None = None


class PortfolioResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    broker: str | None = None

    model_config = ConfigDict(from_attributes=True)

