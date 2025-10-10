"""
Configuration models for EAR tool.
Uses Pydantic Settings for unified configuration from environment variables, .env files, and CLI args.
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OdooConfig(BaseSettings):
    """Odoo connection configuration."""

    model_config = SettingsConfigDict(
        env_prefix='ODOO_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    url: str = Field(default="https://erp.wapsol.de", description="Odoo server URL")
    db: str = Field(default="pwo-18-prod", description="Odoo database name")
    user: str = Field(default="ashant@simplify-erp.de", description="Odoo username/email")
    password: Optional[str] = Field(default=None, description="Odoo password")


class GitHubConfig(BaseSettings):
    """GitHub configuration."""

    model_config = SettingsConfigDict(
        env_prefix='GITHUB_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    orgs: str = Field(default="euroblaze,wapsol", description="Comma-separated GitHub organizations")
    default_period: str = Field(default="lastweek", description="Default time period for reports")

    def get_orgs_list(self) -> List[str]:
        """Get organizations as a list."""
        return [org.strip() for org in self.orgs.split(',') if org.strip()]


class ServerConfig(BaseSettings):
    """HTTPS server configuration."""

    model_config = SettingsConfigDict(
        env_prefix='SERVER_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    port: int = Field(default=443, description="Server port")
    ssl_cert_path: str = Field(default=".ssl/cert.pem", description="SSL certificate path")
    ssl_key_path: str = Field(default=".ssl/key.pem", description="SSL key path")
    auto_generate_certs: bool = Field(default=True, description="Auto-generate SSL certificates if missing")
    reports_dir: str = Field(default="reports", description="Reports directory")


class APIConfig(BaseSettings):
    """API server configuration."""

    model_config = SettingsConfigDict(
        env_prefix='API_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    port: int = Field(default=8000, description="API server port")
    host: str = Field(default="0.0.0.0", description="API server host")


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Sub-configurations
    odoo: OdooConfig = Field(default_factory=OdooConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize sub-configs
        self.odoo = OdooConfig()
        self.github = GitHubConfig()
        self.server = ServerConfig()
        self.api = APIConfig()


# Global config instance (lazy-loaded)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config
