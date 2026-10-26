import type { Schemas } from '@/api/client'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { gw, signedGw } from '@/lib/format'

const gridClass = 'grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3'

export function SummaryTiles({ summary }: { summary: Schemas['ErrorSummary'] }) {
  const tiles = [
    { label: 'Typical miss (MAE)', value: gw(summary.mae) },
    { label: 'Bias (+ means forecast too high)', value: signedGw(summary.bias) },
    {
      label: '80% of misses fall between (P10 to P90)',
      value: `${signedGw(summary.p10)} to ${signedGw(summary.p90)}`,
    },
    { label: 'Hours compared', value: summary.count.toLocaleString('en-GB') },
  ]

  return (
    <div className={gridClass}>
      {tiles.map((tile) => (
        <Card key={tile.label}>
          <CardContent className="grid gap-1">
            <div className="text-2xl font-semibold tabular-nums">{tile.value}</div>
            <div className="text-sm text-muted-foreground">{tile.label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

/** Same shape as the tiles, shown on first load so the layout doesn't jump. */
export function SummaryTilesSkeleton() {
  return (
    <div className={gridClass} aria-busy="true" aria-label="Loading accuracy summary">
      {[1, 2, 3, 4].map((i) => (
        <Card key={i}>
          <CardContent className="grid gap-2">
            <Skeleton className="h-8 w-28" />
            <Skeleton className="h-4 w-40" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
