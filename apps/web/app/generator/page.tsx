'use client'
import { useState } from 'react'
import { generateTicket } from '@/lib/api'
import { GeneratorResponse } from '@/lib/types'

export default function GeneratorPage() {
  const [result, setResult] = useState<GeneratorResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'xgboost' | 'random'>('xgboost')

  const generate = async () => {
    setLoading(true)
    const data = await generateTicket(mode)
    setResult(data)
    setLoading(false)
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="flex items-center gap-4 mb-8">
          <a href="/" className="text-gray-400 hover:text-white">← Back</a>
          <h1 className="text-3xl font-bold">AI Ticket Generator</h1>
        </div>

        <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 mb-6">
          <div className="flex gap-3 mb-6">
            {(['xgboost', 'random'] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-4 py-2 rounded-lg text-sm transition-all ${
                  mode === m
                    ? 'bg-yellow-500 text-black font-bold'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {m === 'xgboost' ? '🤖 XGBoost' : '🎲 Random'}
              </button>
            ))}
          </div>

          <button
            onClick={generate}
            disabled={loading}
            className="w-full py-4 bg-yellow-500 hover:bg-yellow-400 text-black font-bold rounded-xl text-lg transition-all disabled:opacity-50"
          >
            {loading ? 'Generating...' : 'Generate Ticket'}
          </button>
        </div>

        {result && (
          <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
            <div className="text-center mb-6">
              <p className="text-gray-400 text-sm mb-1">
                For draw on <span className="text-yellow-400 font-bold">{result.next_draw_date}</span>
              </p>
              <p className="text-gray-600 text-xs">
                Trained on {result.training_draws} draws · Features from {result.based_on_features_from}
              </p>
            </div>

            <div className="flex justify-center gap-3 mb-4">
              {result.main_numbers.map(n => (
                <div key={n} className="w-12 h-12 rounded-full bg-gray-700 border-2 border-gray-600 flex items-center justify-center font-bold text-lg">
                  {n}
                </div>
              ))}
              <span className="text-gray-600 flex items-center mx-1">+</span>
              {result.euro_numbers.map(n => (
                <div key={n} className="w-12 h-12 rounded-full bg-yellow-600 border-2 border-yellow-500 flex items-center justify-center font-bold text-lg">
                  {n}
                </div>
              ))}
            </div>

            <div className="text-center mt-4 p-3 bg-gray-800 rounded-lg">
              <p className="text-xs text-green-400">
                {result.backtest_reference?.hit_rate_improvement_vs_random}
              </p>
            </div>

            <p className="text-gray-600 text-xs text-center mt-4">
              {result.disclaimer}
            </p>
          </div>
        )}
      </div>
    </main>
  )
}
