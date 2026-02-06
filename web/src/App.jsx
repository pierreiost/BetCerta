import { useState } from 'react'
import { Monitor, Download, Loader2, TrendingUp, Zap } from 'lucide-react'
import { saveGeneration } from './lib/supabase'

const API_URL = import.meta.env.VITE_API_URL || ''

function App() {
  const [form, setForm] = useState({
    home_team: '',
    away_team: '',
    odd: '',
    profit: '',
    bet_amount: '',
    unit: '',
    extra_tip: '',
  })
  const [loading, setLoading] = useState(false)
  const [videoUrl, setVideoUrl] = useState(null)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setVideoUrl(null)

    try {
      const payload = {
        ...form,
        odd: parseFloat(form.odd),
        profit: parseFloat(form.profit),
        bet_amount: parseFloat(form.bet_amount) || 0,
        unit: parseFloat(form.unit) || 0,
      }

      const res = await fetch(`${API_URL}/generate-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        let msg = `Erro ${res.status}`
        try {
          const err = await res.json()
          msg = err.detail || msg
        } catch {
          const text = await res.text()
          msg = text || msg
        }
        throw new Error(msg)
      }

      const data = await res.json()
      const fullVideoUrl = data.video_url.startsWith('http')
        ? data.video_url
        : `${API_URL}${data.video_url}`
      setVideoUrl(fullVideoUrl)

      saveGeneration({
        videoUrl: data.video_url,
        metadata: payload,
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const inputClass = "w-full rounded-lg border border-[#1E2228] bg-[#1A1F28] px-4 py-2.5 text-sm text-[#E5E7EB] placeholder-[#4B5563] outline-none transition focus:border-[#00FF00] focus:ring-1 focus:ring-[#00FF00]/30"

  return (
    <div className="min-h-screen bg-[#0B0E11] text-[#E5E7EB]">
      {/* Header */}
      <header className="border-b border-[#1E2228] px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center gap-3">
          <Monitor className="h-6 w-6 text-[#00FF00]" />
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-[#00FF00] neon-glow">BET</span>CERTA
          </h1>
          <span className="ml-auto text-xs text-[#9CA3AF] font-mono">GERADOR DE VÍDEOS v1.0</span>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="grid gap-10 lg:grid-cols-2">
          {/* Form Panel */}
          <div>
            <div className="mb-6">
              <h2 className="flex items-center gap-2 text-lg font-semibold">
                <Zap className="h-5 w-5 text-[#00FF00]" />
                Dados da Aposta
              </h2>
              <p className="mt-1 text-sm text-[#9CA3AF]">
                Preencha os dados para gerar o vídeo analítico.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                    Time Casa
                  </label>
                  <input
                    type="text" name="home_team" value={form.home_team}
                    onChange={handleChange} required placeholder="Flamengo"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                    Time Fora
                  </label>
                  <input
                    type="text" name="away_team" value={form.away_team}
                    onChange={handleChange} required placeholder="Palmeiras"
                    className={inputClass}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                    Odd
                  </label>
                  <input
                    type="number" name="odd" value={form.odd}
                    onChange={handleChange} required step="0.01" min="1.01"
                    placeholder="2.10" className={inputClass}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                    Lucro (R$)
                  </label>
                  <input
                    type="number" name="profit" value={form.profit}
                    onChange={handleChange} required step="0.01" min="0"
                    placeholder="1500.00" className={inputClass}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                    Valor da Aposta (R$)
                  </label>
                  <input
                    type="number" name="bet_amount" value={form.bet_amount}
                    onChange={handleChange} step="0.01" min="0"
                    placeholder="100.00" className={inputClass}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                    Unidade Indicada (%)
                  </label>
                  <input
                    type="number" name="unit" value={form.unit}
                    onChange={handleChange} step="0.1" min="0" max="100"
                    placeholder="2.0" className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-[#9CA3AF] uppercase tracking-wider">
                  Dica Extra
                </label>
                <input
                  type="text" name="extra_tip" value={form.extra_tip}
                  onChange={handleChange}
                  placeholder="Flamengo tem média de 16.5 desarmes/jogo"
                  className={inputClass}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-[#00FF00] px-6 py-3 text-sm font-bold text-[#0B0E11] transition hover:bg-[#00CC00] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Rendering...
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-4 w-4" />
                    Gerar Vídeo
                  </>
                )}
              </button>
            </form>

            {error && (
              <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>

          {/* Preview Panel */}
          <div>
            <h2 className="mb-6 flex items-center gap-2 text-lg font-semibold">
              <Monitor className="h-5 w-5 text-[#00FF00]" />
              Preview
            </h2>

            <div className="relative overflow-hidden rounded-xl border border-[#1E2228] bg-[#141820]">
              {videoUrl ? (
                <div className="flex flex-col">
                  <video
                    src={videoUrl}
                    controls
                    autoPlay
                    className="aspect-[9/16] w-full max-h-[600px] object-contain bg-black"
                  />
                  <a
                    href={videoUrl}
                    download
                    className="flex items-center justify-center gap-2 border-t border-[#1E2228] px-4 py-3 text-sm font-medium text-[#00FF00] transition hover:bg-[#1A1F28]"
                  >
                    <Download className="h-4 w-4" />
                    Download MP4
                  </a>
                </div>
              ) : (
                <div className="flex aspect-[9/16] max-h-[600px] flex-col items-center justify-center gap-4 p-8 text-center">
                  {loading ? (
                    <>
                      <div className="h-16 w-16 rounded-full border-2 border-[#1E2228] border-t-[#00FF00] animate-spin" />
                      <div>
                        <p className="font-mono text-[#00FF00] neon-glow">Rendering...</p>
                        <p className="mt-1 text-xs text-[#9CA3AF]">Gerando vídeo 1080x1920</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <Monitor className="h-12 w-12 text-[#1E2228]" />
                      <p className="text-sm text-[#9CA3AF]">
                        Preencha os dados e clique em<br />
                        <span className="font-medium text-[#00FF00]">"Gerar Vídeo"</span> para começar.
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
