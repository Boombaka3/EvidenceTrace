import { Link, useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi.js'
import { listAnswers } from '../api/client.js'
import { MOCK_ANSWERS } from '../data/mockData.js'
import { MockBanner } from '../components/MockBanner.jsx'
import { LoadingState } from '../components/LoadingState.jsx'
import { ErrorState } from '../components/ErrorState.jsx'
import { ConfidenceBar } from '../components/ConfidenceBar.jsx'

const ANSWER_STYLES = {
  yes: 'text-[#27a644] bg-[#27a644]/10 border border-[#27a644]/20',
  no: 'text-[#EF4444] bg-[#EF4444]/10 border border-[#EF4444]/20',
  maybe: 'text-[#F59E0B] bg-[#F59E0B]/10 border border-[#F59E0B]/20',
}

function AnswerBadge({ answer }) {
  const value = (answer || 'maybe').toLowerCase()
  return (
    <span className={`rounded-[4px] px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider ${ANSWER_STYLES[value] || ANSWER_STYLES.maybe}`}>
      {value}
    </span>
  )
}

export default function Answers() {
  const { id } = useParams()
  const { data: answers, loading, error, isMock, refetch } = useApi(() => listAnswers(id), MOCK_ANSWERS, [id])

  return (
    <div className="min-h-screen bg-[#010102]">
      {isMock && <MockBanner />}

      <div className="px-8 py-8">
        <Link to={`/jobs/${id}`} className="text-[#8a8f98] text-xs hover:text-[#5e6ad2] transition-colors mb-4 block">
          {'<-'} Job #{id}
        </Link>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-semibold text-[#f7f8f8] tracking-tight">
              QA Answers
            </h1>
            <p className="text-[#8a8f98] text-sm mt-1">
              Evidence-grounded answers scored for consistency, NLI grounding, and confidence.
            </p>
          </div>
          <Link
            to={`/jobs/${id}/chat`}
            className="px-3 py-2 bg-[#5e6ad2] hover:bg-[#828fff] text-white text-sm rounded-[8px] transition-colors"
          >
            Open Chat {'->'}
          </Link>
        </div>

        {loading && <LoadingState rows={4} />}
        {error && !isMock && <ErrorState message={error} onRetry={refetch} />}

        {answers && answers.length === 0 && !loading && (
          <p className="text-[#8a8f98] text-sm py-8 text-center">
            No answers scored yet.
          </p>
        )}

        {answers && answers.length > 0 && (
          <table className="w-full">
            <thead>
              <tr className="bg-[#0f1011] border-y border-[#23252a]">
                {['Question', 'Answer', 'Confidence', 'Paper', 'Error Types'].map(h => (
                  <th key={h} className="text-[#8a8f98] text-[11px] font-medium uppercase tracking-wider px-4 py-3 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {answers.map(answer => (
                <tr key={answer.id} className="border-b border-[#23252a] hover:bg-[#0f1011] transition-colors">
                  <td className="px-4 py-3 text-[#f7f8f8] text-sm max-w-sm">{answer.question}</td>
                  <td className="px-4 py-3">
                    <AnswerBadge answer={answer.answer} />
                  </td>
                  <td className="px-4 py-3">
                    <ConfidenceBar score={answer.final_confidence} />
                  </td>
                  <td className="px-4 py-3 text-[#d0d6e0] text-xs">
                    {answer.paper_title || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(answer.error_types || []).map(errorType => (
                        <span
                          key={errorType}
                          className="rounded-[4px] bg-[#141516] border border-[#23252a] text-[#8a8f98] text-[10px] font-mono px-1.5 py-0.5"
                        >
                          {errorType}
                        </span>
                      ))}
                      {!answer.error_types?.length && (
                        <span className="text-[#62666d] text-[10px] font-mono">-</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
