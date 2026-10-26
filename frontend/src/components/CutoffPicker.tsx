import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// GB day-ahead auctions close around 09:20–09:50 UK time, so 09:00 is the default.
export const DEFAULT_CUTOFF = '09:00'
const CUTOFFS = ['06:00', '07:00', '08:00', DEFAULT_CUTOFF, '10:00', '11:00', '12:00']

type Props = { value: string; onChange: (cutoff: string) => void }

export function CutoffPicker({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span id="cutoff-label" className="text-muted-foreground">
        Decision cutoff
      </span>
      <Select value={value} onValueChange={onChange}>
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
  )
}
