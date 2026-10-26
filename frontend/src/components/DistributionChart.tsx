import { useState } from 'react'
import {
  Bar,
  BarChart,
  type BarShapeProps,
  CartesianGrid,
  Rectangle,
  XAxis,
  YAxis,
} from 'recharts'
import type { ErrorDistribution } from '@/api/types'
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'
import { Slider } from '@/components/ui/slider'
import { gw, percent } from '@/lib/format'

const config = {
  count: { label: 'Hours' },
} satisfies ChartConfig

/** Orange when the forecast missed by more than the margin, so you'd still be short. */
function MissBar(props: BarShapeProps) {
  const fill = props.payload.stillShort ? 'var(--buy)' : 'var(--muted-foreground)'
  return <Rectangle {...props} fill={fill} />
}

/** Chart D: how big the misses were, and how much safety margin covers them. */
export function DistributionChart({ distribution }: { distribution: ErrorDistribution }) {
  const { bins, shortfall } = distribution
  const [margin, setMargin] = useState(0)
  // The server sends the share short for every margin step, so the slider is a lookup.
  const step = shortfall[1].margin_mw - shortfall[0].margin_mw
  const atMargin = shortfall.find((p) => p.margin_mw === margin) ?? shortfall[0]

  // Round tick steps of 50 hours, so the axis reads 0, 50, 100, ...
  const yMax = Math.ceil(Math.max(...bins.map((b) => b.count)) / 50) * 50
  const yTicks = Array.from({ length: yMax / 50 + 1 }, (_, i) => i * 50)

  const rows = bins.map((b) => ({
    label: `${b.from_mw > 0 ? '+' : ''}${b.from_mw / 1000}`,
    range: `${gw(b.from_mw)} to ${gw(b.to_mw)}`,
    count: b.count,
    stillShort: b.from_mw >= margin,
  }))

  return (
    <div className="grid gap-4">
      <ChartContainer config={config} className="aspect-auto h-56 w-full">
        <BarChart data={rows} margin={{ left: 4, right: 4, top: 8 }} barCategoryGap={2}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} />
          <YAxis
            width={40}
            tickLine={false}
            axisLine={false}
            domain={[0, yMax]}
            ticks={yTicks}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                labelFormatter={(_, payload) => `Forecast off by ${payload[0]?.payload.range}`}
                formatter={(value) => <span className="tabular-nums">{value} hours</span>}
              />
            }
          />
          <Bar dataKey="count" radius={3} shape={MissBar} />
        </BarChart>
      </ChartContainer>
      <p className="-mt-2 text-center text-xs text-muted-foreground">
        Hours, by how far the forecast was off (forecast − actual, GW)
      </p>

      <div className="grid gap-3 rounded-lg border p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
          <label htmlFor="margin" className="font-medium">
            Plan for {gw(margin)} less wind than forecast
          </label>
          <span>
            Still short in{' '}
            <b className="text-base text-buy tabular-nums">{percent(atMargin.share_short)}</b> of
            hours
          </span>
        </div>
        <Slider
          id="margin"
          aria-label="Safety margin"
          min={0}
          max={shortfall[shortfall.length - 1].margin_mw}
          step={step}
          value={[margin]}
          onValueChange={([value]) => setMargin(value)}
        />
        <p className="text-xs text-muted-foreground">
          Orange bars are hours where the forecast was too high by more than your margin, so
          you'd still have to buy at short notice.
        </p>
      </div>
    </div>
  )
}
