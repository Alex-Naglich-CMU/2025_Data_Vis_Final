<script lang="ts">
	import { resolve } from '$app/paths';
	import { isDarkMode } from '$lib/stores/theme';

	const navRoutes = [
		{ path: '/', name: 'Home' },
		{ path: 'https://dig.cmu.edu/datavis-fall-2025/final-project/', name: 'Final Info' }
	];
</script>

<nav
	style="display: flex; justify-content: flex-end; align-items: center; gap: 2rem; margin-right: 2.5rem;"
>
	<ul style="display: flex; gap: 2.5rem; list-style: none; margin: 0; padding: 0;">
		{#each navRoutes as { path, name }}
			<li style="font-weight: bold;">
				<!-- External Links, necessary for GitHub Pages -->
				{#if path.startsWith('http')}
					<a href={path} target="_blank" rel="noopener noreferrer">
						{name}
					</a>
				<!-- Internal Links, uses <resolve> to append to the base path to avoid 404 errors -->
				{:else}
					<a href={resolve(path as any)}>
						{name}
					</a>
				{/if}
			</li>
		{/each}
	</ul>

	<button
		onclick={() => isDarkMode.toggle()}
		aria-label="Toggle Theme"
		style="cursor: pointer; padding: 0.5rem; border: none; background: transparent;"
	>
		<svg viewBox="0 0 24 24" width="24" height="24" fill="none">
			{#if $isDarkMode}
				<path
					d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.36 6.36l-.7-.7M6.34 6.34l-.7-.7m12.02 0l-.7.7M6.34 17.66l-.7.7M16 12a4 4 0 11-8 0 4 4 0 018 0z"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
				/>
			{:else}
				<path
					d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
					stroke="currentColor"
					stroke-width="2"
					stroke-linejoin="round"
				/>
			{/if}
		</svg>
	</button>
</nav>
