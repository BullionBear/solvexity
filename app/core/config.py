from pydantic import BaseSettings

class Settings(BaseSettings):
    SOLVEXITY_MONGO_URI: str
    SOLVEXITY_SERVICE: str

    class Config:
        env_file = ".env"

settings = Settings()