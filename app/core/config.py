from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from functools import lru_cache
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Database ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER_DOCKER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # --- Security ---
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- API key ---
    GEMINI_API_KEY: str = ""

    # --- General ---
    PROJECT_NAME: str = "CV Evaluation API"
    ENVIRONMENT: str = "development"
    MODEL_NAME: str = "all-MiniLM-L6-v2"

    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/mydatabase'
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER_DOCKER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
