import { useState } from "react";
import LoginForm from "./components/Auth/LoginForm";
import SignupForm from "./components/Auth/SignupForm";
import { useAuthStore } from "./stores/authStore";

type Page = "login" | "signup";

export default function App() {
  const { accessToken, username, logout } = useAuthStore();
  const [page, setPage] = useState<Page>("login");

  if (accessToken) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#f5f5f5",
          gap: "1rem",
        }}
      >
        <h1 style={{ margin: 0 }}>Welcome, {username}!</h1>
        <button
          onClick={logout}
          style={{
            padding: "0.5rem 1.25rem",
            background: "#ef4444",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontSize: "1rem",
            cursor: "pointer",
          }}
        >
          Sign out
        </button>
      </div>
    );
  }

  return page === "login" ? (
    <LoginForm onSwitchToSignup={() => setPage("signup")} />
  ) : (
    <SignupForm onSwitchToLogin={() => setPage("login")} />
  );
}
