"use client";

import { CopilotKit } from "@copilotkit/react-core";
import Main from "./Main";
import {
  ModelSelectorProvider,
  useModelSelectorContext,
} from "@/lib/model-selector-provider";
import { ModelSelector } from "@/components/ModelSelector";
import { PangeaAuthProvider } from "@/lib/pangea-auth-provider";
import { AuthGuard } from "@/components/AuthGuard";
import { useAuth } from "@pangeacyber/react-auth";

// Combined user info and logout functionality
function UserLogout() {
  const { user, logout } = useAuth();
  
  const handleLogout = async () => {
    try {
      // First, use Pangea's logout function to clear local state
      await logout();
      
      // Clear any local storage/cookies
      localStorage.clear();
      sessionStorage.clear();
      
      // Clear all cookies
      document.cookie.split(";").forEach(function(c) {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
      
      // Get the base URL for the Pangea hosted login
      const baseUrl = process.env.NEXT_PUBLIC_AUTHN_HOSTED_LOGIN_URL?.split('/login')[0];
      
      if (baseUrl) {
        // Redirect to the login page with a fresh state
        window.location.href = `${baseUrl}/login?redirect_uri=${encodeURIComponent(window.location.origin)}`;
      } else {
        // Fallback to just reloading the page
        window.location.href = "/";
      }
    } catch (error) {
      console.error("Logout error:", error);
      // Even if there's an error, try to reload the page
      window.location.href = "/";
    }
  };
  
  return user?.email ? (
    <button 
      onClick={handleLogout}
      className="text-sm text-white opacity-70 hover:opacity-100 transition-opacity cursor-pointer mr-4 bg-transparent border-none p-0 flex items-center"
    >
      Logout: {user.email}
    </button>
  ) : null;
}

export default function ModelSelectorWrapper() {
  return (
    <PangeaAuthProvider>
      <ModelSelectorProvider>
        {/* Place controls outside AuthGuard to avoid loading screens during model changes */}
        <div className="fixed top-0 right-0 p-4 z-50 flex items-center gap-4">
          <UserLogout />
          <ModelSelector />
        </div>
        
        <AuthGuard>
          <Home />
        </AuthGuard>
      </ModelSelectorProvider>
    </PangeaAuthProvider>
  );
}

function Home() {
  const { agent, lgcDeploymentUrl } = useModelSelectorContext();

  // This logic is implemented to demonstrate multi-agent frameworks in this demo project.
  // There are cleaner ways to handle this in a production environment.
  const runtimeUrl = lgcDeploymentUrl
    ? `/api/copilotkit?lgcDeploymentUrl=${lgcDeploymentUrl}`
    : `/api/copilotkit${
        agent.includes("crewai") ? "?coAgentsModel=crewai" : ""
      }`;

  return (
    <CopilotKit runtimeUrl={runtimeUrl} showDevConsole={false} agent={agent}>
      <Main />
    </CopilotKit>
  );
}
