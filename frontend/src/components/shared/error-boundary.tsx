"use client";

import * as React from "react";

import { ErrorState } from "@/components/shared/error-state";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * Catches unhandled render errors in the subtree and shows a recoverable
 * error screen instead of a blank page.  Uses class component syntax because
 * React error boundaries require componentDidCatch / getDerivedStateFromError.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Log to console so the dev overlay and production logging can pick it up.
    console.error("[ErrorBoundary]", error.message, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <ErrorState
          title="Something went wrong"
          description={
            this.state.error?.message ?? "An unexpected error occurred."
          }
          onRetry={() => this.setState({ hasError: false, error: undefined })}
        />
      );
    }
    return this.props.children;
  }
}
