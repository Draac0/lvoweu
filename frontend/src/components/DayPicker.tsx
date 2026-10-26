import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { DaySummary } from '@/api/types'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { gw } from '@/lib/format'
import { formatDay } from '@/lib/time'

type Props = { days: DaySummary[]; value: string; onChange: (day: string) => void }

export function DayPicker({ days, value, onChange }: Props) {
  const index = days.findIndex((d) => d.date === value)

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="outline"
        size="icon"
        aria-label="Previous day"
        disabled={index <= 0}
        onClick={() => onChange(days[index - 1].date)}
      >
        <ChevronLeft />
      </Button>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger aria-label="Delivery day" className="w-36">
          {/* Just the date here; the per-day error is shown in the open list. */}
          <SelectValue>{formatDay(value)}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {days.map((d) => (
            <SelectItem key={d.date} value={d.date}>
              {formatDay(d.date)}
              {/* Each day's typical miss, so bad days stand out while browsing. */}
              <span className="ml-auto pl-3 text-xs text-muted-foreground tabular-nums">
                {gw(d.mae)}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        variant="outline"
        size="icon"
        aria-label="Next day"
        disabled={index === -1 || index >= days.length - 1}
        onClick={() => onChange(days[index + 1].date)}
      >
        <ChevronRight />
      </Button>
    </div>
  )
}
