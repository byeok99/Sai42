import type { ApiHeaders, BaseDto, ErrorResponseDto } from '@/types/api/common'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '')
const DEFAULT_BASE_URL = configuredBaseUrl
  ? configuredBaseUrl.endsWith('/api/v1')
    ? configuredBaseUrl
    : `${configuredBaseUrl}/api/v1`
  : 'https://sai42-backend.onrender.com/api/v1'
const API_BASE_URL = DEFAULT_BASE_URL

export class ApiRequestError extends Error {
  constructor(
    public readonly code: string,
    public readonly status: number,
    public readonly traceId?: string,
    message = '요청 처리에 실패했습니다.',
  ) {
    super(
      `${message} (오류 코드: ${code} · HTTP ${status}${traceId ? ` · 추적 ID: ${traceId}` : ''})`,
    )
    this.name = 'ApiRequestError'
  }
}

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
      timeoutMs?: number
    } = {},
  ): Promise<BaseDto<T>> {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin)

    Object.entries(options.params ?? {}).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    })

    const controller = options.timeoutMs ? new AbortController() : null
    const timeoutId = controller
      ? window.setTimeout(() => controller.abort(), options.timeoutMs)
      : null

    let response: Response
    try {
      response = await fetch(url, {
        method,
        headers: this.getHeaders(options.headers),
        ...(method !== 'GET' && options.body ? { body: JSON.stringify(options.body) } : {}),
        ...(controller ? { signal: controller.signal } : {}),
      })
    } finally {
      if (timeoutId !== null) window.clearTimeout(timeoutId)
    }

    const payload = (await response.json().catch(() => null)) as
      | BaseDto<T>
      | ErrorResponseDto
      | null

    if (!response.ok) {
      if (payload && 'code' in payload && 'message' in payload) {
        throw new ApiRequestError(payload.code, response.status, payload.traceId, payload.message)
      }
      throw new ApiRequestError(
        'NETWORK_REQUEST_FAILED',
        response.status,
        undefined,
        '서버 요청에 실패했습니다.',
      )
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
      timeoutMs?: number
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
