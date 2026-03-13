import os


OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "openai/text-embedding-3-small")

# Claude via OpenRouter
CLAUDE_MODEL = "anthropic/claude-sonnet-4-6"

# Paths
DATA_RAW = "data/raw"
DATA_PROCESSED = "data/processed"
DATA_RESULTS = "data/results"
OUTPUTS = "outputs"
