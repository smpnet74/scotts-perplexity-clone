"""
Prompt formatting for the CrewAI Qwen3 agent.
"""
from typing_extensions import Dict, Any, List


def format_prompt(research_question: str, report: str, resources: List[Dict[str, Any]]) -> str:
    """
    Format the prompt for the CrewAI Qwen3 agent.
    
    Args:
        research_question: The research question.
        report: The current report.
        resources: The resources available for the research.
        
    Returns:
        The formatted prompt.
    """
    resources_text = ""
    if resources:
        resources_text = "Here are some resources that might be helpful:\n\n"
        for i, resource in enumerate(resources):
            resources_text += f"{i+1}. {resource.get('title', 'Untitled')}\n"
            resources_text += f"   URL: {resource.get('url', '')}\n"
            resources_text += f"   Description: {resource.get('description', '')}\n\n"
    
    prompt = f"""You are a helpful research assistant. Your goal is to help the user research a topic and write a report.

Current Research Question: {research_question if research_question else "No research question yet. You can help the user define one."}

Current Report: {report if report else "No report yet. You can help the user write one."}

{resources_text}

You can use the following tools:
1. Search - to search for information on the web
2. WriteReport - to write or update the research report
3. WriteResearchQuestion - to write or update the research question
4. DeleteResources - to delete resources that are not helpful

Respond to the user in a helpful and informative way. If they ask a question, try to answer it based on the resources you have. If you don't have enough information, use the Search tool to find more information.
"""
    
    return prompt
