"use client";

import React, { useState } from "react";
import { ChunkScore, Message } from "@/app/types";
import ReactMarkdown from "react-markdown";
import { FaDatabase } from "react-icons/fa";
import { BiError } from "react-icons/bi";
import { IoNewspaper, IoDocumentAttach } from "react-icons/io5";
import { FaBrain, FaChevronDown, FaChevronUp } from "react-icons/fa";

import VerbaButton from "../Navigation/VerbaButton";

import { Theme } from "@/app/types";

interface ChatMessageProps {
  message: Message;
  message_index: number;
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
  message_index,
  setSelectedDocumentScore,
  setSelectedChunkScore,
}) => {
  const [showReasoning, setShowReasoning] = useState(false);

  const colorTable = {
    user: "bg-bg-verba",
    system: "bg-bg-alt-verba",
    error: "bg-warning-verba",
    retrieval: "bg-bg-verba",
    thinking: "bg-blue-50 dark:bg-blue-900/20",
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
          {(message.type === "system" || message.type === "thinking") && (
            <>
              {message.reasoningTrace && message.reasoningTrace.steps.length > 0 && (
                <div className="w-full mb-3">
                  <button
                    onClick={() => setShowReasoning(!showReasoning)}
                    className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                  >
                    <FaBrain size={14} />
                    <span>Reasoning Steps ({message.reasoningTrace.steps.length})</span>
                    {showReasoning ? <FaChevronUp size={12} /> : <FaChevronDown size={12} />}
                  </button>
                  {showReasoning && (
                    <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
                      {message.reasoningTrace.steps.map((step, idx) => (
                        <div key={idx} className="mb-2 last:mb-0">
                          <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">Step {idx + 1}:</span>
                          <p className="text-xs mt-1 text-gray-700 dark:text-gray-300">{step}</p>
                        </div>
                      ))}
                      {message.reasoningTrace.confidence && (
                        <div className="mt-2 pt-2 border-t border-blue-200 dark:border-blue-700">
                          <span className="text-xs text-blue-700 dark:text-blue-300">
                            Confidence: {(message.reasoningTrace.confidence * 100).toFixed(1)}%
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
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <pre className={`language-${match[1]} p-4 rounded-lg overflow-x-auto ${selectedTheme.theme === "dark" ? "bg-gray-800" : "bg-gray-100"}`}>
                        <code className={`language-${match[1]}`}>
                          {String(children).replace(/\n$/, "")}
                        </code>
                      </pre>
                    ) : (
                      <code className={className}>{children}</code>
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
  } else {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 w-full items-center">
        {message.content.map((document, index) => (
          <button
            onClick={() => {
              setSelectedDocument(document.uuid);
              setSelectedDocumentScore(
                document.uuid + document.score + document.chunks.length
              );
              setSelectedChunkScore(document.chunks);
            }}
            key={"Retrieval" + document.title + index}
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
                "context-modal-" + message_index
              ) as HTMLDialogElement
            ).showModal()
          }
        />
        <dialog id={"context-modal-" + message_index} className="modal">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Context</h3>
            <p className="py-4">{message.context}</p>
            <div className="modal-action">
              <form method="dialog">
                <button className="btn focus:outline-none text-text-alt-verba bg-button-verba hover:bg-button-hover-verba hover:text-text-verba border-none shadow-none">
                  <p>Close</p>
                </button>
              </form>
            </div>
          </div>
        </dialog>
      </div>
    );
  }
};

export default ChatMessage;
