"""Demo for Fly.io deployment"""

import os
from dotenv import load_dotenv
load_dotenv()

# pylint: disable=wrong-import-position
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from copilotkit.crewai import CrewAIAgent
from research_canvas.crewai.agent import ResearchCanvasFlow
from research_canvas.langgraph.agent import graph

app = FastAPI()

# Add CORS middleware to allow requests from your UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you can use "*". For production, specify your UI's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="research_agent",
            description="Research agent.",
            graph=graph,
        ),
        LangGraphAgent(
            name="research_agent_google_genai",
            description="Research agent.",
            graph=graph
        ),
        CrewAIAgent(
            name="research_agent_crewai",
            description="Research agent.",
            flow=ResearchCanvasFlow(),
        ),
    ],
)

add_fastapi_endpoint(app, sdk, "/copilotkit")

# Add a manual info endpoint to handle direct requests to /copilotkit/info
@app.get("/copilotkit/info")
@app.post("/copilotkit/info")
async def copilotkit_info(request: Request):
    """CopilotKit info endpoint."""
    try:
        body = await request.json()
    except:
        body = {}

    return JSONResponse(
        content={
            "actions": [],
            "agents": [
                {
                    "name": "research_agent",
                    "description": "Research agent.",
                    "type": "langgraph"
                },
                {
                    "name": "research_agent_google_genai",
                    "description": "Research agent.",
                    "type": "langgraph"
                },
                {
                    "name": "research_agent_crewai",
                    "description": "Research agent.",
                    "type": "crewai"
                }
            ],
            "sdkVersion": "0.1.44"
        }
    )

@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "research_canvas.fly_demo:app",  # Note: This is updated to use fly_demo instead of demo
        host="0.0.0.0",
        port=port,
    )


if __name__ == "__main__":
    main()
