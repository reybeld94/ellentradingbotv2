/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_USE_LIVE_BROKER: string;    // "true" | "false"
  readonly VITE_LOG_BROKER_WIRE: string;    // "true" | "false"
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
