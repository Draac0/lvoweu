import { useDistribution, useHorizonAccuracy } from '@/api/queries'
import { ChartCard } from '@/components/ChartCard'
import { DistributionChart } from '@/components/DistributionChart'
import { HorizonChart } from '@/components/HorizonChart'
import { QueryContent } from '@/components/QueryContent'
import { Skeleton } from '@/components/ui/skeleton'

/** Charts C and D: how much to trust the forecast, and how big a margin to keep. */
export function TrustSection({ cutoff }: { cutoff: string }) {
  const horizonQuery = useHorizonAccuracy()
  const distributionQuery = useDistribution(cutoff)

  return (
    <section className="grid gap-4">
      <h2 className="text-lg font-semibold">How much to trust the forecast</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard
          title="Deciding earlier means bigger misses"
          description="Typical miss of all January forecasts, by how many hours ahead they were made."
        >
          <QueryContent query={horizonQuery} placeholder={<Skeleton className="h-64 w-full" />}>
            {(buckets) => <HorizonChart buckets={buckets} />}
          </QueryContent>
        </ChartCard>

        <ChartCard
          title="How big a safety margin do you need?"
          description={`Misses of the forecast available at ${cutoff}, across every January hour.`}
        >
          <QueryContent
            query={distributionQuery}
            placeholder={<Skeleton className="h-80 w-full" />}
          >
            {(distribution) => <DistributionChart distribution={distribution} />}
          </QueryContent>
        </ChartCard>
      </div>
    </section>
  )
}
