import { createServerClient } from '@supabase/ssr';
import { redirect } from '@sveltejs/kit';

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

	event.locals.safeGetSession = async () => {
		const { data: { session } } = await event.locals.supabase.auth.getSession();
		if (!session) return { session: null, user: null };

		const { data: { user }, error: userError } = await event.locals.supabase.auth.getUser();
		if (userError) {
			// Invalid/expired token — clear and return null
			return { session: null, user: null };
		}

		return { session, user };
	};

	const { session, user } = await event.locals.safeGetSession();

	event.locals.session = session;
	event.locals.user = user;

	if (!session && !PUBLIC_PATHS.includes(event.url.pathname)) {
		throw redirect(303, '/login');
	}

	return resolve(event);
};
