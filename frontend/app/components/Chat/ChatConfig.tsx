"use client";

import React, { useCallback, useEffect } from "react";
import { MdCancel } from "react-icons/md";
import { IoSettingsSharp } from "react-icons/io5";
import { RAGConfig, RAGComponentConfig, Credentials } from "@/app/types";
import { updateRAGConfig } from "@/app/api";
import ComponentView from "../Ingestion/ComponentView";
import VerbaButton from "../Navigation/VerbaButton";

interface ChatConfigProps {
  RAGConfig: RAGConfig | null;
  setRAGConfig: React.Dispatch<React.SetStateAction<RAGConfig | null>>;
  onSave: () => void;
  onReset: () => void;
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
  useEffect(() => {
    console.log("RAGConfig in ChatConfig:", RAGConfig);
  }, [RAGConfig]);

  const updateConfig = (
    component_n: string,
    configTitle: string,
    value: string | boolean | string[]
  ) => {
    setRAGConfig((prevRAGConfig) => {
      if (prevRAGConfig) {
        const newRAGConfig = { ...prevRAGConfig };
        if (typeof value === "string" || typeof value === "boolean") {
          newRAGConfig[component_n].components[
            newRAGConfig[component_n].selected
          ].config[configTitle].value = value;
        } else {
          newRAGConfig[component_n].components[
            newRAGConfig[component_n].selected
          ].config[configTitle].values = value;
        }
        return newRAGConfig;
      }
      return prevRAGConfig;
    });
  };

  const selectComponent = (component_n: string, selected_component: string) => {
    setRAGConfig((prevRAGConfig) => {
      if (prevRAGConfig) {
        const newRAGConfig = { ...prevRAGConfig };
        newRAGConfig[component_n].selected = selected_component;
        return newRAGConfig;
      }
      return prevRAGConfig;
    });
  };

  const saveComponentConfig = useCallback(
    async (
      component_n: string,
      selected_component: string,
      component_config: RAGComponentConfig
    ) => {
      if (!RAGConfig) return;

      addStatusMessage("Saving " + selected_component + " Config", "SUCCESS");

      const newRAGConfig = JSON.parse(JSON.stringify(RAGConfig));
      newRAGConfig[component_n].selected = selected_component;
      newRAGConfig[component_n].components[selected_component] =
        component_config;
      const response = await updateRAGConfig(newRAGConfig, credentials);
      if (response) {
        setRAGConfig(newRAGConfig);
      }
    },
    [RAGConfig, credentials, addStatusMessage, setRAGConfig]
  );

  const renderGeneratorDropdown = () => {
    if (!RAGConfig || !RAGConfig.Generator) return null;

    const generators = Object.keys(RAGConfig.Generator.components);
    return (
      <div className="mb-4">
        <label className="block text-sm font-medium text-text-verba mb-2">
          Select Generator
        </label>
        <select
          className="w-full p-2 bg-bg-verba text-text-verba border border-button-verba rounded"
          value={RAGConfig.Generator.selected}
          onChange={(e) => selectComponent("Generator", e.target.value)}
          disabled={production === "Demo"}
        >
          {generators.map((gen) => (
            <option key={gen} value={gen}>
              {gen}
            </option>
          ))}
        </select>
      </div>
    );
  };

  if (RAGConfig) {
    return (
      <div className="flex flex-col justify-start rounded-2xl w-full p-4 ">
        <div className="sticky flex flex-col gap-2 w-full top-0 z-20 justify-end">
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
          {renderGeneratorDropdown()}
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
          />
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
  } else {
    return <div>Loading configuration...</div>;
  }
};

export default ChatConfig;
