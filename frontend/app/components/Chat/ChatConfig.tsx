"use client";

import { updateRAGConfig } from "@/app/api";
import type { Credentials, RAGComponentConfig, RAGConfig } from "@/app/types";
import type React from "react";
import { useCallback } from "react";
import { IoSettingsSharp } from "react-icons/io5";
import { MdCancel } from "react-icons/md";
import ComponentView from "../Ingestion/ComponentView";

import VerbaButton from "../Navigation/VerbaButton";

interface ChatConfigProps {
  RAGConfig: RAGConfig | null;
  setRAGConfig: React.Dispatch<React.SetStateAction<RAGConfig | null>>;
  onSave: () => void; // New parameter for handling save
  onReset: () => void; // New parameter for handling reset
  addStatusMessage: (
    message: string,
    type: "INFO" | "WARNING" | "SUCCESS" | "ERROR"
  ) => void;
  credentials: Credentials;
  production: "Local" | "Demo" | "Production";
}

const ChatConfig: React.FC<ChatConfigProps> = ({
  RAGConfig,
  setRAGConfig,
  addStatusMessage,
  onSave,
  credentials,
  onReset,
  production,
}) => {
  const updateConfig = (
    componentN: string,
    configTitle: string,
    value: string | boolean | string[]
  ) => {
    setRAGConfig((prevRAGConfig) => {
      if (prevRAGConfig) {
        // Deep clone to ensure state update is detected
        const newRAGConfig = JSON.parse(JSON.stringify(prevRAGConfig));
        if (typeof value === "string" || typeof value === "boolean") {
          newRAGConfig[componentN].components[
            newRAGConfig[componentN].selected
          ].config[configTitle].value = value;
        } else {
          newRAGConfig[componentN].components[
            newRAGConfig[componentN].selected
          ].config[configTitle].values = value;
        }
        return newRAGConfig;
      }
      return prevRAGConfig;
    });
  };

  const selectComponent = (componentN: string, selectedComponent: string) => {
    setRAGConfig((prevRAGConfig) => {
      if (prevRAGConfig) {
        // Deep clone to ensure state update is detected
        const newRAGConfig = JSON.parse(JSON.stringify(prevRAGConfig));
        newRAGConfig[componentN].selected = selectedComponent;
        return newRAGConfig;
      }
      return prevRAGConfig;
    });
  };

  const saveComponentConfig = useCallback(
    async (
      componentN: string,
      selectedComponent: string,
      componentConfig: RAGComponentConfig
    ) => {
      if (!RAGConfig) return;

      addStatusMessage(`Saving ${selectedComponent} Config`, "SUCCESS");

      const newRAGConfig = JSON.parse(JSON.stringify(RAGConfig));
      newRAGConfig[componentN].selected = selectedComponent;
      newRAGConfig[componentN].components[selectedComponent] = componentConfig;
      const response = await updateRAGConfig(newRAGConfig, credentials);
      if (response) {
        setRAGConfig(newRAGConfig);
      }
    },
    [RAGConfig, addStatusMessage, credentials, setRAGConfig]
  );

  if (RAGConfig) {
    return (
      <div className="flex flex-col justify-start rounded-2xl w-full p-4 ">
        <div className="sticky flex flex-col gap-2 w-full top-0 z-20 justify-end">
          {/* Add Save and Reset buttons */}
          <div className="flex justify-end w-full gap-2 p-4 bg-bg-alt-verba rounded-lg">
            <VerbaButton
              Icon={IoSettingsSharp}
              title="Save Config"
              onClick={onSave}
              className="max-w-[150px]"
              disabled={production === "Demo"}
            />
            <VerbaButton
              Icon={MdCancel}
              title="Reset"
              onClick={onReset}
              className="max-w-[150px]"
              disabled={production === "Demo"}
            />
          </div>
        </div>

        <div className="flex flex-col justify-start gap-3 rounded-2xl w-full p-6 ">
          <ComponentView
            RAGConfig={RAGConfig}
            component_name="Embedder"
            selectComponent={selectComponent}
            updateConfig={updateConfig}
            saveComponentConfig={saveComponentConfig}
            blocked={production === "Demo"}
          />
          <ComponentView
            RAGConfig={RAGConfig}
            component_name="Generator"
            selectComponent={selectComponent}
            updateConfig={updateConfig}
            saveComponentConfig={saveComponentConfig}
            blocked={production === "Demo"}
          />{" "}
          <ComponentView
            RAGConfig={RAGConfig}
            component_name="Retriever"
            selectComponent={selectComponent}
            updateConfig={updateConfig}
            saveComponentConfig={saveComponentConfig}
            blocked={production === "Demo"}
          />
        </div>
      </div>
    );
  }
  return <div />;
};

export default ChatConfig;
