import type { Metadata } from "next";
import "./globals.css";
import DevApiClientRegistration from "./dev-api-client-registration";

export const metadata: Metadata = {
  title: "EngineerAI",
  description:
    "A Personal AI Engineering Company designed to act as a lifelong engineering partner — transforming ideas, sketches, photos, drawings, and engineering requirements into manufacturable engineering solutions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <DevApiClientRegistration />
        {children}
      </body>
    </html>
  );
}
