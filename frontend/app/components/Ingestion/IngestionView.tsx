"use client";

import type {
  CreateNewDocument,
  Credentials,
  FileData,
  FileMap,
  StatusReport,
} from "@/app/types";
import type { RAGConfig } from "@/app/types";
import { getImportWebSocketApiHost } from "@/app/util";
import type {
  ConnectionState,
  ReconnectingWebSocket,
} from "@/app/utils/websocket";
import type React from "react";
import { useEffect, useState } from "react";
import ConfigurationView from "./ConfigurationView";
import FileSelectionView from "./FileSelectionView";

interface IngestionViewProps {
  credentials: Credentials;
  // biome-ignore lint/style/useNamingConvention: External API parameter
  RAGConfig: RAGConfig | null;
  setRAGConfig: React.Dispatch<React.SetStateAction<RAGConfig | null>>;
  addStatusMessage: (
    message: string,
    type: "INFO" | "WARNING" | "SUCCESS" | "ERROR"
  ) => void;
}

const IngestionView: React.FC<IngestionViewProps> = ({
  credentials,
  // biome-ignore lint/style/useNamingConvention: External API parameter
  RAGConfig,
  setRAGConfig,
  addStatusMessage,
}) => {
  const [fileMap, setFileMap] = useState<FileMap>({});
  const [selectedFileData, setSelectedFileData] = useState<string | null>(null);
  const [reconnect, setReconnect] = useState(false);
  const [socket, setSocket] = useState<
    WebSocket | ReconnectingWebSocket | null
  >(null);
  const [socketStatus, setSocketStatus] =
    useState<ConnectionState>("DISCONNECTED");
  const [_messageQueueSize, _setMessageQueueSize] = useState(0);

  useEffect(() => {
    setReconnect(true);
  }, []);

  // Setup Import WebSocket and messages
  useEffect(() => {
    let isComponentMounted = true;
    let cleanupFn: (() => void) | undefined;

    const connectWebSocket = async (attempt = 1) => {
      if (!isComponentMounted) return;

      const socketHost = getImportWebSocketApiHost();
      const localSocket = new WebSocket(socketHost);

      // Calculate exponential backoff delay with jitter
      const baseDelay = 1000 * 2 ** (attempt - 1);
      const jitter = Math.random() * 1000;
      const backoffDelay = Math.min(baseDelay + jitter, 30000); // Max 30 seconds
      const maxRetries = 5;

      localSocket.onopen = () => {
        if (!isComponentMounted) {
          localSocket.close(1000, "Component unmounted during connection");
          return;
        }
        setSocketStatus("CONNECTED");
      };

      localSocket.onmessage = (event) => {
        if (!isComponentMounted) return;
        setSocketStatus("CONNECTED");
        try {
          const data: StatusReport | CreateNewDocument | { type: string } =
            JSON.parse(event.data);

          // Handle pong messages
          if ("type" in data && data.type === "pong") {
            return; // Pong received, connection is alive
          }

          if ("new_file_id" in data) {
            setFileMap((prevFileMap) => {
              const newFileMap: FileMap = { ...prevFileMap };
              newFileMap[data.new_file_id] = {
                ...newFileMap[data.original_file_id],
                fileID: data.new_file_id,
                filename: data.filename,
                block: true,
              };
              return newFileMap;
            });
          } else {
            updateStatus(data as StatusReport);
          }
        } catch (_e) {
          console.error("Received data is not valid JSON:", event.data);
          return;
        }
      };

      localSocket.onerror = (error) => {
        if (!isComponentMounted) return;
        console.error("Import WebSocket Error:", error);
        setSocketStatus("DISCONNECTED");
      };

      localSocket.onclose = (event) => {
        if (!isComponentMounted) return;
        setSocketStatus("DISCONNECTED");
        setSocketErrorStatus();

        if (event.wasClean) {
          // Don't reconnect on clean close
          return;
        }

        console.error("WebSocket connection died");

        // Only retry if within max retries
        if (attempt < maxRetries) {
          setTimeout(() => {
            if (isComponentMounted) {
              connectWebSocket(attempt + 1);
            }
          }, backoffDelay);
        } else {
          addStatusMessage(
            "Connection lost. Please refresh the page.",
            "ERROR"
          );
        }
      };

      setSocket(localSocket);

      // Add ping/pong for keepalive
      const pingInterval = setInterval(() => {
        if (localSocket.readyState === WebSocket.OPEN) {
          localSocket.send(JSON.stringify({ type: "ping" }));
        }
      }, 30000); // Send ping every 30 seconds

      cleanupFn = () => {
        clearInterval(pingInterval);
        if (localSocket.readyState !== WebSocket.CLOSED) {
          localSocket.close(1000, "Component unmounting");
        }
      };
    };

    connectWebSocket();

    return () => {
      isComponentMounted = false;
      if (cleanupFn) cleanupFn();
      if (
        socket &&
        "readyState" in socket &&
        socket.readyState !== WebSocket.CLOSED
      ) {
        socket.close(1000, "Component unmounting");
      }
    };
  }, [reconnect, addStatusMessage]);

  const reconnectToVerba = () => {
    setReconnect((prevState) => !prevState);
  };

  const setSocketErrorStatus = () => {
    setFileMap((prevFileMap) => {
      if (fileMap) {
        const newFileMap = { ...prevFileMap };
        for (const fileMapKey in newFileMap) {
          if (
            newFileMap[fileMapKey].status !== "DONE" &&
            newFileMap[fileMapKey].status !== "ERROR" &&
            newFileMap[fileMapKey].status !== "READY"
          ) {
            newFileMap[fileMapKey].status = "ERROR";
            newFileMap[fileMapKey].status_report.ERROR = {
              fileID: fileMapKey,
              status: "ERROR",
              message: "Connection was interrupted",
              took: 0,
            };
          }
        }
        return newFileMap;
      }
      return prevFileMap;
    });
  };

  const updateStatus = (data: StatusReport) => {
    if (data.status === "DONE") {
      addStatusMessage(`File ${data.fileID} imported`, "SUCCESS");
    }
    if (data.status === "ERROR") {
      addStatusMessage(`File ${data.fileID} import failed`, "ERROR");
    }
    setFileMap((prevFileMap) => {
      if (data && data.fileID in prevFileMap) {
        const newFileData: FileData = JSON.parse(
          JSON.stringify(prevFileMap[data.fileID])
        );
        const newFileMap: FileMap = { ...prevFileMap };
        newFileData.status = data.status;
        newFileData.status_report[data.status] = data;
        newFileMap[data.fileID] = newFileData;
        return newFileMap;
      }
      return prevFileMap;
    });
  };

  const setInitialStatus = (fileID: string) => {
    setFileMap((prevFileMap) => {
      if (fileID in prevFileMap) {
        const newFileData: FileData = JSON.parse(
          JSON.stringify(prevFileMap[fileID])
        );
        const newFileMap: FileMap = { ...prevFileMap };
        newFileData.status = "WAITING";
        if (Object.entries(newFileData.status_report).length > 0) {
          newFileData.status_report = {};
        }
        newFileMap[fileID] = newFileData;
        return newFileMap;
      }
      return prevFileMap;
    });
  };

  const importSelected = () => {
    addStatusMessage("Importing selected file", "INFO");
    if (
      selectedFileData &&
      ["READY", "DONE", "ERROR"].includes(fileMap[selectedFileData].status) &&
      !fileMap[selectedFileData].block
    ) {
      sendDataBatches(
        JSON.stringify(fileMap[selectedFileData]),
        selectedFileData
      );
    }
  };

  const importAll = () => {
    addStatusMessage("Importing all files", "INFO");
    for (const fileID in fileMap) {
      if (
        ["READY", "DONE", "ERROR"].includes(fileMap[fileID].status) &&
        !fileMap[fileID].block
      ) {
        sendDataBatches(JSON.stringify(fileMap[fileID]), fileID);
      }
    }
  };

  const sendDataBatches = (data: string, fileID: string) => {
    if (
      socket &&
      "readyState" in socket &&
      socket.readyState === WebSocket.OPEN
    ) {
      setInitialStatus(fileID);
      const chunkSize = 2000; // Define chunk size (in bytes)
      const batches = [];
      let offset = 0;

      // Create the batches
      while (offset < data.length) {
        const chunk = data.slice(offset, offset + chunkSize);
        batches.push(chunk);
        offset += chunkSize;
      }

      const totalBatches = batches.length;

      // Send the batches
      batches.forEach((chunk, order) => {
        socket.send(
          JSON.stringify({
            chunk: chunk,
            isLastChunk: order === totalBatches - 1,
            total: totalBatches,
            order: order,
            fileID: fileID,
            credentials: credentials,
          })
        );
      });
    } else {
      console.error(
        "WebSocket is not open. ReadyState:",
        socket && "readyState" in socket ? socket.readyState : "unknown"
      );
      setReconnect((prevState) => !prevState);
    }
  };

  return (
    <div className="flex justify-center gap-3 h-[80vh] ">
      <div
        className={`${selectedFileData ? "hidden md:flex md:w-[45vw]" : "w-full md:w-[45vw] md:flex"}`}
      >
        <FileSelectionView
          fileMap={fileMap}
          addStatusMessage={addStatusMessage}
          setFileMap={setFileMap}
          ragConfig={RAGConfig}
          setragConfig={setRAGConfig}
          selectedFileData={selectedFileData}
          setSelectedFileData={setSelectedFileData}
          importSelected={importSelected}
          importAll={importAll}
          socketStatus={socketStatus === "CONNECTED" ? "ONLINE" : "OFFLINE"}
          reconnect={reconnectToVerba}
        />
      </div>

      <div
        className={`${selectedFileData ? "md:w-[55vw] w-full flex" : "hidden md:flex md:w-[55vw]"}`}
      >
        {selectedFileData && (
          <ConfigurationView
            addStatusMessage={addStatusMessage}
            selectedFileData={selectedFileData}
            ragConfig={RAGConfig}
            credentials={credentials}
            setragConfig={setRAGConfig}
            fileMap={fileMap}
            setFileMap={setFileMap}
            setSelectedFileData={setSelectedFileData}
          />
        )}
      </div>
    </div>
  );
};

export default IngestionView;
