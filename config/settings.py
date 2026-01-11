# RAG Application Configuration
# ================================
# This file holds all configuration in ONE place.
# Why? So you don't have to hunt through 10 files to change an API key.

import os
from dataclasses import dataclass

# ============================================
# PYTHON CONCEPT: dataclass
# ============================================
# A dataclass is a shortcut for creating classes that mainly hold data.
# Instead of writing __init__, __repr__, etc., Python generates them for you.
#
# Without dataclass, you'd write:
#   class ChunkConfig:
#       def __init__(self, chunk_size, chunk_overlap):
#           self.chunk_size = chunk_size
#           self.chunk_overlap = chunk_overlap
#
# With dataclass, you just declare the fields:

@dataclass
class ChunkConfig:
    """Configuration for document chunking."""
    chunk_size: int = 1000       # Number of characters per chunk
    chunk_overlap: int = 200     # Overlap between consecutive chunks


@dataclass
class WeaviateConfig:
    """Configuration for Weaviate vector database."""
    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051
    class_name: str = "Document"  # Name of the collection in Weaviate


@dataclass
class GeminiConfig:
    """Configuration for Google Gemini API (used for embeddings)."""
    api_key: str = os.getenv("GEMINI_API_KEY", "AIzaSyByz9QB9i9tqyR8IRIMqmiZ4eJ7_e5MVAA")
    embedding_model: str = "models/text-embedding-004"


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API (used for LLM)."""
    api_key: str = os.getenv(
        "OPENROUTER_API_KEY",
        "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"
    )
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "xiaomi/mimo-v2-flash:free"


# ============================================
# PYTHON CONCEPT: Putting it all together
# ============================================
# We create ONE master config that holds all sub-configs.
# This makes it easy to pass around: just pass `config` everywhere.

@dataclass
class AppConfig:
    """Master configuration for the entire application."""
    chunk: ChunkConfig = None
    weaviate: WeaviateConfig = None
    gemini: GeminiConfig = None
    openrouter: OpenRouterConfig = None
    
    def __post_init__(self):
        # __post_init__ runs AFTER the dataclass __init__
        # We use it to set default values for nested configs
        if self.chunk is None:
            self.chunk = ChunkConfig()
        if self.weaviate is None:
            self.weaviate = WeaviateConfig()
        if self.gemini is None:
            self.gemini = GeminiConfig()
        if self.openrouter is None:
            self.openrouter = OpenRouterConfig()


# Create a default config instance
# Other files can do: from config.settings import config
config = AppConfig()
