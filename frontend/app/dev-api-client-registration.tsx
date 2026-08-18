"use client";

// A dedicated Client Component whose only purpose is to trigger
// api-client.ts's dev-only window.apiClient registration in the browser.
// Server Components (like the root layout) execute on the server, where
// `window` doesn't exist, so a bare import from layout.tsx alone can
// never reach the browser-executed guard. Rendering an actual Client
// Component — even one that renders nothing — is what makes Next.js
// include this code in the client bundle and run it in the browser.
import "../lib/api-client";

export default function DevApiClientRegistration() {
  return null;
}
