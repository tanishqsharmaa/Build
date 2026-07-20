import { createClient } from '@supabase/supabase-js';

export const load = async () => {
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceKey  = process.env.SUPABASE_SERVICE_KEY;
  const userId      = process.env.TEST_USER_ID ?? '00000000-0000-0000-0000-000000000001';

  // If Supabase isn't configured yet, return empty state (dev convenience)
  if (!supabaseUrl || !serviceKey) {
    console.warn('[dashboard] SUPABASE_URL or SUPABASE_SERVICE_KEY not set — returning empty state.');
    return { plan: null, scores: [], userId };
  }

  const supabase = createClient(supabaseUrl, serviceKey);

  const [plansRes, scoresRes] = await Promise.all([
    supabase
      .from('learning_plans')
      .select('milestones, current_milestone_index, plan_revision_count')
      .eq('user_id', userId)
      .eq('is_active', true)
      .limit(1),

    supabase
      .from('quiz_results')
      .select('overall_score, created_at')
      .eq('user_id', userId)
      .not('overall_score', 'is', null)
      .order('created_at', { ascending: false })
      .limit(10),
  ]);

  return {
    plan:   plansRes.data?.[0]  ?? null,
    scores: scoresRes.data       ?? [],
    userId,
  };
};
