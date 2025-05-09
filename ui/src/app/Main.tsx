import { ResearchCanvas } from "@/components/ResearchCanvas";
import { useModelSelectorContext } from "@/lib/model-selector-provider";
import { AgentState } from "@/lib/types";
import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useCopilotChatSuggestions } from "@copilotkit/react-ui";

export default function Main() {
  const { model, agent } = useModelSelectorContext();
  const { state, setState } = useCoAgent<AgentState>({
    name: agent,
    initialState: {
      model,
      research_question: "",
      resources: [],
      report: "",
      logs: [],
    },
  });

  useCopilotChatSuggestions({
    instructions: [
      "What is quantum computing?",
      "Explain climate change impacts",
      "History of artificial intelligence"
    ].join('\n'),
  });

  return (
    <>
      <header className="flex h-[60px] bg-[#0E103D] text-white items-center px-10">
        <div className="flex items-center">
          <img 
            src="https://5yzd7skyh50nr53x.public.blob.vercel-storage.com/scottsperplexitycloneicon-N7HkyLNtwyQFG4k6kOGr4VTqCW9LQK.jpeg" 
            alt="Scott's Perplexity Clone" 
            className="h-10 w-auto" 
          />
        </div>
      </header>

      <div
        className="flex flex-1 border"
        style={{ height: "calc(100vh - 60px)" }}
      >
        <div className="flex-1 overflow-hidden">
          <ResearchCanvas />
        </div>
        <div
          className="w-[500px] h-full flex-shrink-0 pb-4 flex flex-col bg-[#E0E9FD]"
          style={
            {
              "--copilot-kit-background-color": "#E0E9FD",
              "--copilot-kit-secondary-color": "#6766FC",
              "--copilot-kit-separator-color": "#b8b8b8",
              "--copilot-kit-primary-color": "#FFFFFF",
              "--copilot-kit-contrast-color": "#000000",
              "--copilot-kit-secondary-contrast-color": "#000",
              "--progress-dot-color": "black",
            } as any
          }
        >
          <CopilotChat
            className="h-full"
            onSubmitMessage={async (message) => {
              // clear the logs before starting the new research
              setState({ 
                ...state, 
                logs: [],
                // Set the research question from the chat message
                research_question: message
              });
              await new Promise((resolve) => setTimeout(resolve, 30));
            }}
            labels={{
              initial: "Hi! How can I assist you with your research today?",
            }}
          />
        </div>
      </div>
    </>
  );
}
