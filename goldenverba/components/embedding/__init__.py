from goldenverba.components.embedding.OpenAIEmbedder import OpenAIEmbedder
from goldenverba.components.embedding.CohereEmbedder import CohereEmbedder
from goldenverba.components.embedding.WeaviateEmbedder import WeaviateEmbedder
from goldenverba.components.embedding.VoyageAIEmbedder import VoyageAIEmbedder
from goldenverba.components.embedding.SentenceTransformersEmbedder import SentenceTransformersEmbedder
from goldenverba.components.embedding.OllamaEmbedder import OllamaEmbedder

embedders = [
    SentenceTransformersEmbedder(),
    OpenAIEmbedder(),
    CohereEmbedder(),
    WeaviateEmbedder(),
    VoyageAIEmbedder(),
    OllamaEmbedder()
]
