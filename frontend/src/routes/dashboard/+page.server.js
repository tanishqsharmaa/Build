export const load = async ({ locals }) => {
	const userId = locals.session?.user?.id;

	if (!userId) {
		return { plan: null, scores: [], userId: null };
	}

	const supabase = locals.supabase;

	const [plansRes, scoresRes] = await Promise.all([
		supabase
			.from('learning_plans')
			.select('milestones, current_milestone_index, plan_revision_count')
			.eq('user_id', userId)
			.eq('is_active', true)
			.limit(1),

		supabase
			.from('quiz_results')
			.select('score, created_at')
			.eq('user_id', userId)
			.not('score', 'is', null)
			.order('created_at', { ascending: false })
			.limit(10)
	]);

	return {
		plan: plansRes.data?.[0] ?? null,
		scores: scoresRes.data ?? [],
		userId
	};
};
