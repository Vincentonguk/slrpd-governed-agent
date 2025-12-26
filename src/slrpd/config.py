from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = '.data'
    corpus_dir: str = '.data/corpus'
    audit_dir: str = '.data/audit'
    reports_dir: str = '.data/reports'
    min_retrieval_score_default: float = 0.15

settings = Settings()

