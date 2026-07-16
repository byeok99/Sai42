import type { District } from '@/types/api/course'

const districtLabels: Record<District, string> = {
  DONG_GU: '동구',
  JUNG_GU: '중구',
  SEO_GU: '서구',
  YUSEONG_GU: '유성구',
  DAEDEOK_GU: '대덕구',
  ANY: '아무곳이나',
}

export function formatDistrict(district: District | string | null | undefined) {
  if (!district) return ''
  return districtLabels[district as District] ?? district
}
