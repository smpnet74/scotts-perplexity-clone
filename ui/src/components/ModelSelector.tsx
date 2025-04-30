"use client";

import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useModelSelectorContext } from "@/lib/model-selector-provider";

export function ModelSelector() {
  const { model, setModel } = useModelSelectorContext();

  return (
    <div className="fixed top-0 right-0 p-4 z-50">
      <Select value={model} onValueChange={(v) => setModel(v)}>
        <SelectTrigger className="w-[260px] text-white">
          <SelectValue placeholder="Theme" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="model1">GPT-4o-Mini-Langgraph</SelectItem>
          <SelectItem value="model2">Anthropic -Notworking </SelectItem>
          <SelectItem value="model3">Google - Notworking</SelectItem>
          <SelectItem value="model4">Gemini-2.5-Flash-Langgraph</SelectItem>
          <SelectItem value="crewai">GPT-4o-Mini-CrewAI</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
