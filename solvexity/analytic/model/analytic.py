from pydantic import BaseModel


class Analytic(BaseModel):
    result: float
    