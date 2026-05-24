import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
            EuroJackpot AI
          </h1>
          <p className="text-gray-400 text-lg">
            AI-powered lottery analysis — powered by XGBoost
          </p>
          <p className="text-gray-600 text-sm mt-2">
            No guaranteed wins. Just smarter analysis.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link href="/draws" className="group p-6 bg-gray-900 rounded-2xl border border-gray-800 hover:border-yellow-500 transition-all">
            <div className="text-3xl mb-3">🎱</div>
            <h2 className="text-xl font-semibold mb-2">Draw History</h2>
            <p className="text-gray-400 text-sm">Browse all EuroJackpot results from 2022 to today</p>
          </Link>

          <Link href="/statistics" className="group p-6 bg-gray-900 rounded-2xl border border-gray-800 hover:border-yellow-500 transition-all">
            <div className="text-3xl mb-3">📊</div>
            <h2 className="text-xl font-semibold mb-2">Statistics</h2>
            <p className="text-gray-400 text-sm">Frequency charts and trend analysis across rolling windows</p>
          </Link>

          <Link href="/generator" className="group p-6 bg-gray-900 rounded-2xl border border-gray-800 hover:border-yellow-500 transition-all">
            <div className="text-3xl mb-3">🎰</div>
            <h2 className="text-xl font-semibold mb-2">Ticket Generator</h2>
            <p className="text-gray-400 text-sm">Generate tickets with XGBoost or pure random mode</p>
          </Link>
        </div>

        <p className="text-center text-gray-600 text-xs mt-16 max-w-2xl mx-auto">
          EuroJackpot draws are random. This tool analyzes historical patterns for research and entertainment only.
        </p>
      </div>
    </main>
  )
}
