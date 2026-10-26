import { useDay, useDays, useForecastHistory } from '@/api/queries'
import { ChartCard } from '@/components/ChartCard'
import { DayChart } from '@/components/DayChart'
import { DayPicker } from '@/components/DayPicker'
import { ForecastHistoryChart } from '@/components/ForecastHistoryChart'
import { QueryContent } from '@/components/QueryContent'
import { Skeleton } from '@/components/ui/skeleton'
import { gw } from '@/lib/format'
import { formatDay, marketTime } from '@/lib/time'
import { useUrlParam } from '@/lib/useUrlParam'

const chartPlaceholder = <Skeleton className="h-72 w-full" />

/** Charts A and B: one delivery day, and how one of its hours was forecast over time. */
export function DaySection({ cutoff }: { cutoff: string }) {
  const daysQuery = useDays(cutoff)
  const [pickedDay, setPickedDay] = useUrlParam('day', '')
  const [hour, setHour] = useUrlParam('hour', '18:00')

  const firstDay = daysQuery.data?.[0]?.date
  const day = pickedDay || firstDay
  const dayQuery = useDay(day, cutoff)
  const selectedHour = dayQuery.data?.hours.find((h) => marketTime(h.start_time) === hour)
  const historyQuery = useForecastHistory(selectedHour?.start_time)
  const dayName = day ? formatDay(day) : ''

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">One delivery day, hour by hour</h2>
        {daysQuery.data && day && (
          <DayPicker days={daysQuery.data} value={day} onChange={setPickedDay} />
        )}
      </div>

      <ChartCard
        title={`${dayName}: what the trader saw vs what happened`}
        description={`Forecast available at ${cutoff} the day before. Click an hour to see its forecast history below.`}
        headline={
          dayQuery.data && (
            <>
              <div className="text-xl font-semibold tabular-nums">{gw(dayQuery.data.mae)}</div>
              <div className="text-xs text-muted-foreground">typical miss this day</div>
            </>
          )
        }
      >
        <QueryContent query={dayQuery} placeholder={chartPlaceholder}>
          {(dayDetail) => (
            <DayChart
              hours={dayDetail.hours}
              actuals={dayDetail.actuals}
              selectedTime={selectedHour?.start_time}
              onSelectTime={(startTime) => setHour(marketTime(startTime))}
            />
          )}
        </QueryContent>
      </ChartCard>

      <ChartCard
        title={`How the forecast for ${dayName}, ${hour} changed`}
        description={`Each dot is one forecast publish, oldest on the left. The orange dot is the one available at the ${cutoff} cutoff.`}
      >
        <QueryContent query={historyQuery} placeholder={chartPlaceholder}>
          {(history) => (
            <ForecastHistoryChart
              history={history}
              decisionPublishTime={selectedHour?.publish_time}
            />
          )}
        </QueryContent>
      </ChartCard>
    </section>
  )
}
