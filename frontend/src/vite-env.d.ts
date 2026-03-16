/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL: string;
    // Add other VITE_* env variables here as you use them
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
