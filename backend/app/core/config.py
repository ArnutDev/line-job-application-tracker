from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    line_channel_secret: str = ""
    line_channel_access_token: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"


    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()