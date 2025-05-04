"""
Delete resources from the state.
"""
from typing_extensions import Dict, Any, List


def maybe_perform_delete(state: Dict[str, Any]):
    """
    Check if the user requested deletion of resources and perform it if needed.
    
    Args:
        state: The state object containing resources and delete_urls.
    """
    if not state.get("delete_urls"):
        return
    
    # Get the URLs to delete
    urls_to_delete = state["delete_urls"]
    
    # Filter out the resources that match the URLs to delete
    state["resources"] = [
        resource for resource in state.get("resources", [])
        if resource.get("url") not in urls_to_delete
    ]
    
    # Clear the delete_urls after processing
    state["delete_urls"] = []
