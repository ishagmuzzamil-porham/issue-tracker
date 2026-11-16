import { useEffect, useState } from 'react'

function App() {
  const [issues, setIssues] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/issues')
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then(setIssues)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main>
      <h1>Issue Tracker</h1>
      {error && <p>Could not load issues: {error}</p>}
      <ul>
        {issues.map((issue) => (
          <li key={issue.id}>
            <strong>{issue.title}</strong> ({issue.type}, {issue.status})
            <br />
            {issue.customer} / {issue.project}, reported by {issue.reported_by}
          </li>
        ))}
      </ul>
    </main>
  )
}

export default App