import { redirect } from '@sveltejs/kit';

export const load = async ({ locals, url }) => {
	if (locals.session) {
		throw redirect(303, '/dashboard');
	}

	const redirectTo = `${url.origin}/dashboard`;

	const supabase = locals.supabase;
	const { data } = await supabase.auth.signInWithOAuth({
		provider: 'google',
		options: { redirectTo }
	});

	return { oauthUrl: data.url };
};
