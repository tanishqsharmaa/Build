/** Thin fetch wrappers for GET /quiz/:id and POST /quiz/submit. No UI logic. */

const getAPI = () => import.meta.env.VITE_API_URL;

/**
 * @param {string} quizId
 * @returns {Promise<{ quiz_id: string, topic: string, questions: object[] }>}
 */
export async function fetchQuiz(quizId) {
  const res = await fetch(`${getAPI()}/quiz/${quizId}`);
  if (!res.ok) throw new Error(`quiz not found: ${quizId} (${res.status})`);
  return res.json();
}

/**
 * @param {{ quiz_id: string, user_id: string, user_email: string, answers: number[] }} body
 * @returns {Promise<{ overall_score: number, recommendation: string, per_question: object[], summary_feedback: string }>}
 */
export async function submitQuiz(body) {
  const res = await fetch(`${getAPI()}/quiz/submit`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`/quiz/submit failed: ${res.status}`);
  return res.json();
}
