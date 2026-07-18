/** Thin fetch wrappers for POST /analyze and POST /plan. No UI logic. */

const getAPI = () => import.meta.env.VITE_API_URL;

/**
 * @param {{ user_id: string, user_email: string, user_goal: string,
 *           current_skills: string[], hours_per_week: number }} body
 * @returns {Promise<{ skill_gap_report: object, overall_readiness_percent: number, recommended_timeline_weeks: number }>}
 */
export async function analyzeSkills(body) {
  const res = await fetch(`${getAPI()}/analyze`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`/analyze failed: ${res.status}`);
  return res.json();
}

/**
 * @param {{ ...AnalyzeRequest, skill_gap_report: object }} body
 * @returns {Promise<{ milestones: object[], total_weeks: number }>}
 */
export async function planMilestones(body) {
  const res = await fetch(`${getAPI()}/plan`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`/plan failed: ${res.status}`);
  return res.json();
}
