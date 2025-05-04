"use client";

import React from "react";
import { createContext, useContext, useState, ReactNode } from "react";

type ModelSelectorContextType = {
  model: string;
  setModel: (model: string) => void;
  agent: string;
  lgcDeploymentUrl?: string | null;
  hidden: boolean;
  setHidden: (hidden: boolean) => void;
};

const ModelSelectorContext = createContext<
  ModelSelectorContextType | undefined
>(undefined);

export const ModelSelectorProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  // Get model directly from URL parameter, like the original implementation
  const model =
    globalThis.window === undefined
      ? "model1"
      : new URL(window.location.href).searchParams.get("coAgentsModel") ??
        "model1";
        
  const [hidden, setHidden] = useState<boolean>(false);

  // Update the model and force a page reload to clear the entire page
  // This matches the original implementation exactly
  const setModel = (model: string) => {
    if (typeof window !== 'undefined') {
      // Update URL and force a page reload - exactly like the original
      const url = new URL(window.location.href);
      url.searchParams.set("coAgentsModel", model);
      window.location.href = url.toString();
    }
  };

  const lgcDeploymentUrl =
    globalThis.window === undefined
      ? null
      : new URL(window.location.href).searchParams.get("lgcDeploymentUrl");

  // Determine the agent based on the current model
  let agent = "research_agent";
  if (model === "model3") {
    agent = "research_agent_google_genai";
  } else if (model === "crewai") {
    agent = "research_agent_crewai";
  } else if (model === "qwen3-30b-a3b-fp8-crewai") {
    agent = "research_agent_crewai_qwen3";
  }

  return (
    <ModelSelectorContext.Provider
      value={{
        model,
        agent,
        lgcDeploymentUrl,
        hidden,
        setModel,
        setHidden,
      }}
    >
      {children}
    </ModelSelectorContext.Provider>
  );
};

export const useModelSelectorContext = () => {
  const context = useContext(ModelSelectorContext);
  if (context === undefined) {
    throw new Error(
      "useModelSelectorContext must be used within a ModelSelectorProvider"
    );
  }
  return context;
};
