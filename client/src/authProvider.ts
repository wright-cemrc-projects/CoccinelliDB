import type { AuthProvider } from "@refinedev/core";
import axios from "axios";
import { redirectToLogin } from "./authUtils";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Ensures session cookies are included in requests
  headers: {
    "Content-Type": "application/json",
  },
});
axios.defaults.headers.common['Access-Control-Allow-Origin'] = '*';

// The backend's session can expire between requests (OIDC token refresh
// failure). It now reports that as a 401 instead of silently redirecting,
// so send the user back through login rather than surfacing a raw fetch
// error, preserving the page they were on.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      redirectToLogin();
    }
    return Promise.reject(error);
  },
);

const fetchWithCredentials = async (url: string, method: string = "GET", body: any = null) => {
  try {
    const response = await api({
      url,
      method,
      data: body,
      withCredentials: true,
    });
    return response.data;
  } catch (error: any) {
    console.error("API Error:", error.response?.data || error.message);
    throw error.response?.data || new Error("An error occurred while fetching data");
  }
};

export const authProvider: AuthProvider = {
  login: async () => {
    // Redirect the user to Flask's /login route, which starts OIDC authentication
    redirectToLogin();
    return { success: true };
  },

  logout: async () => {
    // // Logout by calling Flask's /logout route
    window.location.href = `${API_BASE_URL}/custom-logout`;
    return { success: true };
  },

  check: async () => {
    // Check authentication status by calling Flask's /me endpoint
    try {
      await fetchWithCredentials("/me");
      return { authenticated: true };
    } catch {
      return {
        authenticated: false,
        redirectTo: "/",
        error: {
          message: "Check failed",
          name: "Unauthorized",
        },
      };
    }
  },

  getIdentity: async () => {
    // Get user details from Flask's /me endpoint
    try {
      const user = await fetchWithCredentials("/me");
      return {
        id: user.id,
        name: user.email,
        email: user.email,
        roles: user.roles,
        avatar: `https://www.gravatar.com/avatar/${user.emailmd5}?s=400&d=identicon`,
      };
    } catch {
      return null;
    }
  },

  getPermissions: async () => null,

  onError: async (error) => {
    console.error(error);
    if (error?.statusCode === 401 || error?.response?.status === 401) {
      redirectToLogin();
      return { logout: true };
    }
    return { error };
  },
};
