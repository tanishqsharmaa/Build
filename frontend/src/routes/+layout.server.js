export const load = async ({ locals }) => {
	return {
		session: locals.session,
		user: locals.user
	};
};
