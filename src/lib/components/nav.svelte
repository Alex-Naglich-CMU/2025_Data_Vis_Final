<script lang="ts">
	import { resolve, asset } from '$app/paths';

	type NavRoute = {
		path: string; // ✅ Tell TypeScript 'path' is just a generic string
		name: string;
	};

	const navRoutes: NavRoute[] = [
		{ path: '/', name: 'Home' },
		{ path: '/internal', name: 'Internal Docs' },
		{ path: 'https://dig.cmu.edu/datavis-fall-2025/final-project/', name: 'Final Info' },
		{ path: '/team', name: 'Team' },
		{ path: '/playground', name: 'Playground' },
		{ path: '/kim', name: 'Kim' }
	];

</script>

<div class="flex justify-end mr-10">
	<div class="flex items-center justify-between">
		<nav class="flex-grow m-2">
			<ul class="flex space-x-10">
				{#each navRoutes as { path, name }}
					<li class="font-bold hover:underline">
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
				{/each}
			</ul>
		</nav>
	</div>
</div>

