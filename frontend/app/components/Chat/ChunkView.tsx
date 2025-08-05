import type React from "react";
import type { Chunk } from "../../types/chat";

interface ChunkViewProps {
  chunk: Chunk;
}

const ChunkView: React.FC<ChunkViewProps> = ({ chunk }) => {
  return (
    <div className="mb-4 p-4 bg-gray-100 rounded-lg">
      <p className="text-sm text-gray-600 mb-2">
        Source: {chunk.source} (Score: {chunk.score.toFixed(4)})
      </p>
      <p className="whitespace-pre-wrap">{chunk.content}</p>
    </div>
  );
};

export default ChunkView;
