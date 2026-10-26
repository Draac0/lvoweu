import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import type { HorizonBucket } from '@/api/types'
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'

const config = {
  mae: { label: 'Typical miss', color: 'var(--forecast)' },
} satisfies ChartConfig

/** Chart C: the further ahead a forecast is made, the bigger its typical miss. */
export function HorizonChart({ buckets }: { buckets: HorizonBucket[] }) {
  const rows = buckets.map((b) => ({
    label: `${b.from_h}–${b.to_h}h`,
    mae: b.mae / 1000,
    count: b.count,
  }))

  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full">
      <BarChart data={rows} margin={{ left: 4, right: 4, top: 8 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} axisLine={false} interval={0} fontSize={11} />
        <YAxis
          width={56}
          tickLine={false}
          axisLine={false}
          tickFormatter={(gw: number) => `${gw} GW`}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              labelFormatter={(label) => `Made ${label} ahead`}
              formatter={(value, _, item) => (
                <span className="tabular-nums">
                  Typical miss <b>{Number(value).toFixed(2)} GW</b> ({item.payload.count}{' '}
                  forecasts)
                </span>
              )}
            />
          }
        />
        <Bar dataKey="mae" fill="var(--color-mae)" radius={4} />
      </BarChart>
    </ChartContainer>
  )
}
