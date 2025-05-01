"use client";

import { AuthProvider } from "@pangeacyber/react-auth";
import { ReactNode } from "react";

interface PangeaAuthProviderProps {
  children: ReactNode;
}

export function PangeaAuthProvider({ children }: PangeaAuthProviderProps) {
  const hostedLoginURL = process.env.NEXT_PUBLIC_AUTHN_HOSTED_LOGIN_URL || "";
  const authConfig = {
    clientToken: process.env.NEXT_PUBLIC_AUTHN_CLIENT_TOKEN || "",
    domain: process.env.NEXT_PUBLIC_PANGEA_DOMAIN || "",
  };

  return (
    <AuthProvider loginUrl={hostedLoginURL} config={authConfig}>
      <>{children}</>
    </AuthProvider>
  );
}
