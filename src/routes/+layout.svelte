<script lang="ts">
	import '../app.css';
	import RXIcon from '$lib/assets/RXIcon.jpg';
	import Nav from '$lib/components/nav.svelte';

	let { children } = $props();

</script>

<svelte:head>
	<link rel="icon" href={RXIcon} />
</svelte:head>
<Nav />
<div class="container">
	<div class="content">
		{@render children?.()}
	</div>
</div>

<style>
/* 
	.content {
		display: flex;
		flex-direction: column;
		justify-content: center;
	} */
</style>