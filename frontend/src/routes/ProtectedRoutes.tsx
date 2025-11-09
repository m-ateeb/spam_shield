import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

interface Props {
  children: JSX.Element;
}

export const ProtectedRoute: React.FC<Props> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    // Redirect to login with return URL
    const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
    return <Navigate to={`/login?returnUrl=${returnUrl}`} replace />;
  }

  return children;
};
