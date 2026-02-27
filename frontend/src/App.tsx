import { useEffect, useState } from 'react'
import { Rocket } from 'lucide-react'
import IdeaCard from './components/IdeaCard'
import './index.css'

interface Idea {
  id: number
  title: string
  summary: string
  source_url: string
  original_text: string
  score: number
  target_audience: string
  status: string
  created_at: string
}

function App() {
  const [ideas, setIdeas] = useState<Idea[]>([])
  const [loading, setLoading] = useState(true)
  const [topic, setTopic] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchIdeas()
  }, [])

  const fetchIdeas = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE_URL}/ideas?status=pending`)
      const data = await res.json()
      setIdeas(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (id: number, status: string) => {
    try {
      await fetch(`${API_BASE_URL}/ideas/${id}/status?status=${status}`, {
        method: 'POST'
      })
      setIdeas(ideas.filter(idea => idea.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  const handleScrape = async () => {
    try {
      const url = topic ? `${API_BASE_URL}/scrape?topic=${encodeURIComponent(topic)}` : `${API_BASE_URL}/scrape`
      await fetch(url, { method: 'POST' })
      alert(`Scraping started in the background${topic ? ` for topic: ${topic}` : ''}! Refresh the page in a moment.`)
      setTopic('') // clear after search
    } catch (err) {
      console.error(err)
    }
  }

  const handleGenerateRandom = async () => {
    try {
      setIsGenerating(true)
      const res = await fetch(`${API_BASE_URL}/random`, { method: 'POST' })
      const newIdea = await res.json()
      setIdeas([newIdea, ...ideas])
    } catch (err) {
      console.error(err)
      alert("Failed to generate random idea.")
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="container">
      <header>
        <div className="header-top">
          <div className="title-group">
            <h1>Orbit Ideas</h1>
            <p>Discover AI-curated business opportunities from the internet.</p>
          </div>
          <button onClick={handleGenerateRandom} className="btn-secondary" disabled={isGenerating}>
            {isGenerating ? 'Generating...' : '🎲 Generate Random Idea'}
          </button>
        </div>

        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="Search for a specific topic (e.g., 'productivity', 'fintech')..."
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleScrape()}
          />
          <button onClick={handleScrape} className="main-btn">
            <Rocket size={18} />
            {topic ? 'Scrape Topic' : 'Scrape All'}
          </button>
        </div>
      </header>

      {loading ? (
        <div className="loading">Fetching the latest ideas...</div>
      ) : ideas.length === 0 ? (
        <div className="empty">No pending ideas found. Try running the scraper.</div>
      ) : (
        <div className="ideas-grid">
          {ideas.map((idea, idx) => (
            <IdeaCard
              key={idea.id}
              idea={idea}
              onUpdateStatus={handleStatusUpdate}
              style={{ animationDelay: `${idx * 0.1}s` }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default App
