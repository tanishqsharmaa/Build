import { redirect } from '@sveltejs/kit';

export const actions = {
	default: async ({ request, locals }) => {
		const { data, error } = await locals.supabase.auth.signInWithOAuth({
			provider: 'google',
			options: {
				redirectTo: `${new URL(request.url).origin}/auth/callback`
			}
		});

		if (error) {
			return { error: error.message };
		}

		throw redirect(303, data.url);
	}
};
