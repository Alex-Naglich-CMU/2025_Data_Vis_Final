<script lang="ts">
	import '../app.css';
	import rxSymbol from '$lib/assets/rx-symbol.jpg';
	import Nav from '$lib/components/Nav.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={rxSymbol} />
</svelte:head>
<Nav />
<div class="container">
	<div class="content">
		{@render children?.()}
	</div>
</div>

<style>
</style>
