from setuptools import find_packages, setup

setup(
    name="goldenverba",
    version="2.0.0",
    packages=find_packages(),
    python_requires=">=3.10.0",
    entry_points={
        "console_scripts": [
            "verba=goldenverba.server.cli:cli",
        ],
    },
    author="Weaviate",
    author_email="edward@weaviate.io",
    description="Welcome to Verba: The Golden RAGtriever, an open-source initiative designed to offer a streamlined, user-friendly interface for Retrieval-Augmented Generation (RAG) applications. In just a few easy steps, dive into your data and make meaningful interactions!",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/weaviate/Verba",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    include_package_data=True,
    install_requires=[
      "weaviate-client==4.9.6",
        "python-dotenv==1.0.0",
        "wasabi==1.1.2",
        "fastapi==0.111.1",
        "uvicorn[standard]==0.29.0",
        "gunicorn==22.0.0",
        "click==8.1.7",
        "asyncio==3.4.3",
        "tiktoken>=0.7.0",
        "requests==2.31.0",
        "pypdf==4.3.1",
        "python-docx==1.1.2",
        "scikit-learn==1.5.1",
        "langchain-text-splitters>=0.2.2",
        "langchain-openai>=0.2.0",
        "langsmith>=0.1.118",
        "instructor>=1.4.1",
        "spacy==3.7.5",
        "aiohttp==3.9.5",
        "markdownify==0.13.1",
        "assemblyai==0.33.0",
        "beautifulsoup4==4.12.3",
        "langdetect==1.0.9",
        "anthropic>=0.34.0",  # For Claude 4 models
    ],
    extras_require={
        "dev": ["pytest", "wheel", "twine", "black>=23.7.0", "setuptools"],
        "google": [
            "google-genai>=0.1.0",  # New Google Generative AI client
        ],
        "huggingface": [
            "sentence-transformers==3.0.1",
        ],
    },
)
