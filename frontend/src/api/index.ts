import type { ApiClient } from "./client";
import { HttpClient } from "./httpClient";
import { MockClient } from "./mockClient";

const mode = import.meta.env.VITE_API_MODE ?? "http";

export const api: ApiClient =
  mode === "mock" ? new MockClient() : new HttpClient();

export const apiMode = mode;
export { ApiError, GuardError } from "./client";
export type { ApiClient } from "./client";
