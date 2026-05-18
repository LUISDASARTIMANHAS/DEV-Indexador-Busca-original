import { appEnv } from "@/lib/env";
import { storageKeys } from "@/lib/storage";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type RequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  token?: string;
  query?: Record<string, string | number | undefined>;
};

export const authSessionExpiredEvent = "ifesdoc:session-expired";

const clearStoredSession = () => {
  localStorage.removeItem(storageKeys.session);
};

const readStoredToken = () => {
  const raw = localStorage.getItem(storageKeys.session);
  if (!raw) {
    return null;
  }

  try {
    const session = JSON.parse(raw) as { token?: string };
    return session.token ?? null;
  } catch {
    return null;
  }
};

const notifyUnauthorized = () => {
  clearStoredSession();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(authSessionExpiredEvent));
  }
};

export const buildApiUrl = (path: string, query?: RequestOptions["query"]) => {
  const url = new URL(path, appEnv.apiBaseUrl);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  return url.toString();
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const token = options.token ?? readStoredToken();

  const response = await fetch(buildApiUrl(path, options.query), {
    method: options.method || "GET",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    body: options.body ? (isFormData ? (options.body as FormData) : JSON.stringify(options.body)) : undefined,
  });

  if (!response.ok) {
    if (response.status === 401) {
      notifyUnauthorized();
    }
    let message = "Falha ao comunicar com a API.";

    try {
      const payload = await response.json();
      if (payload?.message) {
        message = payload.message;
      } else if (payload?.detail) {
        message = payload.detail;
      }
    } catch {
      // ignore invalid error bodies
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
};

const readFilenameFromDisposition = (value: string | null) => {
  if (!value) {
    return null;
  }

  const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const match = value.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? null;
};

export const apiBlobRequest = async (
  path: string,
  options: RequestOptions = {},
): Promise<{ blob: Blob; filename: string | null }> => {
  const token = options.token ?? readStoredToken();
  const response = await fetch(buildApiUrl(path, options.query), {
    method: options.method || "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      notifyUnauthorized();
    }
    throw new ApiError("Falha ao baixar o arquivo solicitado.", response.status);
  }

  return {
    blob: await response.blob(),
    filename: readFilenameFromDisposition(response.headers.get("Content-Disposition")),
  };
};
