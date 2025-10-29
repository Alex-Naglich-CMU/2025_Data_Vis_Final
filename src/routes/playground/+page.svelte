<script lang="ts">
	import { resolve } from '$app/paths';

	const navRoutes: { path: string; name: string }[] = [
		{ path: '/playground/toggle_fetching', name: 'Toggle between fetching one url vs another, reload the variable without race conditions' },
		{ path: '/playground/smart_fetch', name: 'Properly use the Medicare api to get the id from the metadata of the main page and use that to grab data about the later ones' }
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