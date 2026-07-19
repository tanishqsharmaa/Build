import { redirect, error } from '@sveltejs/kit';

export const actions = {
	default: async ({ request, locals }) => {
		const form = await request.formData();

		const rawSkills = form.get('skills')?.toString() ?? '';
		const skills = rawSkills.split(',').map(s => s.trim()).filter(Boolean);
		const goal = form.get('user_goal')?.toString()?.trim() ?? '';
		const hours = parseInt(form.get('hours')?.toString() ?? '10', 10);

		if (!goal) throw error(400, 'Goal is required.');
		if (!skills.length) throw error(400, 'At least one skill is required.');

		const userId = locals.session?.user?.id;
		const userEmail = locals.session?.user?.email;

		if (!userId || !userEmail) {
			throw redirect(303, '/login');
		}

		const apiUrl = import.meta.env.VITE_API_URL;

		if (!apiUrl) throw error(500, 'VITE_API_URL not configured. Set it in .env.local.');

		const body = {
			user_id: userId,
			user_email: userEmail,
			user_goal: goal,
			current_skills: skills,
			hours_per_week: hours
		};

		// ── Step 1: Skill Gap Analysis ─────────────────────────────────────
		let analyzeData;
		try {
			const ar = await fetch(`${apiUrl}/analyze`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
			if (!ar.ok) {
				const detail = await ar.text().catch(() => ar.statusText);
				throw error(502, `Skill gap analysis failed (${ar.status}): ${detail}`);
			}
			analyzeData = await ar.json();
		} catch (e) {
			if (e.status) throw e;
			throw error(502, `Could not reach the SkillBridge API. Is Modal running? Details: ${e.message}`);
		}

		// ── Step 2: Learning Path Planning ────────────────────────────────
		try {
			const pr = await fetch(`${apiUrl}/plan`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ ...body, skill_gap_report: analyzeData.skill_gap_report })
			});
			if (!pr.ok) {
				const detail = await pr.text().catch(() => pr.statusText);
				throw error(502, `Learning plan generation failed (${pr.status}): ${detail}`);
			}
		} catch (e) {
			if (e.status) throw e;
			throw error(502, `Plan request failed: ${e.message}`);
		}

		throw redirect(303, '/dashboard');
	}
};
