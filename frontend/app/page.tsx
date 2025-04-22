'use client';

import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a resume file');
      return;
    }

    setLoading(true);
    setQuestions([]);
    
    const formData = new FormData();
    formData.append('resume', file);

    try {
      const response = await axios.post('http://localhost:8000/api/analyze-resume', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data && response.data.questions) {
        setQuestions(response.data.questions);
      } else {
        setError('Failed to generate questions');
      }
    } catch (err) {
      console.error('Error uploading resume:', err);
      setError('Error uploading resume. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>AI Resume Screening</h1>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="resume" style={{ display: 'block', marginBottom: '0.5rem' }}>
            Upload your resume (PDF, DOCX)
          </label>
          <input
            type="file"
            id="resume"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            style={{ marginBottom: '0.5rem' }}
          />
          {file && <p>Selected file: {file.name}</p>}
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Generate Questions'}
        </button>
      </form>

      {error && (
        <div style={{ color: 'red', margin: '1rem 0' }}>
          {error}
        </div>
      )}

      {questions.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Generated Questions</h2>
          <ul style={{ marginTop: '1rem' }}>
            {questions.map((question, index) => (
              <li key={index} style={{ marginBottom: '0.5rem' }}>
                {question}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}