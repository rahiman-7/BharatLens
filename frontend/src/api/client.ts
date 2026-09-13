const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const token = typeof window !== 'undefined' ? localStorage.getItem('bharatlens_token') : null;

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers as Record<string, string>),
    },
  });


  if (!response.ok) {
    // If unauthorized, clean up stale session tokens from localStorage
    if (response.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('bharatlens_token');
      localStorage.removeItem('bharatlens_user');
    }

    let errorData: unknown = null;
    let errorMessage = `API request failed with status ${response.status}`;
    try {
      errorData = await response.json();
      if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData) {
        errorMessage = String((errorData as { detail: unknown }).detail);
      }
    } catch {
      // Non-JSON error body
    }
    throw new ApiError(response.status, errorMessage, errorData);
  }

  return response.json() as Promise<T>;
}
