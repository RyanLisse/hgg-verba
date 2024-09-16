import React from 'react';
import { Chunk } from '../../types/chat';
import ChunkView from './ChunkView';

interface ContentViewProps {
  chunks: Chunk[];
}

const ContentView: React.FC<ContentViewProps> = ({ chunks }) => {
  return (
    <div className="mt-4">
      <h3 className="text-lg font-semibold mb-2">Retrieved Chunks:</h3>
      {chunks.map((chunk, index) => (
        <ChunkView key={index} chunk={chunk} />
      ))}
    </div>
  );
};

export default ContentView;