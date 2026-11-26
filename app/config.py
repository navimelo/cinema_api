"""Configurações da aplicação (lidas de variáveis de ambiente ou do arquivo .env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./database.db"
    SQL_ECHO: bool = False

    # --- Parâmetros das regras de negócio do cinema ---
    INTERVALO_LIMPEZA_MIN: int = 15          # intervalo entre sessões na mesma sala
    MAX_INGRESSOS_POR_COMPRA: int = 10       # limite de assentos por operação de compra
    CANCELAMENTO_ANTECEDENCIA_MIN: int = 60  # cancelar até X min antes da sessão
    VALIDACAO_ANTECEDENCIA_MIN: int = 30     # validar (entrada) a partir de X min antes


settings = Settings()
