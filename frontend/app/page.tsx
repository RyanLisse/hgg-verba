"use client";

import React, { useState, useEffect, useCallback } from "react";
import { GoogleAnalytics } from "@next/third-parties/google";
import { PageType, Credentials, RAGConfig, Theme, StatusMessage, LightTheme, Themes, DarkTheme, DocumentFilter, WCDTheme, WeaviateTheme } from "./types";

// Components
import Navbar from "./components/Navigation/NavbarComponent";
import DocumentView from "./components/Document/DocumentView";
import IngestionView from "./components/Ingestion/IngestionView";
import ChatView from "./components/Chat/ChatView";
import SettingsView from "./components/Settings/SettingsView";
import StatusMessengerComponent from "./components/Navigation/StatusMessenger";

// Utilities
import { fetchHealth, connectToVerba } from "./api";

export default function Home() {
  // Page States
  const [currentPage, setCurrentPage] = useState<PageType>("CHAT");
  const [production, setProduction] = useState<"Local" | "Demo" | "Production">("Production");
  const [gtag, setGtag] = useState("");

  // Settings
  const [themes, setThemes] = useState<Themes>({
    Light: LightTheme,
    Dark: DarkTheme,
    Weaviate: WeaviateTheme,
    WCD: WCDTheme,
  });
  const [selectedTheme, setSelectedTheme] = useState<Theme>(themes["WCD"]);

  // Login States
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [credentials, setCredentials] = useState<Credentials>({
    deployment: "Weaviate",
    url: process.env.WEAVIATE_URL_VERBA || "",
    key: process.env.WEAVIATE_API_KEY_VERBA || "",
  });

  // RAG Config
  const [RAGConfig, setRAGConfig] = useState<null | RAGConfig>(null);
  const [documentFilter, setDocumentFilter] = useState<DocumentFilter[]>([]);
  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([]);

  // Define fontClassName
  const fontClassName = "default-font-class"; // Set your desired default class name

  // Function to add a status message
  const addStatusMessage = (message: string, type: "INFO" | "WARNING" | "SUCCESS" | "ERROR") => {
    const newMessage: StatusMessage = {
      message,
      timestamp: new Date().toISOString(),
      type,
    };
    setStatusMessages((prevMessages) => [...prevMessages, newMessage]);
  };

  const initialFetch = useCallback(async (retries: number = 3, delay: number = 1000) => {
    for (let i = 0; i < retries; i++) {
      try {
        const [health_data] = await Promise.all([fetchHealth()]);

        if (health_data) {
          setProduction(health_data.production);
          setGtag(health_data.gtag);
          setIsHealthy(true);
          setCredentials({
            deployment: "Weaviate",
            url: health_data.deployments.WEAVIATE_URL_VERBA,
            key: health_data.deployments.WEAVIATE_API_KEY_VERBA,
          });
          return; // Exit if successful
        } else {
          console.warn("Could not retrieve health data");
        }
      } catch (error) {
        console.error("Error during initial fetch:", error);
      }

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    // If all retries fail
    setIsHealthy(false);
    setIsLoggedIn(false);
  }, []);

  useEffect(() => {
    initialFetch(); // Call the function without parameters
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      const timer = setTimeout(() => {
        setIsLoaded(true);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isLoggedIn]);

  const connect = async () => {
    const response = await connectToVerba(
      credentials.deployment,
      credentials.url,
      credentials.key
    );
    if (response) {
      if (response.error) {
        setIsLoggedIn(false);
        console.error(response.error);
      } else {
        setIsLoggedIn(true);
        setRAGConfig(response.rag_config);
        if (response.themes) {
          setThemes(response.themes);
        }
        if (response.theme) {
          setSelectedTheme(response.theme);
        }
      }
    }
  };

  useEffect(() => {
    if (isHealthy) {
      connect();
    }
  }, [isHealthy]);

  const isValidTheme = (theme: Theme): boolean => {
    const requiredAttributes = [
      "primary_color",
      "secondary_color",
      "warning_color",
      "bg_color",
      "bg_alt_color",
      "text_color",
      "text_alt_color",
      "button_color",
      "button_hover_color",
      "button_text_color",
      "button_text_alt_color",
    ];
    return requiredAttributes.every(
      (attr) =>
        typeof theme[attr as keyof Theme] === "object" &&
        "color" in (theme[attr as keyof Theme] as object)
    );
  };

  // Function to update CSS variables based on the selected theme
  const updateCSSVariables = useCallback(() => {
    const themeToUse = selectedTheme;
    const cssVars = {
      "--primary-verba": themeToUse.primary_color.color,
      "--secondary-verba": themeToUse.secondary_color.color,
      "--warning-verba": themeToUse.warning_color.color,
      "--bg-verba": themeToUse.bg_color.color,
      "--bg-alt-verba": themeToUse.bg_alt_color.color,
      "--text-verba": themeToUse.text_color.color,
      "--text-alt-verba": themeToUse.text_alt_color.color,
      "--button-verba": themeToUse.button_color.color,
      "--button-hover-verba": themeToUse.button_hover_color.color,
      "--text-verba-button": themeToUse.button_text_color.color,
      "--text-alt-verba-button": themeToUse.button_text_alt_color.color,
    };
    Object.entries(cssVars).forEach(([key, value]) => {
      document.documentElement.style.setProperty(key, value);
    });
  }, [selectedTheme]);

  useEffect(() => {
    updateCSSVariables(); // Call to update CSS variables when selectedTheme changes
  }, [selectedTheme]);

  return (
    <main className={`min-h-screen bg-bg-verba text-text-verba ${fontClassName}`} data-theme={selectedTheme.theme}>
      {gtag !== "" && <GoogleAnalytics gaId={gtag} />}
      <StatusMessengerComponent status_messages={statusMessages} set_status_messages={setStatusMessages} />
      {isLoggedIn && isHealthy && (
        <div className={`transition-opacity duration-1000 ${isLoaded ? "opacity-100" : "opacity-0"} flex flex-col gap-2 p-5 md:p-10`}>
          <Navbar
            production={production}
            title={selectedTheme.title.text}
            subtitle={selectedTheme.subtitle.text}
            imageSrc={selectedTheme.image.src}
            version="v2.0.0"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
          />
          {/* Render components based on currentPage */}
          {currentPage === "CHAT" && (
            <ChatView
              addStatusMessage={addStatusMessage}
              credentials={credentials}
              RAGConfig={RAGConfig}
              setRAGConfig={setRAGConfig}
              production={production}
              selectedTheme={selectedTheme}
              currentPage={currentPage}
              documentFilter={documentFilter}
              setDocumentFilter={setDocumentFilter}
            />
          )}
          {currentPage === "SETTINGS" && (
            <SettingsView
              selectedTheme={selectedTheme}
              setSelectedTheme={setSelectedTheme}
              themes={themes}
              setThemes={setThemes}
              credentials={credentials}
              addStatusMessage={addStatusMessage}
            />
          )}
          {currentPage === "IMPORT_DATA" && (
            <IngestionView
              credentials={credentials}
              RAGConfig={RAGConfig}
              setRAGConfig={setRAGConfig}
              addStatusMessage={addStatusMessage}
            />
          )}
          {currentPage === "DOCUMENTS" && (
            <DocumentView
              selectedTheme={selectedTheme}
              production={production}
              credentials={credentials}
              documentFilter={documentFilter}
              setDocumentFilter={setDocumentFilter}
              addStatusMessage={addStatusMessage}
            />
          )}
        </div>
      )}
    </main>
  );
}
