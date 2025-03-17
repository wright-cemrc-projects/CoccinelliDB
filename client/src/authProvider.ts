import type { AuthProvider } from "@refinedev/core";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080";
const AUTH_URL = import.meta.env.VITE_AUTH_URL || "http://127.0.0.1:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Ensures session cookies are included in requests
  headers: {
    "Content-Type": "application/json",
  },
});
axios.defaults.headers.common['Access-Control-Allow-Origin'] = '*';

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
    window.location.href = `${AUTH_URL}/login`;
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
        name: `${user.given_name} ${user.family_name}`,
        email: user.email,
        avatar: "https://i.pravatar.cc/300",
      };
    } catch {
      return null;
    }
  },

  getPermissions: async () => null,

  onError: async (error) => {
    console.error(error);
    return { error };
  },
};
