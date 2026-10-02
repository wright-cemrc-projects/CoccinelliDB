import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button, Result } from "antd";
import { redirectToLogin } from "@/src/authUtils";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled error in app tree:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Something went wrong"
          subTitle="This can happen if your session expired while the page was open. Try signing in again."
          extra={[
            <Button key="login" type="primary" onClick={() => redirectToLogin()}>
              Sign in again
            </Button>,
            <Button key="reload" onClick={() => window.location.reload()}>
              Reload page
            </Button>,
          ]}
        />
      );
    }
    return this.props.children;
  }
}
