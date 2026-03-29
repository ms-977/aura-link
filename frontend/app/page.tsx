export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Aura-Link</h1>
          <p className="text-gray-400 mt-1">Multi-LLM Gateway Dashboard</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <p className="text-gray-400 text-sm">Total Requests</p>
            <p className="text-4xl font-bold mt-2">1,284</p>
            <p className="text-green-400 text-sm mt-1">↑ 12% today</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <p className="text-gray-400 text-sm">Total Cost</p>
            <p className="text-4xl font-bold mt-2">$3.42</p>
            <p className="text-green-400 text-sm mt-1">↓ 8% vs yesterday</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <p className="text-gray-400 text-sm">Tokens Used</p>
            <p className="text-4xl font-bold mt-2">842K</p>
            <p className="text-gray-400 text-sm mt-1">Across all providers</p>
          </div>
        </div>

        {/* Provider Status */}
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h2 className="text-lg font-semibold mb-4">Provider Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <span>OpenAI GPT-4</span>
              </div>
              <span className="text-gray-400 text-sm">642 requests · $2.10</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <span>Azure AI</span>
              </div>
              <span className="text-gray-400 text-sm">401 requests · $0.98</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                <span>Local Model</span>
              </div>
              <span className="text-gray-400 text-sm">241 requests · $0.00</span>
            </div>
          </div>
        </div>

      </div>
    </main>
  )
}