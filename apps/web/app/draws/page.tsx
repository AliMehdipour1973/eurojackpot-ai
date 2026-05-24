'use client'
import { useEffect, useState } from 'react'
import { getDraws } from '@/lib/api'
import { Draw } from '@/lib/types'
import Link from 'next/link'

export default function DrawsPage() {
  const [draws, setDraws] = useState<Draw[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const limit = 20

  useEffect(() => {
    setLoading(true)
    getDraws(limit, offset).then(data => {
      setDraws(data.draws)
      setTotal(data.total)
      setLoading(false)
    })
  }, [offset])

  const formatDate = (d: number) => {
    const s = d.toString()
    return `${s.slice(0,4)}-${s.slice(4,6)}-${s.slice(6,8)}`
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="flex items-center gap-4 mb-8">
          <Link href="/" className="text-gray-400 hover:text-white">← Back</Link>
          <h1 className="text-3xl font-bold">Draw History</h1>
          <span className="text-gray-500 text-sm">{total} draws</span>
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-500">Loading...</div>
        ) : (
          <>
            <div className="space-y-3">
              {draws.map(draw => (
                <div key={draw.draw_date} className="p-4 bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-between">
                  <span className="text-gray-400 text-sm w-28">{formatDate(draw.draw_date)}</span>
                  <div className="flex gap-2">
                    {draw.main_numbers.map(n => (
                      <span key={n} className="w-9 h-9 rounded-full bg-gray-700 flex items-center justify-center text-sm font-bold">
                        {n}
                      </span>
                    ))}
                    <span className="text-gray-600 mx-1">+</span>
                    {draw.euro_numbers.map(n => (
                      <span key={n} className="w-9 h-9 rounded-full bg-yellow-600 flex items-center justify-center text-sm font-bold">
                        {n}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-between mt-8">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-4 py-2 bg-gray-800 rounded-lg disabled:opacity-30"
              >
                ← Previous
              </button>
              <span className="text-gray-500 text-sm py-2">
                {offset + 1}–{Math.min(offset + limit, total)} of {total}
              </span>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="px-4 py-2 bg-gray-800 rounded-lg disabled:opacity-30"
              >
                Next →
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
