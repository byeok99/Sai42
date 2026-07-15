import type { ApiHeaders, BaseDto, ErrorResponseDto } from '@/types/api/common'

const DEFAULT_BASE_URL = 'https://sai42-backend.onrender.com/api/v1'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

export class ApiClient {
  constructor(private readonly baseUrl: string = DEFAULT_BASE_URL) {}

  private getHeaders(headers?: ApiHeaders): HeadersInit {
    const mergedHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (headers) {
      Object.entries(headers).forEach(([key, value]) => {
        if (value) {
          mergedHeaders[key] = value
        }
      })
    }

    return mergedHeaders
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    path: string,
    options: {
      headers?: ApiHeaders
      body?: unknown
      params?: Record<string, string | number | boolean | undefined>
    } = {},
  ): Promise<BaseDto<T>> {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin)

    Object.entries(options.params ?? {}).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    })

    const response = await fetch(url, {
      method,
      headers: this.getHeaders(options.headers),
      ...(method !== 'GET' && options.body ? { body: JSON.stringify(options.body) } : {}),
    })

    const payload = (await response.json().catch(() => null)) as
      | BaseDto<T>
      | ErrorResponseDto
      | null

    if (!response.ok) {
      const errorMessage = payload && 'message' in payload ? payload.message : 'Request failed'
      throw new Error(errorMessage)
    }

    if (!payload || typeof payload !== 'object' || !('success' in payload) || !payload.success) {
      throw new Error('Unexpected API response')
    }

    return payload as BaseDto<T>
  }

  get<T>(
    path: string,
    options?: {
      headers?: ApiHeaders
      params?: Record<string, string | number | boolean | undefined>
    },
  ): Promise<BaseDto<T>> {
    return this.request<T>('GET', path, options)
  }

  post<T>(path: string, body?: unknown, options?: { headers?: ApiHeaders }): Promise<BaseDto<T>> {
    return this.request<T>('POST', path, { ...options, body })
  }

  put<T>(path: string, body?: unknown, options?: { headers?: ApiHeaders }): Promise<BaseDto<T>> {
    return this.request<T>('PUT', path, { ...options, body })
  }

  patch<T>(path: string, body?: unknown, options?: { headers?: ApiHeaders }): Promise<BaseDto<T>> {
    return this.request<T>('PATCH', path, { ...options, body })
  }

  delete<T>(path: string, options?: { headers?: ApiHeaders }): Promise<BaseDto<T>> {
    return this.request<T>('DELETE', path, options)
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
