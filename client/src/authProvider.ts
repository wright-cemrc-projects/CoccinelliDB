import type { AuthProvider } from "@refinedev/core";
import axios from "axios";

const API_BASE_URL = "http://localhost:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Ensures session cookies are included in requests
  headers: {
    "Content-Type": "application/json",
  },
});


const fetchWithCredentials = async (url: string, method: string = "GET", body: any = null) => {
  try {
    const response = await api({
      url,
      method,
      data: body,
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
    window.location.href = "http://localhost:8080/login";
    return { success: true };
  },

  logout: async () => {
    // Logout by calling Flask's /logout route
    await fetchWithCredentials("/logout", "POST");
    window.location.href = "/login";
    return { success: true };
  },

  check: async () => {
    // Check authentication status by calling Flask's /me endpoint
    try {
      await fetchWithCredentials("/me");
      return { authenticated: true };
    } catch {

      return { authenticated: false, redirectTo: "/login" };
    }
  },

  getIdentity: async () => {
    // Get user details from Flask's /me endpoint
    try {
      const user = await fetchWithCredentials("/me");
      return {
        id: user.id,
        name: `${user.first_name} ${user.last_name}`,
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