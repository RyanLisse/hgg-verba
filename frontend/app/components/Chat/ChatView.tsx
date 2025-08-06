"use client";

import type React from "react";
import { useState } from "react";
import ChatInterface from "./ChatInterface";

import DocumentExplorer from "../Document/DocumentExplorer";

import type {
  ChunkScore,
  Credentials,
  DocumentFilter,
  PageType, // Add this import
  RAGConfig,
  Theme,
} from "@/app/types";

interface ChatViewProps {
  selectedTheme: Theme;
  credentials: Credentials;
  addStatusMessage: (
    message: string,
    type: "INFO" | "WARNING" | "SUCCESS" | "ERROR"
  ) => void;
  production: "Local" | "Demo" | "Production";
  currentPage: PageType; // Update this type
  ragConfig: RAGConfig | null;
  setRagConfig: React.Dispatch<React.SetStateAction<RAGConfig | null>>;
  documentFilter: DocumentFilter[];
  setDocumentFilter: React.Dispatch<React.SetStateAction<DocumentFilter[]>>;
  labels: string[];
  filterLabels: string[];
  setFilterLabels: React.Dispatch<React.SetStateAction<string[]>>;
}

const ChatView: React.FC<ChatViewProps> = ({
  credentials,
  selectedTheme,
  addStatusMessage,
  production,
  currentPage,
  ragConfig,
  setRagConfig,
  documentFilter,
  setDocumentFilter,
  labels,
  filterLabels,
  setFilterLabels,
}) => {
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [selectedChunkScore, setSelectedChunkScore] = useState<ChunkScore[]>(
    []
  );
  return (
    <div className="flex md:flex-row flex-col justify-center gap-3 h-[50vh] md:h-[80vh] ">
      <div
        className={`${selectedDocument ? "hidden md:flex md:w-[45vw]" : "w-full md:w-[45vw] md:flex"}`}
      >
        <ChatInterface
          addStatusMessage={addStatusMessage}
          production={production}
          credentials={credentials}
          selectedTheme={selectedTheme}
          setSelectedDocument={setSelectedDocument}
          setSelectedChunkScore={setSelectedChunkScore}
          currentPage={currentPage}
          ragConfig={ragConfig}
          setragConfig={setRagConfig}
          documentFilter={documentFilter}
          setDocumentFilter={setDocumentFilter}
          labels={labels}
          filterLabels={filterLabels}
          setFilterLabels={setFilterLabels}
        />
      </div>

      <div
        className={`${selectedDocument ? "md:w-[55vw] w-full flex" : "hidden md:flex md:w-[55vw]"}`}
      >
        <DocumentExplorer
          addStatusMessage={addStatusMessage}
          credentials={credentials}
          production={production}
          documentFilter={documentFilter}
          setDocumentFilter={setDocumentFilter}
          setSelectedDocument={setSelectedDocument}
          selectedTheme={selectedTheme}
          selectedDocument={selectedDocument}
          chunkScores={selectedChunkScore}
        />
      </div>
    </div>
  );
};

export default ChatView;
