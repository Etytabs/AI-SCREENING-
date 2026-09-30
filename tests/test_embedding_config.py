from ml.semantic_matching.embedding import (
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingConfig,
    create_embedder,
)


def test_embedding_config_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("AI_SCREENING_EMBEDDINGS_ENABLED", raising=False)
    monkeypatch.delenv("AI_SCREENING_EMBEDDING_MODEL", raising=False)

    config = EmbeddingConfig.from_env()

    assert config.enabled is False
    assert config.model_name == DEFAULT_EMBEDDING_MODEL


def test_embedding_config_can_enable_model(monkeypatch):
    monkeypatch.setenv("AI_SCREENING_EMBEDDINGS_ENABLED", "true")
    monkeypatch.setenv("AI_SCREENING_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    config = EmbeddingConfig.from_env()

    assert config.enabled is True
    assert config.model_name == DEFAULT_EMBEDDING_MODEL


def test_disabled_runtime_does_not_construct_model():
    assert create_embedder(EmbeddingConfig(enabled=False)) is None
