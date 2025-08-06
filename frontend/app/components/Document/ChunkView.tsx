"use client";

import type { ChunksPayload, Theme, VerbaChunk } from "@/app/types";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { IoChevronBack, IoChevronForward } from "react-icons/io5";
import ReactMarkdown from "react-markdown";

import { fetchChunks } from "@/app/api";
import type { Credentials } from "@/app/types";

import VerbaButton from "../Navigation/VerbaButton";

interface ChunkViewProps {
  selectedDocument: string | null;
  selectedTheme: Theme;
  credentials: Credentials;
}

const ChunkView: React.FC<ChunkViewProps> = ({
  selectedDocument,
  credentials,
  selectedTheme,
}) => {
  const [isFetching, setIsFetching] = useState(false);
  const [chunks, setChunks] = useState<VerbaChunk[]>([]);
  const [page, setPage] = useState(1);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [isPreviousDisabled, setIsPreviousDisabled] = useState(true);

  const pageSize = 10;

  const fetchChunksData = useCallback(
    async (pageNumber: number) => {
      try {
        setIsFetching(true);

        const data: ChunksPayload | null = await fetchChunks(
          selectedDocument,
          pageNumber,
          pageSize,
          credentials
        );

        if (data) {
          if (data.error !== "") {
            console.error(data.error);
            setIsFetching(false);
            setChunks([]);
            return false; // No more chunks available
          }
          setChunks(data.chunks);
          setIsFetching(false);
          return data.chunks.length > 0; // Return true if chunks were fetched
        }
        return false; // No more chunks available
      } catch (error) {
        console.error("Failed to fetch document:", error);
        setIsFetching(false);
        return false; // No more chunks available
      }
    },
    [selectedDocument, credentials]
  );

  useEffect(() => {
    fetchChunksData(page);
    setIsPreviousDisabled(page === 1 && currentChunkIndex === 0);
  }, [page, currentChunkIndex, fetchChunksData]);

  useEffect(() => {
    if (selectedDocument) {
      fetchChunksData(1);
      setCurrentChunkIndex(0);
      setPage(1);
      setIsPreviousDisabled(true);
    }
  }, [selectedDocument, fetchChunksData]);

  const nextChunk = async () => {
    if (currentChunkIndex === chunks.length - 1) {
      const hasMoreChunks = await fetchChunksData(page + 1);
      if (hasMoreChunks) {
        setPage((prev) => prev + 1);
        setCurrentChunkIndex(0);
      } else {
        await fetchChunksData(1);
        setPage(1);
        setCurrentChunkIndex(0);
      }
    } else {
      setCurrentChunkIndex((prev) => prev + 1);
    }
  };

  const previousChunk = async () => {
    if (currentChunkIndex === 0) {
      if (page > 1) {
        const prevPage = page - 1;
        const hasChunks = await fetchChunksData(prevPage);
        if (hasChunks) {
          setPage(prevPage);
          setCurrentChunkIndex(pageSize - 1);
        }
      } else {
        let lastPage = page;
        let hasMoreChunks = true;
        while (hasMoreChunks) {
          hasMoreChunks = await fetchChunksData(lastPage + 1);
          if (hasMoreChunks) lastPage++;
        }
        await fetchChunksData(lastPage);
        setPage(lastPage);
        setCurrentChunkIndex(chunks.length - 1);
      }
    } else {
      setCurrentChunkIndex((prev) => prev - 1);
    }
  };

  if (chunks.length === 0) {
    return (
      <div>
        {isFetching && (
          <div className="flex items-center justify-center text-text-verba gap-2 h-full">
            <span className="loading loading-spinner loading-sm" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {chunks.length > 0 && (
        <div className="bg-bg-alt-verba flex flex-col rounded-lg overflow-hidden h-full">
          {/* Content div */}
          <div className="flex-grow overflow-hidden p-3">
            <div className="flex justify-between mb-2">
              <div className="flex gap-2">
                <div className="flex gap-2 items-center p-3 bg-secondary-verba rounded-full w-fit">
                  <IoChevronBack size={12} />
                  <p className="text-xs flex text-text-verba">
                    Chunk {chunks[currentChunkIndex].chunk_id}
                  </p>
                </div>
              </div>
            </div>
            <div className="overflow-y-auto h-[calc(100%-3rem)]">
              <ReactMarkdown
                className="max-w-[50vw] items-center justify-center flex-wrap md:prose-base sm:prose-sm p-3 prose-pre:bg-bg-alt-verba"
                components={{
                  code({ node, inline, className, children, ..._props }) {
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
                      <code className={className}>{children}</code>
                    );
                  },
                }}
              >
                {chunks[currentChunkIndex].content}
              </ReactMarkdown>
            </div>
          </div>

          {/* Navigation div */}
          {chunks.length > 1 && (
            <div className="flex justify-center items-center gap-2 p-3 bg-bg-alt-verba">
              <VerbaButton
                title={"Previous Chunk"}
                onClick={previousChunk}
                className="btn-sm min-w-min max-w-[200px]"
                text_class_name="text-xs"
                disabled={isPreviousDisabled}
                Icon={IoChevronBack}
              />
              <VerbaButton
                title={"Next Chunk"}
                onClick={nextChunk}
                className="btn-sm min-w-min max-w-[200px]"
                text_class_name="text-xs"
                Icon={IoChevronForward}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChunkView;
