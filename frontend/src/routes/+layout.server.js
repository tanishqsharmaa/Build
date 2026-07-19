export const load = async ({ locals }) => {
	return {
		session: locals.session,
		profile: locals.profile
	};
};
