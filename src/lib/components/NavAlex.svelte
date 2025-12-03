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
		{ path: '/team', name: 'Team' },
		{ path: '/testing_ground', name: 'Testing Ground' }
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

<div class="bg-#F6F5EC flex items-center justify-between">
	<nav class="m-2 flex-grow">
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

	<a href={resolve('/')} class="m-1 rounded-full bg-black p-0.5" aria-label="Go to Homepage">
		<div class="relative h-10 overflow-hidden rounded-full">
			<img
				src={asset('/images/axolotl.jpg')}
				alt="Home"
				class="h-full w-full object-cover object-center"
			/>
			<div
				class="absolute inset-0 rounded-full transition-all duration-200 hover:bg-white/10"
			></div>
		</div>
	</a>
</div>
