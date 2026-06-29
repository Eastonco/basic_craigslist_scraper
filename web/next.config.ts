import type { NextConfig } from "next";

// standalone: small runtime image — Docker copies .next/standalone + static.
const config: NextConfig = { output: "standalone" };

export default config;
