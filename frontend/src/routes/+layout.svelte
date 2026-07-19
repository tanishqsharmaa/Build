<script>
	import { page } from '$app/stores';
	import '../app.css';
</script>

<div class="min-h-screen bg-[var(--color-bg)]">
	{#if $page.data.session}
		<header class="border-b border-[#334155] bg-[#0f172a]/80 backdrop-blur sticky top-0 z-50">
			<div class="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
				<a href="/dashboard" class="text-white font-bold text-lg no-underline">SkillBridge</a>
				<div class="flex items-center gap-4">
					<span class="text-[#94a3b8] text-sm hidden sm:block">
						{$page.data.session.user.email}
					</span>
					<a href="/logout" class="text-[#94a3b8] hover:text-white text-sm no-underline transition-colors">
						Sign out
					</a>
				</div>
			</div>
		</header>
	{/if}

	<slot />
</div>
