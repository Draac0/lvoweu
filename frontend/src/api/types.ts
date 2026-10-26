// Readable names for the API's types. These are aliases of the types generated from the
// backend's OpenAPI spec (npm run gen:api), never hand-written, so they can't drift.
import type { components } from '@/api/schema'

type Schemas = components['schemas']

export type ActualPoint = Schemas['ActualPoint']
export type DayDetail = Schemas['DayDetail']
export type DaySummary = Schemas['DaySummary']
export type DecisionHour = Schemas['DecisionHour']
export type ErrorDistribution = Schemas['ErrorDistribution']
export type ErrorSummary = Schemas['ErrorSummary']
export type ForecastHistory = Schemas['ForecastHistory']
export type ForecastPoint = Schemas['ForecastPoint']
export type HistogramBin = Schemas['HistogramBin']
export type HorizonBucket = Schemas['HorizonBucket']
export type ShortfallPoint = Schemas['ShortfallPoint']
