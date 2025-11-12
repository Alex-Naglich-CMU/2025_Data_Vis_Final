<script lang="ts">
	import { resolve } from '$app/paths';

	const navRoutes: { path: string; name: string }[] = [
		{
			path: '/playground/toggle_fetching',
			name: 'Example where I re-fetch and override a value without race condition issues.'
		},
		{
			path: '/playground/smart_fetch',
			name: 'Medicare Api calls to get all of the necessary data. Use for exploring the JSON'
		},
		{ path: '/playground/alex', name: 'Alex Testing Ground' }
	];
</script>

<ul class="flex space-x-4 p-4">
	{#each navRoutes as { path, name }}
		<li class="font-mono font-bold hover:underline">
			<a href={resolve(path as any)}>
				{name}
			</a>
		</li>
	{/each}
</ul>
