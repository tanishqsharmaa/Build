import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Stub VITE_API_URL before importing the module
vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

// Dynamic import to pick up the stubbed env
const { analyzeSkills, planMilestones } = await import('../analyze.js');

describe('analyzeSkills', () => {
  beforeEach(() => { vi.resetAllMocks(); });

  it('POST to correct URL with JSON body', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ skill_gap_report: {}, overall_readiness_percent: 70, recommended_timeline_weeks: 8 }),
    });

    const body = { user_id: 'u1', user_email: 'a@b.com', user_goal: 'Dev', current_skills: ['Python'], hours_per_week: 10 };
    await analyzeSkills(body);

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/analyze',
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('returns parsed JSON on success', async () => {
    const mockData = { skill_gap_report: { skills: [] }, overall_readiness_percent: 60, recommended_timeline_weeks: 12 };
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => mockData });

    const result = await analyzeSkills({});
    expect(result).toEqual(mockData);
  });

  it('throws with status code on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 });
    await expect(analyzeSkills({})).rejects.toThrow('/analyze failed: 500');
  });
});

describe('planMilestones', () => {
  beforeEach(() => { vi.resetAllMocks(); });

  it('POST to /plan with correct URL', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ milestones: [], total_weeks: 4 }),
    });

    await planMilestones({ user_id: 'u1', skill_gap_report: {} });
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/plan',
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('throws on 502 response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 502 });
    await expect(planMilestones({})).rejects.toThrow('/plan failed: 502');
  });
});
