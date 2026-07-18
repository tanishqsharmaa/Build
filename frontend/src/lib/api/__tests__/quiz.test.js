import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

const { fetchQuiz, submitQuiz } = await import('../quiz.js');

describe('fetchQuiz', () => {
  beforeEach(() => { vi.resetAllMocks(); });

  it('GET to correct quiz URL', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ quiz_id: 'q1', topic: 'Python', questions: [] }),
    });

    await fetchQuiz('q1');
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/quiz/q1');
  });

  it('returns quiz data on success', async () => {
    const mockData = { quiz_id: 'abc', topic: 'SQL', questions: [{ question: 'Q?', options: [] }] };
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => mockData });

    const result = await fetchQuiz('abc');
    expect(result.topic).toBe('SQL');
    expect(result.questions).toHaveLength(1);
  });

  it('throws on 404', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 });
    await expect(fetchQuiz('bad-id')).rejects.toThrow('quiz not found');
  });
});

describe('submitQuiz', () => {
  beforeEach(() => { vi.resetAllMocks(); });

  it('POST to /quiz/submit', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ overall_score: 80, recommendation: 'advance', per_question: [], summary_feedback: '' }),
    });

    await submitQuiz({ quiz_id: 'q1', user_id: 'u1', user_email: 'a@b.com', answers: [0,1,2,0,3] });
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/quiz/submit',
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('returns result with overall_score', async () => {
    const mockResult = { overall_score: 60, recommendation: 'review', per_question: [], summary_feedback: 'Try again' };
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => mockResult });

    const result = await submitQuiz({});
    expect(result.overall_score).toBe(60);
    expect(result.recommendation).toBe('review');
  });

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 422 });
    await expect(submitQuiz({})).rejects.toThrow('/quiz/submit failed: 422');
  });
});
