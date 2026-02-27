import { CSSProperties } from 'react'
import { Check, X, Star, ExternalLink } from 'lucide-react'

interface Idea {
  id: number
  title: string
  summary: string
  source_url: string
  score: number
  target_audience: string
  created_at: string
}

interface Props {
  idea: Idea
  onUpdateStatus: (id: number, status: string) => void
  style?: CSSProperties
}

export default function IdeaCard({ idea, onUpdateStatus, style }: Props) {
  const date = new Date(idea.created_at).toLocaleDateString()

  return (
    <div className="idea-card" style={style}>
      <div className="idea-meta">
        <span className="idea-date">{date}</span>
        <span className="idea-score">AI Score: {idea.score}</span>
      </div>
      
      <h3 className="idea-title">{idea.title}</h3>
      <p className="idea-summary">{idea.summary}</p>
      
      {idea.target_audience && (
        <div className="idea-audience">
          <strong>Audience:</strong> {idea.target_audience}
        </div>
      )}
      
      <div className="idea-actions">
        <button 
          onClick={() => onUpdateStatus(idea.id, 'approved')} 
          className="btn btn-approve"
          title="Approve"
        >
          <Check size={18} /> Approve
        </button>
        <button 
          onClick={() => onUpdateStatus(idea.id, 'rejected')} 
          className="btn btn-reject"
          title="Reject"
        >
          <X size={18} /> Reject
        </button>
        <button 
          onClick={() => onUpdateStatus(idea.id, 'starred')} 
          className="btn btn-star"
          title="Star"
        >
          <Star size={18} />
        </button>
        <a 
          href={idea.source_url} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="link-btn"
          title="Source"
        >
          <ExternalLink size={18} />
        </a>
      </div>
    </div>
  )
}
