import { redirect } from '@sveltejs/kit';

export const actions = {
	default: async ({ locals }) => {
		const supabase = locals.supabase;
		await supabase.auth.signOut();
		throw redirect(303, '/');
	}
};
