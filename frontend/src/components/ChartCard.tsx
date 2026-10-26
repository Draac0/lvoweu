import type { ReactNode } from 'react'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type Props = {
  title: ReactNode
  description: ReactNode
  headline?: ReactNode
  children: ReactNode
}

export function ChartCard({ title, description, headline, children }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
        {headline && <CardAction className="text-right">{headline}</CardAction>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}
