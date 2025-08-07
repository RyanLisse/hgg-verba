import { Float, OrbitControls, PerspectiveCamera } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { extend } from "@react-three/fiber";
import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GoTriangleDown } from "react-icons/go";
import { MdCancel } from "react-icons/md";
import * as three from "three";

import { vectorToColor } from "./util";

import { fetchChunk, fetchVectors } from "@/app/api";

import type {
  ChunkPayload,
  ChunkScore,
  Credentials,
  VectorGroup,
  VectorsPayload,
  VerbaChunk,
  VerbaVector,
} from "@/app/types";

import { colors } from "./util";

// biome-ignore lint/style/useNamingConvention: Three.js API requirement
extend({ OrbitControls: OrbitControls });

const Sphere: React.FC<{
  vector: VerbaVector;
  color: string;
  setHoverTitle: React.MutableRefObject<(t: string | null) => void>;
  documentTitle: string;
  multiplication: number;
  dynamicColor: boolean;
  // biome-ignore lint/style/useNamingConvention: API response format
  chunk_id: string;
  // biome-ignore lint/style/useNamingConvention: API response format
  chunk_uuid: string;
  setSelectedChunk: (c: string) => void;
  selectedChunk: string | null;
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  minZ: number;
  maxZ: number;
  chunkScores?: ChunkScore[];
}> = ({
  vector,
  color,
  setHoverTitle,
  documentTitle,
  multiplication,
  dynamicColor,
  chunk_id,
  chunk_uuid,
  setSelectedChunk,
  selectedChunk,
  minX,
  maxX,
  minY,
  maxY,
  minZ,
  maxZ,
  chunkScores,
}) => {
  const ref = useRef<three.Mesh>(null);
  const hoverRef = useRef(false);

  const isHighlighted = useMemo(
    () => chunkScores?.some((score) => score.uuid === chunk_uuid),
    [chunkScores, chunk_uuid]
  );

  const sphereColor = useMemo(() => {
    if (isHighlighted) return new three.Color("yellow");
    if (selectedChunk === chunk_uuid) return new three.Color("green");
    return dynamicColor
      ? vectorToColor(vector, minX, maxX, minY, maxY, minZ, maxZ)
      : new three.Color(color);
  }, [
    isHighlighted,
    selectedChunk,
    chunk_uuid,
    dynamicColor,
    color,
    vector,
    minX,
    maxX,
    minY,
    maxY,
    minZ,
    maxZ,
  ]);

  const sphereRadius = isHighlighted
    ? 3
    : selectedChunk === chunk_uuid
      ? 1.5
      : 1;
  const sphereOpacity = isHighlighted ? 1 : hoverRef.current ? 1 : 0.5;

  const handlePointerEnter = useCallback(() => {
    hoverRef.current = true;
    setHoverTitle.current(`${documentTitle} | ${chunk_id}`);
  }, [documentTitle, chunk_id, setHoverTitle]);

  const handlePointerLeave = useCallback(() => {
    hoverRef.current = false;
    setHoverTitle.current(null);
  }, [setHoverTitle]);

  const handleClick = useCallback(() => {
    setSelectedChunk(chunk_uuid);
  }, [chunk_uuid, setSelectedChunk]);

  useFrame(() => {
    if (ref.current) {
      ref.current.position.lerp(
        new three.Vector3(
          vector.x * multiplication,
          vector.y * multiplication,
          vector.z * multiplication
        ),
        0.02
      );

      // Update material color based on hover state
      const material = ref.current.material as three.MeshBasicMaterial;
      material.color.set(hoverRef.current ? "blue" : sphereColor);
      material.opacity = hoverRef.current ? 1 : sphereOpacity;
      material.transparent = !hoverRef.current;
    }
  });

  return (
    <Float rotationIntensity={0.2}>
      <mesh
        ref={ref}
        position={[0, 0, 0]}
        onPointerEnter={handlePointerEnter}
        onPointerLeave={handlePointerLeave}
        onClick={handleClick}
      >
        <sphereGeometry args={[sphereRadius, 32, 32]} />
        <meshBasicMaterial
          color={sphereColor}
          opacity={sphereOpacity}
          transparent={true}
        />
      </mesh>
    </Float>
  );
};

interface VectorViewProps {
  credentials: Credentials;
  selectedDocument: string | null;
  chunkScores?: ChunkScore[];
  production: "Local" | "Demo" | "Production";
}

const VectorView: React.FC<VectorViewProps> = ({
  credentials,
  selectedDocument,
  production,
  chunkScores,
}) => {
  const _refs = useRef<(three.Mesh | null)[]>([]);
  const [isFetching, setIsFetching] = useState(false);
  const [vectors, setVectors] = useState<VectorGroup[]>([]);
  const [embedder, setEmbedder] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [dynamicColor, setDymanicColor] = useState(true);
  const [hoverTitleState, setHoverTitleState] = useState<string | null>(null);
  const hoverTitleRef = useRef<(t: string | null) => void>((t) =>
    setHoverTitleState(t)
  );
  const [viewMultiplication, setViewMultiplication] = useState(200);
  const [currentDimensions, setCurrentDimensions] = useState(0);

  const [selectedChunk, setSelectedChunk] = useState<null | string>(null);
  const [chunk, setChunk] = useState<VerbaChunk | null>(null);

  const [minX, setMinX] = useState(-1);
  const [maxX, setMaxX] = useState(1);

  const [minY, setMinY] = useState(-1);
  const [maxY, setMaxY] = useState(1);

  const [minZ, setMinZ] = useState(-1);
  const [maxZ, setMaxZ] = useState(1);

  useEffect(() => {
    if (selectedDocument) {
      fetchVectorsData();
    } else {
      setVectors([]);
    }
  }, [selectedDocument]);

  useEffect(() => {
    if (selectedChunk) {
      fetchChunkData();
    } else {
      setChunk(null);
    }
  }, [selectedChunk]);

  function calculateMinMax(values: number[]): { min: number; max: number } {
    const min = Math.min(...values);
    const max = Math.max(...values);
    return { min, max };
  }

  const getVectorCount = () => {
    let vectorCount = 0;
    for (const vectorGroup of vectors) {
      vectorCount += vectorGroup.chunks.length;
    }
    return vectorCount;
  };

  const fetchChunkData = async () => {
    try {
      const data: ChunkPayload | null = await fetchChunk(
        selectedChunk,
        embedder,
        credentials
      );

      if (data) {
        if (data.error !== "") {
          console.error(data.error);
          setChunk(null);
        } else {
          setChunk(data.chunk);
        }
      }
    } catch (error) {
      console.error("Failed to fetch document:", error);
      setIsFetching(false);
    }
  };

  const fetchVectorsData = async () => {
    try {
      setIsFetching(true);

      const data: VectorsPayload | null = await fetchVectors(
        selectedDocument,
        showAll,
        credentials
      );

      if (data) {
        if (data.error !== "") {
          console.error(data.error);
          setIsFetching(false);
          setVectors([]);
          setCurrentDimensions(0);
          setEmbedder("None");
        } else {
          setVectors(data.vector_groups.groups);
          setEmbedder(data.vector_groups.embedder);
          setCurrentDimensions(data.vector_groups.dimensions);
          setIsFetching(false);

          if (!showAll) {
            const xValues = data.vector_groups.groups[0].chunks.map(
              (v) => v.vector.x
            );
            const yValues = data.vector_groups.groups[0].chunks.map(
              (v) => v.vector.y
            );
            const zValues = data.vector_groups.groups[0].chunks.map(
              (v) => v.vector.z
            );

            const { min: _minX, max: _maxX } = calculateMinMax(xValues);
            setMinX(_minX);
            setMaxX(_maxX);

            const { min: _minY, max: _maxY } = calculateMinMax(yValues);
            setMinY(_minY);
            setMaxY(_maxY);

            const { min: _minZ, max: _maxZ } = calculateMinMax(zValues);
            setMinZ(_minZ);
            setMaxZ(_maxZ);
          }
        }
      }
    } catch (error) {
      console.error("Failed to fetch document:", error);
      setIsFetching(false);
    }
  };

  function selectColor(index: number): string {
    if (index >= colors.length) {
      const randomIndex = Math.floor(Math.random() * colors.length);
      return colors[randomIndex];
    }
    return colors[index];
  }

  return (
    <div className="flex flex-col gap-2 h-full w-full">
      <div className="flex justify-end w-full gap-2 items-center">
        <div className="flex w-full items-start justify-between">
          {/* Left */}
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              {isFetching && (
                <div className="flex items-center justify-center text-text-alt-verba gap-2 h-full">
                  <span className="loading loading-spinner loading-xs lg:loading-sm" />
                </div>
              )}
              <p className="text-text-alt-verba text-xs lg:text-sm font-bold">
                Embedding Model:
              </p>
              <p className="text-text-alt-verba text-xs lg:text-sm">
                {embedder}
              </p>
            </div>
            <div className="flex gap-1 items-center">
              <p className="text-text-alt-verba text-xs lg:text-sm font-bold">
                Hover:
              </p>
              <p
                className="text-xs lg:text-sm text-text-alt-verba truncate max-w-[100px] lg:max-w-[300px]"
                title={hoverTitleState ?? ""}
              >
                {hoverTitleState ?? ""}
              </p>
            </div>
            <div className="flex gap-1 items-center">
              <p className="text-text-alt-verba text-xs lg:text-sm font-bold">
                Vectors:
              </p>
              <p className="text-xs lg:text-sm text-text-alt-verba">
                {vectors.length} x {getVectorCount()} x {currentDimensions}
              </p>
            </div>
          </div>

          <div className="flex gap-10 items-center justify-between min-w-[20vw]">
            <div className="flex flex-col gap-2 w-full">
              {production !== "Demo" && (
                <div className="flex gap-2 items-center justify-between">
                  <p className="text-xs text-text-alt-verba">
                    Show All Documents
                  </p>
                  <input
                    type="checkbox"
                    className="toggle"
                    checked={showAll}
                    onChange={(e) => {
                      setShowAll(e.target.checked);
                    }}
                  />
                </div>
              )}

              <div className="flex gap-2 items-center justify-between">
                <p className="text-xs text-text-alt-verba">Dynamic Coloring</p>
                <input
                  type="checkbox"
                  className="toggle"
                  checked={dynamicColor}
                  onChange={(e) => {
                    setDymanicColor(e.target.checked);
                  }}
                />
              </div>
            </div>

            <div className="flex flex-col gap-2 w-full">
              {/* Dropdown */}
              <div className="dropdown dropdown-bottom flex w-full justify-start items-center">
                <button
                  type="button"
                  tabIndex={0}
                  disabled={true}
                  className="btn btn-sm bg-button-verba hover:bg-button-hover-verba text-text-verba w-full flex justify-start border-none"
                >
                  <GoTriangleDown size={15} />
                  <p>PCA</p>
                </button>
                <ul className="dropdown-content menu bg-base-100 rounded-box z-[1] w-full p-2 shadow" />
              </div>
              {/* Zoom */}
              <div className="flex items-center gap-2 w-full">
                <p className="text-text-alt-verba text-sm">Zoom</p>
                <input
                  onChange={(e) => {
                    setViewMultiplication(Number(e.target.value));
                  }}
                  type="range"
                  min={0}
                  max="1000"
                  value={viewMultiplication}
                  className="range range-xs grow w-full"
                />
              </div>
            </div>

            {chunk && (
              <button
                type="button"
                onClick={() => {
                  setChunk(null);
                  setSelectedChunk(null);
                }}
                className="flex btn btn-square border-none text-text-verba bg-button-verba hover:bg-warning-verba gap-2"
              >
                <MdCancel size={15} />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex gap-5 h-[45vh] w-full">
        <div
          className={`flex flex-grow transition-all duration-300 ease-in-out ${
            selectedChunk ? "w-2/3" : "w-full"
          } h-full`}
        >
          <Canvas>
            <ambientLight intensity={1} />
            <OrbitControls />
            <PerspectiveCamera makeDefault position={[0, 0, 0 + 150]} />
            <axesHelper args={[50]} />
            {vectors.map((vectorGroup, index) =>
              vectorGroup.chunks.map((chunk, vIndex) => (
                <Sphere
                  dynamicColor={dynamicColor}
                  multiplication={viewMultiplication}
                  key={`Sphere_${vIndex}${vectorGroup.name}`}
                  vector={chunk.vector}
                  color={selectColor(index)}
                  setHoverTitle={hoverTitleRef}
                  documentTitle={vectorGroup.name}
                  chunk_id={chunk.chunk_id}
                  setSelectedChunk={setSelectedChunk}
                  selectedChunk={selectedChunk}
                  chunk_uuid={chunk.uuid}
                  minX={minX}
                  minY={minY}
                  minZ={minZ}
                  maxX={maxX}
                  maxY={maxY}
                  maxZ={maxZ}
                  chunkScores={chunkScores}
                />
              ))
            )}
          </Canvas>
        </div>
        <div
          className={`flex flex-grow transition-all duration-300 ease-in-out ${
            selectedChunk ? "w-1/3 opacity-100" : "w-0 opacity-0"
          } overflow-auto`}
        >
          {chunk && (
            <div className="flex flex-col p-3 gap-2 w-full">
              <p className="text-text-alt-verba fond-bold">
                Chunk {chunk.chunk_id}
              </p>
              <p className="text-text-alt-verba text-sm">{chunk.content}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VectorView;
