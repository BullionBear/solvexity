from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str="SOLVEXITY"
    SOLVEXITY_MONGO_URI: str
    SOLVEXITY_SERVICE: str

    class Config:
        env_file = ".env"

settings = Settings()