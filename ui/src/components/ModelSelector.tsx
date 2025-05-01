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
    <Select value={model} onValueChange={(v) => setModel(v)}>
      <SelectTrigger className="w-[260px] text-white">
        <SelectValue placeholder="Theme" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="model1">gpt-4o-mini-langgraph</SelectItem>
        <SelectItem value="model2">gemini-2.5-flash-langgraph</SelectItem>
        <SelectItem value="crewai">gpt-4o-mini-crewai</SelectItem>
      </SelectContent>
    </Select>
  );
}
