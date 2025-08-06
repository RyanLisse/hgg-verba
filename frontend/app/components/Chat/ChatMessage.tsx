"use client";

import type {
  ChunkScore,
  Citation,
  Message,
  StructuredResponse,
  Theme,
} from "@/app/types";
import type React from "react";
import { useState } from "react";
import { BiError } from "react-icons/bi";
import { FaDatabase } from "react-icons/fa";
import {
  FaBrain,
  FaChevronDown,
  FaChevronUp,
  FaClock,
  FaExclamationTriangle,
  FaEye,
  FaLightbulb,
  FaQuestion,
} from "react-icons/fa";
import { HiCog, HiSparkles } from "react-icons/hi2";
import { IoDocumentAttach, IoNewspaper } from "react-icons/io5";
import { RiRobot2Fill } from "react-icons/ri";
import ReactMarkdown from "react-markdown";

import VerbaButton from "../Navigation/VerbaButton";

interface ChatMessageProps {
  message: Message;
  messageIndex: number;
  selectedTheme: Theme;
  selectedDocument: string | null;
  setSelectedDocument: (s: string | null) => void;
  setSelectedDocumentScore: (s: string | null) => void;
  setSelectedChunkScore: (s: ChunkScore[]) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  selectedTheme,
  selectedDocument,
  setSelectedDocument,
  messageIndex,
  setSelectedDocumentScore,
  setSelectedChunkScore,
}) => {
  const [showReasoning, setShowReasoning] = useState(false);
  const [showCitations, setShowCitations] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [showLimitations, setShowLimitations] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);

  const colorTable = {
    user: "bg-bg-verba",
    system: "bg-bg-alt-verba",
    error: "bg-warning-verba",
    retrieval: "bg-bg-verba",
    thinking: "bg-blue-50 dark:bg-blue-900/20",
  };

  const renderConfidenceBadge = (confidence: string) => {
    const colors = {
      high: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      medium:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      low: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      unknown: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colors[confidence as keyof typeof colors]}`}
      >
        {confidence.toUpperCase()}
      </span>
    );
  };

  const renderCitations = (citations: Citation[]) => {
    if (!citations || citations.length === 0) return null;

    return (
      <div className="mt-4">
        <button
          type="button"
          onClick={() => setShowCitations(!showCitations)}
          className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors mb-2"
        >
          <IoDocumentAttach size={14} />
          <span>Sources ({citations.length})</span>
          {showCitations ? (
            <FaChevronUp size={12} />
          ) : (
            <FaChevronDown size={12} />
          )}
        </button>
        {showCitations && (
          <div className="space-y-2 pl-4 border-l-2 border-blue-200 dark:border-blue-700">
            {citations.map((citation, idx) => (
              <div
                key={citation.source_id || `citation-${idx}`}
                className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                      {citation.title || `Source ${idx + 1}`}
                    </h4>
                    <p className="text-xs text-gray-700 dark:text-gray-300 mb-2">
                      {citation.content_snippet}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <span className="capitalize">{citation.source_type}</span>
                      {citation.confidence_score && (
                        <span>
                          • Confidence:{" "}
                          {(citation.confidence_score * 100).toFixed(0)}%
                        </span>
                      )}
                      {citation.page_number && (
                        <span>• Page {citation.page_number}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderStructuredResponse = (structured: StructuredResponse) => {
    return (
      <div className="space-y-4">
        {/* Provider header */}
        {structured.provider && (
          <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
            <RiRobot2Fill size={14} />
            <span>Powered by {structured.provider.toUpperCase()}</span>
            {structured.model_name && <span>• {structured.model_name}</span>}
          </div>
        )}

        {/* Confidence level */}
        {structured.confidence_level && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Confidence:
            </span>
            {renderConfidenceBadge(structured.confidence_level)}
          </div>
        )}

        {/* Extended thinking */}
        {structured.extended_thinking && (
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-700">
            <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 mb-2">
              <FaBrain size={14} />
              <span className="text-sm font-medium">Extended Thinking</span>
            </div>
            <p className="text-sm text-purple-800 dark:text-purple-200">
              {structured.extended_thinking}
            </p>
          </div>
        )}

        {/* Main answer */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{structured.answer}</ReactMarkdown>
        </div>

        {/* Key insights */}
        {structured.key_insights && structured.key_insights.length > 0 && (
          <div>
            <button
              type="button"
              onClick={() => setShowInsights(!showInsights)}
              className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 transition-colors mb-2"
            >
              <FaLightbulb size={14} />
              <span>Key Insights ({structured.key_insights.length})</span>
              {showInsights ? (
                <FaChevronUp size={12} />
              ) : (
                <FaChevronDown size={12} />
              )}
            </button>
            {showInsights && (
              <ul className="space-y-1 pl-4">
                {structured.key_insights.map((insight, idx) => (
                  <li
                    key={`insight-${idx}-${insight.slice(0, 20)}`}
                    className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2"
                  >
                    <HiSparkles
                      size={14}
                      className="text-yellow-500 mt-0.5 flex-shrink-0"
                    />
                    {insight}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Alternative perspectives */}
        {structured.alternative_perspectives &&
          structured.alternative_perspectives.length > 0 && (
            <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
              <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 mb-2">
                <FaEye size={14} />
                <span className="text-sm font-medium">
                  Alternative Perspectives
                </span>
              </div>
              <ul className="space-y-1">
                {structured.alternative_perspectives.map((perspective, idx) => (
                  <li
                    key={`perspective-${idx}-${perspective.slice(0, 20)}`}
                    className="text-sm text-indigo-800 dark:text-indigo-200"
                  >
                    • {perspective}
                  </li>
                ))}
              </ul>
            </div>
          )}

        {/* Citations */}
        {structured.citations && renderCitations(structured.citations)}

        {/* Limitations */}
        {structured.limitations && structured.limitations.length > 0 && (
          <div>
            <button
              type="button"
              onClick={() => setShowLimitations(!showLimitations)}
              className="flex items-center gap-2 text-sm text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 transition-colors mb-2"
            >
              <FaExclamationTriangle size={14} />
              <span>Limitations ({structured.limitations.length})</span>
              {showLimitations ? (
                <FaChevronUp size={12} />
              ) : (
                <FaChevronDown size={12} />
              )}
            </button>
            {showLimitations && (
              <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-700">
                <ul className="space-y-1">
                  {structured.limitations.map((limitation, idx) => (
                    <li
                      key={`limitation-${idx}-${limitation.slice(0, 20)}`}
                      className="text-sm text-orange-800 dark:text-orange-200"
                    >
                      • {limitation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Follow-up questions */}
        {structured.follow_up_questions &&
          structured.follow_up_questions.length > 0 && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 dark:text-green-300 mb-2">
                <FaQuestion size={14} />
                <span className="text-sm font-medium">Follow-up Questions</span>
              </div>
              <ul className="space-y-1">
                {structured.follow_up_questions.map((question, idx) => (
                  <li
                    key={`question-${idx}-${question.slice(0, 20)}`}
                    className="text-sm text-green-800 dark:text-green-200 cursor-pointer hover:text-green-900 dark:hover:text-green-100"
                  >
                    • {question}
                  </li>
                ))}
              </ul>
            </div>
          )}

        {/* Metadata */}
        {(structured.generation_time ||
          structured.tools_used ||
          structured.cost_info) && (
          <div>
            <button
              type="button"
              onClick={() => setShowMetadata(!showMetadata)}
              className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <HiCog size={12} />
              <span>Technical Details</span>
              {showMetadata ? (
                <FaChevronUp size={10} />
              ) : (
                <FaChevronDown size={10} />
              )}
            </button>
            {showMetadata && (
              <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-900/50 rounded text-xs text-gray-600 dark:text-gray-400 space-y-1">
                {structured.generation_time && (
                  <div className="flex items-center gap-2">
                    <FaClock size={10} />
                    <span>
                      Generated in {structured.generation_time.toFixed(2)}s
                    </span>
                  </div>
                )}
                {structured.tools_used && structured.tools_used.length > 0 && (
                  <div>Tools used: {structured.tools_used.join(", ")}</div>
                )}
                {structured.cost_info && (
                  <div>Cost: {JSON.stringify(structured.cost_info)}</div>
                )}
                {structured.factual_accuracy_score && (
                  <div>
                    Accuracy:{" "}
                    {(structured.factual_accuracy_score * 100).toFixed(0)}%
                  </div>
                )}
                {structured.completeness_score && (
                  <div>
                    Completeness:{" "}
                    {(structured.completeness_score * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  if (typeof message.content === "string") {
    return (
      <div
        className={`flex items-end gap-2 ${message.type === "user" ? "justify-end" : "justify-start"}`}
      >
        <div
          className={`flex flex-col items-start p-5 rounded-3xl animate-press-in text-sm lg:text-base ${colorTable[message.type]} ${message.isThinking ? "border-2 border-blue-300 dark:border-blue-600" : ""}`}
        >
          {message.cached && (
            <FaDatabase size={12} className="text-text-verba" />
          )}
          {message.isThinking && (
            <div className="flex items-center gap-2 mb-2 text-blue-600 dark:text-blue-400">
              <FaBrain size={16} />
              <span className="text-xs font-semibold">Thinking...</span>
            </div>
          )}

          {/* Render structured response if available */}
          {message.structured && renderStructuredResponse(message.structured)}

          {(message.type === "system" || message.type === "thinking") &&
            !message.structured && (
              <>
                {message.reasoningTrace &&
                  message.reasoningTrace.steps.length > 0 && (
                    <div className="w-full mb-3">
                      <button
                        type="button"
                        onClick={() => setShowReasoning(!showReasoning)}
                        className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                      >
                        <FaBrain size={14} />
                        <span>
                          Reasoning Steps ({message.reasoningTrace.steps.length}
                          )
                        </span>
                        {showReasoning ? (
                          <FaChevronUp size={12} />
                        ) : (
                          <FaChevronDown size={12} />
                        )}
                      </button>
                      {showReasoning && (
                        <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
                          {message.reasoningTrace.steps.map((step, idx) => (
                            <div
                              key={`step-${idx}-${step.slice(0, 20)}`}
                              className="mb-2 last:mb-0"
                            >
                              <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                                Step {idx + 1}:
                              </span>
                              <p className="text-xs mt-1 text-gray-700 dark:text-gray-300">
                                {step}
                              </p>
                            </div>
                          ))}
                          {message.reasoningTrace.confidence && (
                            <div className="mt-2 pt-2 border-t border-blue-200 dark:border-blue-700">
                              <span className="text-xs text-blue-700 dark:text-blue-300">
                                Confidence:{" "}
                                {(
                                  message.reasoningTrace.confidence * 100
                                ).toFixed(1)}
                                %
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                <ReactMarkdown
                  className="prose md:prose-sm lg:prose-base p-3 prose-pre:bg-bg-alt-verba"
                  components={{
                    code({ inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || "");
                      return !inline && match ? (
                        <pre
                          className={`language-${match[1]} p-4 rounded-lg overflow-x-auto ${selectedTheme.theme === "dark" ? "bg-gray-800" : "bg-gray-100"}`}
                        >
                          <code className={`language-${match[1]}`}>
                            {String(children).replace(/\n$/, "")}
                          </code>
                        </pre>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </>
            )}
          {message.type === "user" && (
            <div className="whitespace-pre-wrap">{message.content}</div>
          )}
          {message.type === "error" && (
            <div className="whitespace-pre-wrap flex items-center gap-2 text-sm text-text-verba">
              <BiError size={15} />
              <p>{message.content}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 w-full items-center">
      {message.content.map((document, index) => (
        <button
          type="button"
          onClick={() => {
            setSelectedDocument(document.uuid);
            setSelectedDocumentScore(
              document.uuid + document.score + document.chunks.length
            );
            setSelectedChunkScore(document.chunks);
          }}
          key={`Retrieval${document.title}${index}`}
          className={`flex ${selectedDocument && selectedDocument === document.uuid + document.score + document.chunks.length ? "bg-secondary-verba hover:bg-button-hover-verba" : "bg-button-verba hover:bg-secondary-verba"} rounded-3xl p-3 items-center justify-between transition-colors duration-300 ease-in-out border-none`}
        >
          <div className="flex items-center justify-between w-full">
            <p
              className="text-xs flex-grow truncate mr-2"
              title={document.title}
            >
              {document.title}
            </p>
            <div className="flex gap-1 items-center text-text-verba flex-shrink-0">
              <IoNewspaper size={12} />
              <p className="text-sm">{document.chunks.length}</p>
            </div>
          </div>
        </button>
      ))}
      <VerbaButton
        Icon={IoDocumentAttach}
        className="btn-sm btn-square"
        onClick={() =>
          (
            document.getElementById(
              `context-modal-${messageIndex}`
            ) as HTMLDialogElement
          ).showModal()
        }
      />
      <dialog id={`context-modal-${messageIndex}`} className="modal">
        <div className="modal-box">
          <h3 className="font-bold text-lg">Context</h3>
          <p className="py-4">{message.context}</p>
          <div className="modal-action">
            <form method="dialog">
              <button
                type="button"
                className="btn focus:outline-none text-text-alt-verba bg-button-verba hover:bg-button-hover-verba hover:text-text-verba border-none shadow-none"
              >
                <p>Close</p>
              </button>
            </form>
          </div>
        </div>
      </dialog>
    </div>
  );
};

export default ChatMessage;
