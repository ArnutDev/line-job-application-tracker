from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    line_channel_secret: str = ""
    line_channel_access_token: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    admin_line_user_ids: str = ""
    daily_message_limit: int = 10

    def is_unlimited_user(self, line_user_id: str) -> bool:
        """Check if a LINE user ID is configured as an unlimited / admin user."""
        if not self.admin_line_user_ids or not line_user_id:
            return False
        admin_ids = [uid.strip() for uid in self.admin_line_user_ids.split(",") if uid.strip()]
        return line_user_id.strip() in admin_ids

    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()