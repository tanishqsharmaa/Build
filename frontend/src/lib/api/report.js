/** Stub for GET /report/:id — implemented fully in Sprint 8. */

const getAPI = () => import.meta.env.VITE_API_URL;

/**
 * @param {string} userId
 * @returns {Promise<object>}
 */
export async function fetchReport(userId) {
  const res = await fetch(`${getAPI()}/report/${userId}`);
  if (!res.ok) throw new Error(`/report failed: ${res.status}`);
  return res.json();
}
