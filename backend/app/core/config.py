import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in project root or current working dir
root_dir = Path(__file__).resolve().parent.parent.parent.parent
env_path = root_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    PROJECT_NAME: str = "BharatAgri Iteration 2 API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "bharatagri_iteration2")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "bharatagri_secure_jwt_secret_key_2026_iteration2")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    PORT: int = int(os.getenv("PORT", 5000))

    @property
    def DATABASE_URL(self) -> str:
        # Standard PyMySQL URL
        pw = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
        return f"mysql+pymysql://{self.DB_USER}{pw}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

settings = Settings()
