export interface BaseDto<T> {
  success: true
  code: string
  message: string
  data: T | null
  meta: PageMetaDto | null
  timestamp: string
  traceId: string
}

export interface PageMetaDto {
  page: number
  size: number
  totalElements: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

export interface ErrorResponseDto {
  success: false
  code: string
  message: string
  errors: Array<{
    field: string | null
    reason: string
    rejectedValue: unknown
  }>
  timestamp: string
  traceId: string
}

export interface ApiHeaders {
  'X-Profile-Id'?: string
  'X-User-Password'?: string
  'X-Request-Id'?: string
  'Idempotency-Key'?: string
}

export type AuthenticatedApiHeaders = ApiHeaders & {
  'X-Profile-Id': string
  'X-User-Password': string
}
