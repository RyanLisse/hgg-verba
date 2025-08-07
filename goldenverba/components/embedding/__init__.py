from goldenverba.components.embedding.CohereEmbedder import CohereEmbedder
from goldenverba.components.embedding.OllamaEmbedder import OllamaEmbedder
from goldenverba.components.embedding.OpenAIEmbedder import OpenAIEmbedder
from goldenverba.components.embedding.SentenceTransformersEmbedder import (
    SentenceTransformersEmbedder,
)
from goldenverba.components.embedding.VoyageAIEmbedder import VoyageAIEmbedder

embedders = [
    SentenceTransformersEmbedder(),
    OpenAIEmbedder(),
    CohereEmbedder(),
    VoyageAIEmbedder(),
    OllamaEmbedder(),
]
