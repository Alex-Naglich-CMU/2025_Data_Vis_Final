<script lang="ts">
	import { asset } from '$app/paths';
	import Graphic from '$lib/components/graphic.svelte';

</script>

<div class="my-4 flex flex-col items-center">
	<h1 class="mb-4 text-3xl font-bold">Data-Vis 2025 Final Project</h1>
	<div class="flex items-center space-x-4">
		<p class="w-40 text-center text-xl font-bold">Please enjoy this image of our mascot!</p>
		<div class="h-40 w-40 overflow-hidden rounded-full">
			<img
				src={asset('/images/axolotl.jpg')}
				alt="axolotl"
				class="h-full w-full scale-110 object-cover"
			/>
		</div>
	</div>
</div>


<Graphic />