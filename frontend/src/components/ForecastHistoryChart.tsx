import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from 'recharts'
import type { ForecastHistory } from '@/api/types'
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'
import { marketDateTime } from '@/lib/time'

const config = {
  forecast: { label: 'Forecast', color: 'var(--forecast)' },
} satisfies ChartConfig

/** Whole-GW ticks covering min..max, evenly spaced, at most ~6 of them. */
function evenTicks(min: number, max: number) {
  const low = Math.floor(min)
  const step = Math.max(1, Math.ceil((Math.ceil(max) - low) / 5))
  const count = Math.ceil((max - low) / step)
  return Array.from({ length: count + 1 }, (_, i) => low + i * step)
}

type Props = {
  history: ForecastHistory
  /** publish_time of the forecast the trader actually used, highlighted on the chart */
  decisionPublishTime?: string
}

/** Chart B: every forecast for one hour, from ~3 days before delivery up to the hour itself. */
export function ForecastHistoryChart({ history, decisionPublishTime }: Props) {
  const rows = history.forecasts.map((f) => ({
    horizon: f.horizon_h,
    forecast: f.forecast_mw / 1000,
    publishTime: f.publish_time,
  }))
  const decision = rows.find((r) => r.publishTime === decisionPublishTime)
  const actual = history.actual_mw === null ? undefined : history.actual_mw / 1000
  // Scale to fit the forecasts AND the actual, or the actual line can fall off the chart.
  const values = rows.map((r) => r.forecast).concat(actual ?? [])
  const yTicks = evenTicks(Math.min(...values), Math.max(...values))

  return (
    <ChartContainer config={config} className="aspect-auto h-72 w-full">
      <LineChart data={rows} margin={{ left: 4, right: 24, top: 16 }}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="horizon"
          type="number"
          reversed
          domain={[0, 'dataMax']}
          ticks={[60, 48, 36, 24, 12, 0]}
          tickFormatter={(h: number) => (h === 0 ? 'Delivery' : `${h}h before`)}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          width={56}
          tickLine={false}
          axisLine={false}
          domain={[yTicks[0], yTicks[yTicks.length - 1]]}
          ticks={yTicks}
          tickFormatter={(gw: number) => `${gw} GW`}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              labelFormatter={(_, payload) => {
                const row = payload[0]?.payload
                return row ? `Published ${marketDateTime(row.publishTime)} (${row.horizon}h ahead)` : ''
              }}
              formatter={(value) => (
                <span className="font-medium tabular-nums">
                  Forecast {Number(value).toFixed(2)} GW
                </span>
              )}
            />
          }
        />
        {actual !== undefined && (
          <ReferenceLine
            y={actual}
            stroke="var(--wind)"
            strokeDasharray="6 4"
            label={{
              value: `Actual ${actual.toFixed(1)} GW`,
              position: 'insideBottomRight',
              fill: 'var(--wind)',
            }}
          />
        )}
        {decision && (
          <ReferenceLine
            x={decision.horizon}
            stroke="var(--buy)"
            strokeDasharray="4 4"
            label={{ value: 'Used at auction', position: 'insideTopRight', fill: 'var(--buy)' }}
          />
        )}
        <Line
          dataKey="forecast"
          stroke="var(--color-forecast)"
          strokeWidth={2}
          isAnimationActive={false}
          dot={(props) => {
            const used = props.payload.publishTime === decisionPublishTime
            return (
              <circle
                key={props.index}
                cx={props.cx}
                cy={props.cy}
                r={used ? 6 : 3}
                fill={used ? 'var(--buy)' : 'var(--forecast)'}
                stroke="white"
                strokeWidth={used ? 2 : 1}
              />
            )
          }}
        />
      </LineChart>
    </ChartContainer>
  )
}
