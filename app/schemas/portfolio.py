from pydantic import BaseModel, ConfigDict

class PortfolioCreate(BaseModel):
    name: str
    api_key: str
    secret_key: str
    base_url: str
    is_paper: bool | None = None


class PortfolioUpdate(BaseModel):
    name: str | None = None
    api_key: str | None = None
    secret_key: str | None = None
    base_url: str | None = None
    is_paper: bool | None = None


class PortfolioResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    broker: str = "alpaca"
    is_paper: bool | None = None

    model_config = ConfigDict(from_attributes=True)

