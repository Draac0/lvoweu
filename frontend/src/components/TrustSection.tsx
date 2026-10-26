import { useDistribution, useHorizonAccuracy } from '@/api/queries'
import { DistributionChart } from '@/components/DistributionChart'
import { HorizonChart } from '@/components/HorizonChart'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

/** Charts C and D: how much to trust the forecast, and how big a margin to keep. */
export function TrustSection({ cutoff }: { cutoff: string }) {
  const horizon = useHorizonAccuracy()
  const distribution = useDistribution(cutoff)

  return (
    <section className="grid gap-4">
      <h2 className="text-lg font-semibold">How much to trust the forecast</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Deciding earlier means bigger misses</CardTitle>
            <CardDescription>
              Typical miss of all January forecasts, by how many hours ahead they were made.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {horizon.isError ? (
              <p className="text-destructive">{horizon.error.message}</p>
            ) : !horizon.data ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <HorizonChart buckets={horizon.data} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>How big a safety margin do you need?</CardTitle>
            <CardDescription>
              Misses of the forecast available at {cutoff}, across every January hour.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {distribution.isError ? (
              <p className="text-destructive">{distribution.error.message}</p>
            ) : !distribution.data ? (
              <Skeleton className="h-80 w-full" />
            ) : (
              <div
                className={cn('transition-opacity', distribution.isPlaceholderData && 'opacity-50')}
              >
                <DistributionChart distribution={distribution.data} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
