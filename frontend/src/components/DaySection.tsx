import { useDay, useDays, useForecastHistory } from '@/api/queries'
import { DayChart } from '@/components/DayChart'
import { DayPicker } from '@/components/DayPicker'
import { ForecastHistoryChart } from '@/components/ForecastHistoryChart'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { gw } from '@/lib/format'
import { formatDay, marketTime } from '@/lib/time'
import { useUrlParam } from '@/lib/useUrlParam'
import { cn } from '@/lib/utils'

/** Charts A and B: one delivery day, and how one of its hours was forecast over time. */
export function DaySection({ cutoff }: { cutoff: string }) {
  const days = useDays(cutoff)
  const [day, setDay] = useUrlParam('day', '')
  const [hour, setHour] = useUrlParam('hour', '18:00')
  const selectedDay = day || days.data?.[0]?.date // default: first day available
  const detail = useDay(selectedDay, cutoff)
  const selected = detail.data?.hours.find((h) => marketTime(h.start_time) === hour)
  const history = useForecastHistory(selected?.start_time)

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">One delivery day, hour by hour</h2>
        {days.data && selectedDay && (
          <DayPicker days={days.data} value={selectedDay} onChange={setDay} />
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {selectedDay ? formatDay(selectedDay) : 'Day'}: what the trader saw vs what happened
          </CardTitle>
          <CardDescription>
            Forecast available at {cutoff} the day before. Click an hour to see its forecast
            history below.
          </CardDescription>
          {detail.data && (
            <CardAction className="text-right">
              <div className="text-xl font-semibold tabular-nums">{gw(detail.data.mae)}</div>
              <div className="text-xs text-muted-foreground">typical miss this day</div>
            </CardAction>
          )}
        </CardHeader>
        <CardContent>
          {detail.isError ? (
            <p className="text-destructive">{detail.error.message}</p>
          ) : !detail.data ? (
            <Skeleton className="h-72 w-full" />
          ) : (
            <div className={cn('transition-opacity', detail.isPlaceholderData && 'opacity-50')}>
              <DayChart
                hours={detail.data.hours}
                actuals={detail.data.actuals}
                selectedTime={selected?.start_time}
                onSelectTime={(startTime) => setHour(marketTime(startTime))}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            How the forecast for {selectedDay ? formatDay(selectedDay) : 'this day'}, {hour}{' '}
            changed
          </CardTitle>
          <CardDescription>
            Each dot is one forecast publish, oldest on the left. The orange dot is the one
            available at the {cutoff} cutoff.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {history.isError ? (
            <p className="text-destructive">{history.error.message}</p>
          ) : !history.data ? (
            <Skeleton className="h-72 w-full" />
          ) : (
            <div className={cn('transition-opacity', history.isPlaceholderData && 'opacity-50')}>
              <ForecastHistoryChart
                history={history.data}
                decisionPublishTime={selected?.publish_time}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}
