from pydantic_settings import BaseSettings
from pydantic import ConfigDict, EmailStr


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int
    POSTGRES_DOMAIN: str

    DATABASE_URL: str

    SECRET_KEY_JWT: str
    ALGORITHM: str

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    REDIS_DOMAIN: str
    REDIS_PORT: int
    REDIS_PASSWORD: str | None = None

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str
  


    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )


config = Settings()
