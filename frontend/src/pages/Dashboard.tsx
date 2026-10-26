import { useSummary } from '@/api/queries'
import { DaySection } from '@/components/DaySection'
import { SummaryTiles, SummaryTilesSkeleton } from '@/components/SummaryTiles'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Spinner } from '@/components/ui/spinner'
import { useUrlParam } from '@/lib/useUrlParam'
import { cn } from '@/lib/utils'

// GB day-ahead auctions close around 09:20–09:50 UK time, so 09:00 is the default.
const CUTOFFS = ['06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00']

export function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [cutoff, setCutoff] = useUrlParam('cutoff', '09:00')
  const summary = useSummary(cutoff)

  return (
    <div className="min-h-screen">
      <header className="flex flex-wrap items-center gap-4 border-b bg-card px-6 py-3">
        <span className="mr-auto font-semibold">Wind Forecast Monitor</span>
        <div className="flex items-center gap-2 text-sm">
          <span id="cutoff-label" className="text-muted-foreground">
            Decision cutoff
          </span>
          <Select value={cutoff} onValueChange={setCutoff}>
            <SelectTrigger aria-labelledby="cutoff-label">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CUTOFFS.map((time) => (
                <SelectItem key={time} value={time}>
                  {time} UK, day before delivery
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button variant="ghost" onClick={onLogout}>
          Log out
        </Button>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 p-6">
        <section className="grid gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">
              January 2026: how accurate was the forecast you could act on?
            </h2>
            {summary.isPlaceholderData && <Spinner className="text-muted-foreground" />}
          </div>
          {summary.isPending && <SummaryTilesSkeleton />}
          {summary.isError && <p className="text-destructive">{summary.error.message}</p>}
          {summary.data && (
            // Dim the previous cutoff's numbers while the new ones load.
            <div className={cn('transition-opacity', summary.isPlaceholderData && 'opacity-50')}>
              <SummaryTiles summary={summary.data} />
            </div>
          )}
        </section>

        <DaySection cutoff={cutoff} />
      </main>
    </div>
  )
}
