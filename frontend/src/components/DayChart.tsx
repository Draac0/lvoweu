import { useMemo } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from 'recharts'
import type { ActualPoint, DecisionHour } from '@/api/types'
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'
import { marketTime } from '@/lib/time'

const config = {
  actual: { label: 'Actual', color: 'var(--wind)' },
  forecast: { label: 'Forecast at decision time', color: 'var(--forecast)' },
} satisfies ChartConfig

type Props = {
  hours: DecisionHour[]
  actuals: ActualPoint[]
  selectedTime?: string
  onSelectTime: (startTime: string) => void
}

type Row = { t: number; actual?: number; forecast?: number }

/** Chart A: one delivery day, the forecast the trader had vs what actually happened (GW). */
export function DayChart({ hours, actuals, selectedTime, onSelectTime }: Props) {
  // Actuals are half-hourly, forecasts hourly: merge them onto one time axis.
  const rows = useMemo(() => {
    const byTime = new Map<number, Row>()
    const rowAt = (iso: string) => {
      const t = Date.parse(iso)
      if (!byTime.has(t)) byTime.set(t, { t })
      return byTime.get(t)!
    }
    for (const a of actuals) rowAt(a.start_time).actual = a.generation_mw / 1000
    for (const h of hours) rowAt(h.start_time).forecast = h.forecast_mw / 1000
    return [...byTime.values()].sort((a, b) => a.t - b.t)
  }, [hours, actuals])

  // Clicking anywhere on the chart selects the forecast hour at or before that point.
  function selectHourAt(t: number) {
    const hour = [...hours].reverse().find((h) => Date.parse(h.start_time) <= t)
    if (hour) onSelectTime(hour.start_time)
  }

  return (
    <ChartContainer config={config} className="aspect-auto h-72 w-full">
      <LineChart
        data={rows}
        margin={{ left: 4, right: 12, top: 8 }}
        onClick={(state) => {
          if (typeof state.activeLabel === 'number') selectHourAt(state.activeLabel)
        }}
        className="cursor-pointer"
      >
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          scale="time"
          domain={['dataMin', 'dataMax']}
          tickFormatter={marketTime}
          tickLine={false}
          axisLine={false}
          minTickGap={24}
        />
        <YAxis
          width={56}
          tickLine={false}
          axisLine={false}
          tickFormatter={(gw: number) => `${gw} GW`}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              labelFormatter={(_, payload) => marketTime(payload[0]?.payload.t)}
              formatter={(value, name) => (
                <div className="flex w-full justify-between gap-4">
                  <span className="text-muted-foreground">
                    {config[name as keyof typeof config].label}
                  </span>
                  <span className="font-medium tabular-nums">{Number(value).toFixed(2)} GW</span>
                </div>
              )}
            />
          }
        />
        {selectedTime && (
          <ReferenceLine x={Date.parse(selectedTime)} stroke="var(--buy)" strokeDasharray="4 4" />
        )}
        <Line
          dataKey="actual"
          type="monotone"
          stroke="var(--color-actual)"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          dataKey="forecast"
          type="monotone"
          stroke="var(--color-forecast)"
          strokeWidth={2}
          dot={{ r: 2 }}
          connectNulls
        />
        <ChartLegend content={<ChartLegendContent />} />
      </LineChart>
    </ChartContainer>
  )
}
