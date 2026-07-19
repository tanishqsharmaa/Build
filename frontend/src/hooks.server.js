import { createServerClient } from '@supabase/ssr';
import { redirect, error } from '@sveltejs/kit';

const PUBLIC_PATHS = ['/', '/login'];

export const handle = async ({ event, resolve }) => {
	event.locals.supabase = createServerClient(
		import.meta.env.VITE_SUPABASE_URL,
		import.meta.env.VITE_SUPABASE_ANON_KEY,
		{
			cookies: {
				getAll: () => event.cookies.getAll(),
				setAll: (cookiesToSet) => {
					cookiesToSet.forEach(({ name, value, options }) =>
						event.cookies.set(name, value, { ...options, path: '/' })
					);
				}
			}
		}
	);

	const { data: { session } } = await event.locals.supabase.auth.getSession();

	if (!session && !PUBLIC_PATHS.includes(event.url.pathname)) {
		const loginUrl = new URL('/login', event.url.origin);
		throw redirect(303, loginUrl);
	}

	event.locals.session = session;

	if (session?.user?.id) {
		try {
			const { data: profile } = await event.locals.supabase
				.from('profiles')
				.select('id, email, goal, hours_per_week')
				.eq('id', session.user.id)
				.maybeSingle();

			event.locals.profile = profile;
		} catch {
			event.locals.profile = null;
		}
	}

	return resolve(event);
};

export const handleError = async ({ error: err, event }) => {
	console.error(`[hooks.server.js] ${event.url.pathname}:`, err);
	return {
		message: err?.message ?? 'Internal error'
	};
};
