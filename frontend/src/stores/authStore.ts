import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi } from "../api/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  username: string | null;
  name: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      username: null,
      name: null,

      login: async (username, password) => {
        const tokens = await authApi.login({ username, password });
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          username,
        });
      },

      logout: () => {
        const { accessToken } = get();
        if (accessToken) authApi.logout(accessToken).catch(() => {});
        set({ accessToken: null, refreshToken: null, username: null, name: null });
      },
    }),
    { name: "auth-storage" }
  )
);
