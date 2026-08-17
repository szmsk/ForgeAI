import "./globals.css";
import type { ReactNode } from "react";
export const metadata = { title: "ForgeAI", description: "Autonomous AI software engineering platform" };
export default function RootLayout({ children }: { children: ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
