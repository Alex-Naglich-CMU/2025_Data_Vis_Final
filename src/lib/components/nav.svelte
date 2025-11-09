<script lang="ts">
	import { resolve, asset } from '$app/paths';
	import { onMount } from 'svelte';

	type NavRoute = {
		path: string; // ✅ Tell TypeScript 'path' is just a generic string
		name: string;
	};

	let colorScheme = $state('light');

	onMount(() => {
		const savedScheme = localStorage.getItem('colorScheme');
		if (savedScheme) {
			colorScheme = savedScheme; // Update the reactive state
		}
	});

	const navRoutes: NavRoute[] = [
		{ path: '/', name: 'Home' },
		{ path: '/internal', name: 'Internal Docs' },
		{ path: 'https://dig.cmu.edu/datavis-fall-2025/final-project/', name: 'Final Info' },
		{ path: '/team', name: 'Team' },
		{ path: '/playground', name: 'Playground' },
		{ path: '/kim', name: 'Kim' }
	];

	$effect(() => {
		// AI suggested change, I had another way to do this but this is more robust.
		// This runs only in the browser, after onMount initializes colorScheme.
		if (typeof document !== 'undefined') {
			const root = document.documentElement;

			// Set the data-theme attribute
			root.setAttribute('data-theme', colorScheme);

			// Save to local storage
			localStorage.setItem('colorScheme', colorScheme);

			// Set the CSS color-scheme property
			root.style.setProperty('color-scheme', colorScheme);
		}
	});
</script>

<div
	class="flex items-center justify-between bg-fuchsia-400 shadow-xl/30 dark:bg-fuchsia-500"
>
	<nav class="flex-grow m-2">
		<ul class="flex space-x-1">
			{#each navRoutes as { path, name }}
				<li class="font-mono font-bold hover:underline">
					{#if path.startsWith('http')}
						<a href={path} target="_blank" rel="noopener noreferrer">
							{name}
						</a>
					{:else}
						<a href={resolve(path as any)}>
							{name}
						</a>
					{/if}
				</li>
				<div class="border-2"></div>
			{/each}
		</ul>
	</nav>

	<a
		href={resolve('/')}
		class="rounded-full bg-black m-1 p-0.5"
		aria-label="Go to Homepage"
	>
		<div class="relative h-10 overflow-hidden rounded-full">
			<img
				src={asset('/images/axolotl.jpg')}
				alt="Home"
				class="h-full w-full object-cover object-center"
			/>
			<div class="absolute inset-0 rounded-full transition-all duration-200 hover:bg-white/10"></div>
		</div>
	</a>

	<select
		class="select ml-2 h-auto w-20 select-sm py-0 select-secondary"
		aria-label="Select Theme"
		bind:value={colorScheme}
	>
		<option value="light">Light</option>
		<option value="dark">Dark</option>
	</select>
</div>
