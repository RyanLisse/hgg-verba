"use client";

import React, { useState, useEffect, useRef } from "react";
import { MdCancel, MdOutlineRefresh } from "react-icons/md";
import { TbPlugConnected } from "react-icons/tb";
import { IoChatbubbleSharp } from "react-icons/io5";
import { FaHammer } from "react-icons/fa";
import { IoIosSend } from "react-icons/io";
import { BiError } from "react-icons/bi";
import { IoMdAddCircle } from "react-icons/io";

import VerbaButton from "../Navigation/VerbaButton";
import SimpleFeedback from "./SimpleFeedback";

import {
  updateRAGConfig,
  sendUserQuery,
  fetchDatacount,
  fetchRAGConfig,
  fetchSuggestions,
  fetchLabels,
} from "@/app/api";
import { getWebSocketApiHost, logMessage } from "@/app/util";
import { ReconnectingWebSocket, ConnectionState } from "@/app/utils/websocket";

import {
  Credentials,
  QueryPayload,
  Suggestion,
  DataCountPayload,
  ChunkScore,
  Message,
  LabelsResponse,
  RAGConfig,
  Theme,
  DocumentFilter,
  PageType,
} from "@/app/types";

import InfoComponent from "../Navigation/InfoComponent";
import ChatConfig from "./ChatConfig";
import ChatMessage from "./ChatMessage";

interface ChatInterfaceProps {
  credentials: Credentials;
  setSelectedDocument: (s: string | null) => void;
  setSelectedChunkScore: (c: ChunkScore[]) => void;
  currentPage: PageType;
  RAGConfig: RAGConfig | null;
  setRAGConfig: React.Dispatch<React.SetStateAction<RAGConfig | null>>;
  selectedTheme: Theme;
  production: "Local" | "Demo" | "Production";
  addStatusMessage: (
    message: string,
    type: "INFO" | "WARNING" | "SUCCESS" | "ERROR"
  ) => void;
  documentFilter: DocumentFilter[];
  setDocumentFilter: React.Dispatch<React.SetStateAction<DocumentFilter[]>>;
  labels: string[];
  filterLabels: string[];
  setFilterLabels: React.Dispatch<React.SetStateAction<string[]>>;
}

interface WebSocketMessage {
  message: string;
  finish_reason: string | null;
  full_text?: string;
  cached?: boolean;
  distance?: string;
  runId?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  production,
  credentials,
  setSelectedDocument,
  setSelectedChunkScore,
  currentPage,
  RAGConfig,
  selectedTheme,
  setRAGConfig,
  addStatusMessage,
  documentFilter,
  setDocumentFilter,
  labels,
  filterLabels,
  setFilterLabels,
}) => {
  const [selectedSetting, setSelectedSetting] = useState<"Chat" | "Config">(
    "Chat"
  );

  // Manages whether data is currently being fetched
  const isFetching = useRef<boolean>(false);
  const [fetchingStatus, setFetchingStatus] = useState<
    "DONE" | "CHUNKS" | "RESPONSE"
  >("DONE");

  // For real-time text updates
  const [previewText, setPreviewText] = useState("");

  // WebSocket state
  const [socket, setSocket] = useState<ReconnectingWebSocket | null>(null);
  const [socketStatus, setSocketStatus] = useState<ConnectionState>(
    "DISCONNECTED"
  );
  const [messageQueueSize, setMessageQueueSize] = useState(0);

  // Suggestions
  const [currentSuggestions, setCurrentSuggestions] = useState<Suggestion[]>([]);

  // Document data
  const [selectedDocumentScore, setSelectedDocumentScore] = useState<
    string | null
  >(null);

  // Data count in the DB
  const [currentDatacount, setCurrentDatacount] = useState(0);

  // Chat user input & messages
  const [userInput, setUserInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  // Retrieve current embedder model
  const currentEmbedding = RAGConfig
    ? (RAGConfig.Embedder.components[RAGConfig.Embedder.selected].config.Model
        .value as string)
    : "No Config found";

  /**
   * Connect to the WebSocket with automatic reconnection.
   */
  useEffect(() => {
    const ws = new ReconnectingWebSocket("/ws/generate_stream", {
      maxRetries: 5,
      initialRetryDelay: 1000,
      maxRetryDelay: 30000,
      heartbeatInterval: 30000,
      reconnectOnError: true,
      messageQueueSize: 10,
    });

    // Set up event handlers
    ws.on("stateChange", (newState: ConnectionState) => {
      setSocketStatus(newState);
      if (newState === "DISCONNECTED" || newState === "ERROR") {
        addStatusMessage("WebSocket disconnected", "WARNING");
      } else if (newState === "CONNECTED") {
        addStatusMessage("WebSocket connected", "SUCCESS");
      }
    });

    ws.on("message", (data: WebSocketMessage | { type: string }) => {
      // If we aren't actively fetching, ignore messages
      if (!isFetching.current) {
        setPreviewText("");
        return;
      }

      const wsMessage = data as WebSocketMessage;
      const newMessageContent = wsMessage.message;
      setPreviewText((prev) => prev + newMessageContent);

      if (wsMessage.finish_reason === "stop") {
        isFetching.current = false;
        setFetchingStatus("DONE");
        addStatusMessage("Finished generation", "SUCCESS");
        const full_text = wsMessage.full_text;
        if (wsMessage.cached) {
          setMessages((prev) => [
            ...prev,
            {
              type: "system",
              content: full_text || "",
              cached: true,
              distance: wsMessage.distance,
              runId: wsMessage.runId,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              type: "system",
              content: full_text || "",
              runId: wsMessage.runId,
            },
          ]);
        }
        setPreviewText("");
      }
    });

    ws.on("error", (error: Error) => {
      console.error("WebSocket Error:", error);
    });

    ws.on("close", (event: CloseEvent) => {
      if (event.wasClean) {
        console.log(
          `WebSocket closed cleanly, code=${event.code}, reason=${event.reason}`
        );
      }
    });

    ws.on("messageQueued", () => {
      setMessageQueueSize(ws.getQueueSize());
    });

    ws.on("sent", () => {
      setMessageQueueSize(ws.getQueueSize());
    });

    // Connect the WebSocket
    ws.connect();
    setSocket(ws);

    // Cleanup
    return () => {
      ws.disconnect();
    };
  }, [addStatusMessage]);

  /**
   * When RAGConfig changes, retrieve the current document count.
   */
  useEffect(() => {
    if (RAGConfig) {
      retrieveDatacount();
    } else {
      setCurrentDatacount(0);
    }
  }, [RAGConfig]);

  /**
   * Reload from server the RAGConfig.
   */
  const retrieveRAGConfig = async () => {
    const config = await fetchRAGConfig(credentials);
    if (config) {
      setRAGConfig(config.rag_config);
    } else {
      addStatusMessage("Failed to fetch RAG Config", "ERROR");
    }
  };

  /**
   * Send the user's question to the server.
   */
  const sendUserMessage = async () => {
    if (isFetching.current || !userInput.trim()) return;

    const sendInput = userInput;
    setUserInput("");
    isFetching.current = true;
    setCurrentSuggestions([]);
    setFetchingStatus("CHUNKS");
    setMessages((prev) => [...prev, { type: "user", content: sendInput }]);

    try {
      addStatusMessage("Sending query...", "INFO");
      const data = await sendUserQuery(
        sendInput,
        RAGConfig,
        filterLabels,
        documentFilter,
        credentials
      );

      if (!data || data.error) {
        handleErrorResponse(data?.error || "No data received");
      } else {
        handleSuccessResponse(data, sendInput);
      }
    } catch (error) {
      handleErrorResponse("Failed to fetch from API");
      console.error("Failed to fetch from API:", error);
    }
  };

  /**
   * Handle an error response from the server.
   * @param errorMessage 
   */
  const handleErrorResponse = (errorMessage: string) => {
    addStatusMessage("Query failed", "ERROR");
    setMessages((prev) => [...prev, { type: "error", content: errorMessage }]);
    isFetching.current = false;
    setFetchingStatus("DONE");
  };

  /**
   * Handle a successful QueryPayload from the server.
   * @param data 
   * @param sendInput 
   */
  const handleSuccessResponse = (data: QueryPayload, sendInput: string) => {
    // Show retrieval documents
    setMessages((prev) => [
      ...prev,
      { type: "retrieval", content: data.documents, context: data.context },
    ]);

    addStatusMessage(
      "Received " + Object.entries(data.documents).length + " documents",
      "SUCCESS"
    );

    if (data.documents.length > 0) {
      const firstDoc = data.documents[0];
      setSelectedDocument(firstDoc.uuid);
      setSelectedDocumentScore(
        `${firstDoc.uuid}${firstDoc.score}${firstDoc.chunks.length}`
      );
      setSelectedChunkScore(firstDoc.chunks);

      if (data.context) {
        streamResponses(sendInput, data.context);
        setFetchingStatus("RESPONSE");
      }
    } else {
      handleErrorResponse("We couldn't find any chunks to your query");
    }
  };

  /**
   * Open the WebSocket channel and stream the response for generation.
   * @param query 
   * @param context 
   */
  const streamResponses = (query?: string, context?: string) => {
    if (socket?.isConnected()) {
      const filteredMessages = messages
        // keep only user/system for context
        .filter((msg) => msg.type === "user" || msg.type === "system")
        .map((msg) => ({
          type: msg.type,
          content: msg.content as string,
        }));

      const data = {
        query,
        context,
        conversation: filteredMessages,
        rag_config: RAGConfig,
      };
      socket.send(data);
    } else {
      console.error("WebSocket is not connected. State:", socket?.getState());
      addStatusMessage("WebSocket not connected. Message queued.", "WARNING");
    }
  };

  /**
   * Listen for Enter key to send message.
   * @param e 
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevent line break
      sendUserMessage();
    }
  };

  /**
   * Retrieve doc count + labels from the server
   */
  const retrieveDatacount = async () => {
    try {
      const data: DataCountPayload | null = await fetchDatacount(
        currentEmbedding,
        documentFilter,
        credentials
      );
      const labelResp: LabelsResponse | null = await fetchLabels(credentials);

      if (data) {
        setCurrentDatacount(data.datacount);
      }
      if (labelResp) {
        // We'll let parent setLabels if needed. For local usage, we do nothing.
      }
    } catch (error) {
      console.error("Failed to fetch from API:", error);
      addStatusMessage("Failed to fetch datacount: " + error, "ERROR");
    }
  };

  /**
   * Button action to reconnect to the WebSocket.
   */
  const reconnectToVerba = () => {
    if (socket) {
      socket.reconnect();
    }
  };

  /**
   * Save the updated RAGConfig
   */
  const onSaveConfig = async () => {
    try {
      const response = await updateRAGConfig(RAGConfig, credentials);
      if (response) {
        addStatusMessage("Config saved successfully", "SUCCESS");
        // Refresh the config from server to ensure it's persisted
        await retrieveRAGConfig();
      } else {
        addStatusMessage("Failed to save config", "ERROR");
      }
    } catch (error) {
      console.error("Error saving config:", error);
      addStatusMessage("Error saving config", "ERROR");
    }
  };

  /**
   * Reset RAGConfig from server
   */
  const onResetConfig = async () => {
    addStatusMessage("Reset Config", "WARNING");
    retrieveRAGConfig();
  };

  /**
   * Show suggestions as user types
   */
  const handleSuggestions = async () => {
    try {
      // If your retriever config has "Suggestion" key, then call suggestions
      if (
        RAGConfig &&
        RAGConfig.Retriever.components[RAGConfig.Retriever.selected].config
          .Suggestion?.value
      ) {
        const suggestions = await fetchSuggestions(userInput, 3, credentials);
        if (suggestions) {
          setCurrentSuggestions(suggestions.suggestions);
        }
      }
    } catch (error) {
      console.error("Error fetching suggestions:", error);
    }
  };

  /**
   * Helper method for feedback submission
   */
  const handleFeedbackSubmit = async (
    runId: string,
    feedbackType: string,
    additionalFeedback: string
  ) => {
    logMessage("Feedback submission triggered", {
      runId,
      feedbackType,
      additionalFeedback,
    });
    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          runId,
          feedbackType,
          additionalFeedback,
          credentials,
        }),
      });

      if (response.ok) {
        logMessage("Feedback submitted successfully", { runId });
        addStatusMessage("Feedback submitted successfully", "SUCCESS");
      } else {
        logMessage("Failed to submit feedback", {
          runId,
          status: response.status,
        });
        addStatusMessage("Failed to submit feedback", "ERROR");
      }
    } catch (error) {
      logMessage("Error submitting feedback", { runId, error });
      console.error("Error submitting feedback:", error);
      addStatusMessage("Error submitting feedback", "ERROR");
    }
  };

  /**
   * Grab the last system runId for feedback
   */
  const getLastRunId = (): string => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      return lastMessage.type === "system" && lastMessage.runId
        ? lastMessage.runId
        : "";
    }
    return "";
  };

  /**
   * Clear all chat states
   */
  const clearAll = () => {
    setSelectedDocument(null);
    setSelectedChunkScore([]);
    setUserInput("");
    setSelectedDocumentScore(null);
    setCurrentSuggestions([]);
    setMessages([
      {
        type: "system",
        content: selectedTheme.intro_message.text,
      },
    ]);
  };

  return (
    <div className="flex flex-col gap-2 w-full">
      {/* Header */}
      <div className="bg-bg-alt-verba rounded-2xl flex flex-col md:flex-row gap-2 p-4 md:p-6 items-center justify-between h-min w-full">
        <div className="hidden md:flex gap-2 justify-start items-center">
          <InfoComponent
            tooltip_text="Use the Chat interface to interact with your data and perform Retrieval Augmented Generation (RAG)."
            display_text="Chat"
          />
          {/* Connection Status Indicator */}
          <div className="flex items-center gap-2 ml-4">
            <div className={`w-2 h-2 rounded-full ${
              socketStatus === "CONNECTED" ? "bg-green-500" :
              socketStatus === "CONNECTING" || socketStatus === "RECONNECTING" ? "bg-yellow-500 animate-pulse" :
              "bg-red-500"
            }`} />
            <span className="text-xs text-text-alt-verba">
              {socketStatus === "CONNECTED" ? "Connected" :
               socketStatus === "CONNECTING" ? "Connecting..." :
               socketStatus === "RECONNECTING" ? "Reconnecting..." :
               "Disconnected"}
            </span>
            {messageQueueSize > 0 && (
              <span className="text-xs text-warning-verba ml-2">
                ({messageQueueSize} queued)
              </span>
            )}
          </div>
        </div>

        <div className="w-full md:w-fit flex gap-3 justify-end items-center">
          <VerbaButton
            title="Chat"
            Icon={IoChatbubbleSharp}
            onClick={() => setSelectedSetting("Chat")}
            selected={selectedSetting === "Chat"}
            disabled={false}
            selected_color="bg-secondary-verba"
          />
          {production !== "Demo" && (
            <VerbaButton
              title="Config"
              Icon={FaHammer}
              onClick={() => setSelectedSetting("Config")}
              selected={selectedSetting === "Config"}
              disabled={false}
              selected_color="bg-secondary-verba"
            />
          )}
        </div>
      </div>

      {/* Main Panel */}
      <div className="bg-bg-alt-verba rounded-2xl flex flex-col h-[50vh] md:h-full w-full overflow-y-auto overflow-x-hidden relative p-2 md:p-4">
        {/* If Chat tab selected, show filter area */}
        {selectedSetting === "Chat" && (
          <div className="sticky flex flex-col gap-2 top-0 z-9 p-4 backdrop-blur-sm bg-opacity-30 bg-bg-alt-verba rounded-lg">
            <div className="flex gap-2 justify-start items-center">
              <div className="flex gap-2">
                <div className="dropdown dropdown-hover">
                  <label tabIndex={0}>
                    <VerbaButton
                      title="Label"
                      className="btn-sm min-w-min"
                      icon_size={12}
                      text_class_name="text-xs"
                      Icon={IoMdAddCircle}
                      selected={false}
                      disabled={false}
                    />
                  </label>
                  <ul
                    tabIndex={0}
                    className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52"
                  >
                    {labels.map((label, index) => (
                      <li key={"Label" + index}>
                        <a
                          onClick={() => {
                            if (!filterLabels.includes(label)) {
                              setFilterLabels([...filterLabels, label]);
                            }
                            // Close the dropdown
                            const dropdownElement =
                              document.activeElement as HTMLElement;
                            dropdownElement.blur();
                            const dropdown = dropdownElement.closest(".dropdown");
                            if (dropdown instanceof HTMLElement) dropdown.blur();
                          }}
                        >
                          {label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {(filterLabels.length > 0 || documentFilter.length > 0) && (
                <VerbaButton
                  onClick={() => {
                    setFilterLabels([]);
                    setDocumentFilter([]);
                  }}
                  title="Clear"
                  className="btn-sm max-w-min"
                  icon_size={12}
                  text_class_name="text-xs"
                  Icon={MdCancel}
                  selected={false}
                  disabled={false}
                />
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {filterLabels.map((label, index) => (
                <VerbaButton
                  title={label}
                  key={"FilterLabel" + index}
                  Icon={MdCancel}
                  className="btn-sm min-w-min max-w-[200px]"
                  icon_size={12}
                  selected_color="bg-primary-verba"
                  selected
                  text_class_name="truncate max-w-[200px]"
                  text_size="text-xs"
                  onClick={() => {
                    setFilterLabels(filterLabels.filter((l) => l !== label));
                  }}
                />
              ))}
              {documentFilter.map((filter, index) => (
                <VerbaButton
                  title={filter.title}
                  key={"DocumentFilter" + index}
                  Icon={MdCancel}
                  className="btn-sm min-w-min max-w-[200px]"
                  icon_size={12}
                  selected_color="bg-primary-verba"
                  selected
                  text_size="text-xs"
                  text_class_name="truncate md:max-w-[100px] lg:max-w-[150px]"
                  onClick={() => {
                    setDocumentFilter(
                      documentFilter.filter((f) => f.uuid !== filter.uuid)
                    );
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Chat or Config */}
        <div
          className={`${
            selectedSetting === "Chat" ? "flex flex-col gap-3 p-4" : "hidden"
          }`}
        >
          <div className="flex w-full justify-start items-center text-text-alt-verba gap-2">
            {currentDatacount === 0 && <BiError size={15} />}
            {currentDatacount === 0 && (
              <p className="text-text-alt-verba text-sm items-center flex">
                {`${currentDatacount} documents embedded by ${currentEmbedding}`}
              </p>
            )}
          </div>

          {messages.map((message, index) => (
            <div
              key={"Message_" + index}
              className={message.type === "user" ? "text-right" : ""}
            >
              <ChatMessage
                message={message}
                message_index={index}
                selectedTheme={selectedTheme}
                selectedDocument={selectedDocumentScore}
                setSelectedDocumentScore={setSelectedDocumentScore}
                setSelectedDocument={setSelectedDocument}
                setSelectedChunkScore={setSelectedChunkScore}
              />
            </div>
          ))}

          {previewText && (
            <ChatMessage
              message={{ type: "system", content: previewText }}
              message_index={-1}
              selectedTheme={selectedTheme}
              selectedDocument={selectedDocumentScore}
              setSelectedDocumentScore={setSelectedDocumentScore}
              setSelectedDocument={setSelectedDocument}
              setSelectedChunkScore={setSelectedChunkScore}
            />
          )}

          {/* Loading Indicator */}
          {isFetching.current && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <span className="text-text-alt-verba loading loading-dots loading-md"></span>
                <p className="text-text-alt-verba">
                  {fetchingStatus === "CHUNKS" && "Retrieving..."}
                  {fetchingStatus === "RESPONSE" && "Generating..."}
                </p>
                <button
                  onClick={() => {
                    setFetchingStatus("DONE");
                    isFetching.current = false;
                  }}
                  className="btn btn-circle btn-sm bg-bg-alt-verba hover:bg-warning-verba hover:text-text-verba text-text-alt-verba shadow-none border-none text-sm"
                >
                  <MdCancel size={15} />
                </button>
              </div>
            </div>
          )}
        </div>

        {selectedSetting === "Config" && (
          <ChatConfig
            addStatusMessage={addStatusMessage}
            production={production}
            RAGConfig={RAGConfig}
            credentials={credentials}
            setRAGConfig={setRAGConfig}
            onReset={onResetConfig}
            onSave={onSaveConfig}
          />
        )}
      </div>

      {/* Footer input / Reconnections */}
      <div className="bg-bg-alt-verba rounded-2xl flex flex-col md:flex-row gap-2 p-4 md:p-6 items-center justify-end h-min w-full">
        {socketStatus === "CONNECTED" ? (
          <div className="flex flex-col w-full gap-2">
            <div className="flex items-center gap-2">
              <div className="relative w-full">
                <textarea
                  className="textarea textarea-bordered w-full bg-bg-verba placeholder-text-alt-verb min-h min-h-[40px] max-h-[150px] overflow-y-auto"
                  placeholder={
                    currentDatacount > 0
                      ? currentDatacount >= 100
                        ? `Chatting with more than 100 documents...`
                        : `Chatting with ${currentDatacount} documents...`
                      : `No documents detected...`
                  }
                  onKeyDown={handleKeyDown}
                  value={userInput}
                  onChange={(e) => {
                    const newValue = e.target.value;
                    setUserInput(newValue);
                    if ((newValue.length - 1) % 3 === 0) {
                      handleSuggestions();
                    }
                  }}
                />
              </div>
              <VerbaButton
                type="button"
                Icon={IoIosSend}
                onClick={sendUserMessage}
                disabled={false}
                selected_color="bg-primary-verba"
              />
            </div>

            <div className="flex gap-2 items-center justify-end">
              <VerbaButton
                type="button"
                Icon={MdOutlineRefresh}
                onClick={clearAll}
                disabled={false}
                selected_color="bg-primary-verba"
              />
              <SimpleFeedback runId={getLastRunId()} onSubmit={handleFeedbackSubmit} />
            </div>

            {currentSuggestions.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-text-alt-verba mb-1">Suggestions:</p>
                <ul className="flex flex-wrap gap-2 w-full">
                  {currentSuggestions.map((suggestion, index) => (
                    <li
                      key={index}
                      className="p-2 bg-button-verba hover:bg-secondary-verba text-text-alt-verba rounded-xl hover:text-text-verba cursor-pointer text-xs lg:text-sm"
                      onClick={() => {
                        setUserInput(suggestion.query);
                        setCurrentSuggestions([]);
                      }}
                    >
                      {suggestion.query.length > 50
                        ? suggestion.query.substring(0, 50) + "..."
                        : suggestion.query}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="flex gap-2 items-center justify-end w-full">
            <button
              onClick={reconnectToVerba}
              className="flex btn border-none text-text-verba bg-button-verba hover:bg-button-hover-verba gap-2 items-center"
            >
              <TbPlugConnected size={15} />
              <p>{socketStatus === "RECONNECTING" ? "Reconnecting..." : "Reconnect"}</p>
              {socketStatus === "RECONNECTING" && (
                <span className="loading loading-spinner loading-xs"></span>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
