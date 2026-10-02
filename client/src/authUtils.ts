export const AUTH_URL = import.meta.env.VITE_AUTH_URL || "http://127.0.0.1:8080";

/**
 * Sends the browser to Flask's OIDC /login route, preserving the current
 * location so the backend's `next` handling returns the user to where they
 * were instead of always landing on the dashboard.
 */
export const redirectToLogin = () => {
  // Flask's /login stores `next` verbatim and redirects to it after the
  // OIDC callback, so this must be an absolute URL on the frontend's own
  // origin (not the Flask app's origin, which may differ in dev).
  const next = `${window.location.origin}${window.location.pathname}${window.location.search}`;
  window.location.href = `${AUTH_URL}/login?next=${encodeURIComponent(next)}`;
};
