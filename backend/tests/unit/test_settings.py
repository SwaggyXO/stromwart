from stromwart.core import LlmProvider, Settings


def test_settings_supports_provider_neutral_llm_configuration() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://stromwart:stromwart@localhost:5433/stromwart_test",
        llm_provider="openai_compatible",
        llm_base_url="https://gateway.example.com/v1",
        llm_api_key="secret",
        llm_model="provider/model",
    )

    assert settings.llm_provider is LlmProvider.OPENAI_COMPATIBLE
    assert settings.allowed_origins == ["http://localhost:5173"]


def test_allowed_origins_parses_comma_separated_cors_origins() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://stromwart:stromwart@localhost:5433/stromwart_test",
        cors_origins="http://localhost:3000, http://localhost:5173",
    )

    assert settings.allowed_origins == [
        "http://localhost:3000",
        "http://localhost:5173",
    ]