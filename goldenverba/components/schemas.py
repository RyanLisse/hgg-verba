# schemas.py - Common Pydantic models for structured RAG outputs
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for generated responses."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Types of sources used in RAG responses."""
    DOCUMENT = "document"
    CHUNK = "chunk"
    WEB_SEARCH = "web_search"
    FILE_SEARCH = "file_search"
    REASONING = "reasoning"


class Citation(BaseModel):
    """Citation information for sources used in responses."""
    source_id: str = Field(..., description="Unique identifier for the source")
    source_type: SourceType = Field(..., description="Type of source (document, chunk, web, etc.)")
    title: Optional[str] = Field(None, description="Title of the source document")
    content_snippet: str = Field(..., description="Relevant snippet from the source")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in this citation's relevance")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ReasoningStep(BaseModel):
    """Individual reasoning step in the thought process."""
    step_number: int = Field(..., description="Sequential step number")
    description: str = Field(..., description="Description of this reasoning step")
    content: str = Field(..., description="The actual reasoning content")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in this step")


class ThinkingTrace(BaseModel):
    """Structured thinking trace for reasoning models."""
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list, description="Step-by-step reasoning process")
    total_thinking_time: Optional[float] = Field(None, description="Total time spent thinking (in seconds)")
    complexity_level: str = Field("medium", description="Complexity level of the reasoning task")
    final_conclusion: str = Field(..., description="Final conclusion from the thinking process")


class RAGResponse(BaseModel):
    """Structured response from RAG generators with enhanced metadata."""
    
    # Core response content
    answer: str = Field(..., description="The main answer to the user's question")
    confidence_level: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Overall confidence in the response")
    
    # Source attribution
    citations: List[Citation] = Field(default_factory=list, description="Sources used to generate this response")
    source_documents_used: int = Field(0, description="Number of source documents referenced")
    
    # Reasoning and validation
    reasoning_trace: Optional[ThinkingTrace] = Field(None, description="Detailed reasoning process if available")
    key_insights: List[str] = Field(default_factory=list, description="Key insights extracted from sources")
    limitations: List[str] = Field(default_factory=list, description="Known limitations or caveats")
    
    # Quality metrics
    factual_accuracy_score: float = Field(0.0, ge=0.0, le=1.0, description="Estimated factual accuracy")
    completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="How complete the answer is")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance to the original question")
    
    # Follow-up suggestions
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    related_topics: List[str] = Field(default_factory=list, description="Related topics for further exploration")
    
    # Technical metadata
    model_name: str = Field(..., description="Name of the model that generated this response")
    generation_time: Optional[float] = Field(None, description="Time taken to generate response (in seconds)")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage statistics")
    
    # Error handling
    warnings: List[str] = Field(default_factory=list, description="Any warnings during generation")
    error_messages: List[str] = Field(default_factory=list, description="Any error messages encountered")


class StreamingChunk(BaseModel):
    """Individual chunk in a streaming response."""
    chunk_type: str = Field(..., description="Type of chunk: content, reasoning, citation, metadata")
    content: str = Field("", description="Content of this chunk")
    is_complete: bool = Field(False, description="Whether this chunk completes a section")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")


class EnhancedRAGResponse(RAGResponse):
    """Extended RAG response with advanced features for specific models."""
    
    # Advanced reasoning (for Claude, o1, Gemini Deep Think)
    extended_thinking: Optional[str] = Field(None, description="Extended thinking process for complex queries")
    alternative_perspectives: List[str] = Field(default_factory=list, description="Alternative viewpoints considered")
    
    # Multimodal support
    image_analysis: Optional[Dict[str, Any]] = Field(None, description="Results from image analysis if applicable")
    visual_elements: List[str] = Field(default_factory=list, description="Visual elements referenced")
    
    # Tool usage tracking
    tools_used: List[str] = Field(default_factory=list, description="External tools used (web search, file search, etc.)")
    tool_results: Dict[str, Any] = Field(default_factory=dict, description="Results from tool usage")
    
    # Quality assurance
    fact_check_status: Optional[str] = Field(None, description="Status of fact-checking if performed")
    cross_references: List[str] = Field(default_factory=list, description="Cross-references to verify information")
    
    # User experience
    reading_time_estimate: Optional[int] = Field(None, description="Estimated reading time in minutes")
    complexity_rating: str = Field("intermediate", description="Complexity rating for the response")


class ValidationResult(BaseModel):
    """Result of validating a generated response."""
    is_valid: bool = Field(..., description="Whether the response passes validation")
    validation_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall validation score")
    issues_found: List[str] = Field(default_factory=list, description="List of validation issues")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    validated_at: str = Field(..., description="Timestamp of validation")


class GeneratorConfig(BaseModel):
    """Configuration for structured output generators."""
    enable_structured_output: bool = Field(True, description="Enable structured Pydantic outputs")
    include_reasoning: bool = Field(True, description="Include reasoning traces")
    include_citations: bool = Field(True, description="Include source citations")
    confidence_threshold: float = Field(0.5, description="Minimum confidence threshold")
    max_citations: int = Field(10, description="Maximum number of citations to include")
    enable_validation: bool = Field(True, description="Enable response validation")
    response_format: str = Field("enhanced", description="Response format: basic, standard, enhanced")


# Utility functions for working with structured outputs

def create_citation_from_chunk(chunk_id: str, content: str, title: str = None) -> Citation:
    """Create a citation from a document chunk."""
    return Citation(
        source_id=chunk_id,
        source_type=SourceType.CHUNK,
        title=title,
        content_snippet=content[:200] + "..." if len(content) > 200 else content,
        confidence_score=0.8
    )


def create_basic_rag_response(answer: str, model_name: str, citations: List[Citation] = None) -> RAGResponse:
    """Create a basic RAG response with minimal metadata."""
    return RAGResponse(
        answer=answer,
        model_name=model_name,
        citations=citations or [],
        confidence_level=ConfidenceLevel.MEDIUM
    )


def validate_response_quality(response: RAGResponse, min_confidence: float = 0.5) -> ValidationResult:
    """Validate the quality of a RAG response."""
    issues = []
    score = 1.0
    
    if response.confidence_level == ConfidenceLevel.LOW:
        issues.append("Response confidence is low")
        score -= 0.3
    
    if not response.citations:
        issues.append("No citations provided")
        score -= 0.4
    
    if len(response.answer) < 50:
        issues.append("Response is too short")
        score -= 0.2
    
    if response.factual_accuracy_score < min_confidence:
        issues.append(f"Factual accuracy below threshold ({response.factual_accuracy_score:.2f} < {min_confidence})")
        score -= 0.3
    
    return ValidationResult(
        is_valid=len(issues) == 0,
        validation_score=max(0.0, score),
        issues_found=issues,
        suggestions=[
            "Add more source citations",
            "Increase response detail",
            "Improve factual accuracy"
        ] if issues else [],
        validated_at=str(__import__('datetime').datetime.utcnow())
    )