from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    line_channel_secret: str = ""
    line_channel_access_token: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"


    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()