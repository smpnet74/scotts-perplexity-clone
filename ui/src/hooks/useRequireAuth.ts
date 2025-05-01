"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@pangeacyber/react-auth";

/**
 * A hook that enforces authentication by redirecting to login if not authenticated
 * @returns Object containing authentication state
 */
export function useRequireAuth() {
  const auth = useAuth();
  const { authenticated, loading, login, user } = auth;
  const [isChecking, setIsChecking] = useState(true);
  
  // Check for model change synchronously during hook initialization
  // This is crucial to avoid any loading flicker
  const isModelChange = typeof window !== 'undefined' && 
    localStorage.getItem('is_model_change') === 'true';
  
  // If this is a model change, immediately return authenticated without any checks
  if (isModelChange) {
    return {
      isAuthenticated: true, // Force authenticated during model changes
      isLoading: false,     // Force not loading during model changes
      user,
    };
  }
  
  // For normal operation (not model change), proceed with authentication checks
  useEffect(() => {
    // Function to check authentication status
    const checkAuth = async () => {
      try {
        // Wait for the initial auth state to load
        if (!loading) {
          if (!authenticated) {
            // If not authenticated, redirect to login
            console.log("Not authenticated, redirecting to login...");
            await login();
          }
          // Auth check complete
          setIsChecking(false);
        }
      } catch (error) {
        console.error("Authentication check error:", error);
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [authenticated, loading, login]);

  return {
    isAuthenticated: authenticated,
    isLoading: loading || isChecking,
    user,
  };
}
