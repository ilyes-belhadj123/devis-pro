from pydantic import BaseModel


class CleApiInput(BaseModel):
    api_key: str


class StatutCle(BaseModel):
    configuree: bool
