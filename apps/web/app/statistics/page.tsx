'use client'
import { useEffect, useState } from 'react'
import { getFrequency } from '@/lib/api'
import { FrequencyItem } from '@/lib/types'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const WINDOWS = [
  { label: 'All time', value: 0 },
  { label: 'Last 10', value: 10 },
  { label: 'Last 20', value: 20 },
  { label: 'Last 50', value: 50 },
]

export default function StatisticsPage() {
  const [frequencies, setFrequencies] = useState<FrequencyItem[]>([])
  const [window, setWindow] = useState(0)
  const [asOfDraw, setAsOfDraw] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getFrequency(window).then(data => {
      setFrequencies(data.frequencies)
      setAsOfDraw(data.as_of_draw)
      setLoading(false)
    })
  }, [window])

  const maxFreq = Math.max(...frequencies.map(f => f.frequency), 1)

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="flex items-center gap-4 mb-8">
          <a href="/" className="text-gray-400 hover:text-white">← Back</a>
          <h1 className="text-3xl font-bold">Number Frequency</h1>
        </div>

        <div className="flex gap-3 mb-8">
          {WINDOWS.map(w => (
            <button
              key={w.value}
              onClick={() => setWindow(w.value)}
              className={`px-4 py-2 rounded-lg text-sm transition-all ${
                window === w.value
                  ? 'bg-yellow-500 text-black font-bold'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-500">Loading...</div>
        ) : (
          <>
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 mb-6">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={frequencies}>
                  <XAxis dataKey="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: '#111827', border: '1px solid #374151' }}
                    labelStyle={{ color: '#f9fafb' }}
                  />
                  <Bar dataKey="frequency" radius={[3,3,0,0]}>
                    {frequencies.map((f) => (
                      <Cell
                        key={f.number}
                        fill={f.frequency === maxFreq ? '#eab308' : '#3b82f6'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-10 gap-2">
              {frequencies.map(f => (
                <div key={f.number} className="text-center p-2 bg-gray-900 rounded-lg border border-gray-800">
                  <div className="text-xs text-gray-400">{f.number}</div>
                  <div className={`text-sm font-bold ${
                    f.frequency === maxFreq ? 'text-yellow-400' : 'text-white'
                  }`}>
                    {f.frequency}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </main>
  )
}
