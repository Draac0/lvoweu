import { useSummary } from '@/api/queries'
import { CutoffPicker, DEFAULT_CUTOFF } from '@/components/CutoffPicker'
import { DaySection } from '@/components/DaySection'
import { QueryContent } from '@/components/QueryContent'
import { SummaryTiles, SummaryTilesSkeleton } from '@/components/SummaryTiles'
import { TrustSection } from '@/components/TrustSection'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { useUrlParam } from '@/lib/useUrlParam'

export function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [cutoff, setCutoff] = useUrlParam('cutoff', DEFAULT_CUTOFF)
  const summaryQuery = useSummary(cutoff)

  return (
    <div className="min-h-screen">
      <header className="flex flex-wrap items-center gap-4 border-b bg-card px-6 py-3">
        <span className="mr-auto font-semibold">Wind Forecast Monitor</span>
        <CutoffPicker value={cutoff} onChange={setCutoff} />
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
            {summaryQuery.isPlaceholderData && <Spinner className="text-muted-foreground" />}
          </div>
          <QueryContent query={summaryQuery} placeholder={<SummaryTilesSkeleton />}>
            {(summary) => <SummaryTiles summary={summary} />}
          </QueryContent>
        </section>

        <DaySection cutoff={cutoff} />
        <TrustSection cutoff={cutoff} />
      </main>
    </div>
  )
}
