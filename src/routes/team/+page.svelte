<script lang="ts">
	import { asset } from '$app/paths';

</script>

<!-- meet the team 2 row 3 col grid with subgrid to hold images and names  -->

<div class="grid grid-cols-3 gap-4">
	<div class="col-span-3 text-center">
		<h2 class="text-2xl font-bold mb-4">Meet the Team</h2>
	</div>

	<div class="subgrid col-span-1 flex flex-col items-center">
		<img
			src={asset('/images/alex.jpg')}
			alt="Alex"
			class="h-40 w-40 rounded-full object-cover"
		/>
		<p class="mt-2 text-lg font-semibold">Alex</p>
	</div>

	<div class="subgrid col-span-1 flex flex-col items-center">
		<img
			src={asset('/images/charlie.jpg')}
			alt="Charlie"
			class="h-40 w-40 rounded-full object-cover"
		/>
		<p class="mt-2 text-lg font-semibold">Charlie</p>
	</div>

	<div class="subgrid col-span-1 flex flex-col items-center">
		<img
			src={asset('/images/eric.jpg')}
			alt="Eric"
			class="h-40 w-40 rounded-full object-cover"
		/>
		<p class="mt-2 text-lg font-semibold">Eric</p>
	</div>

	<div class="subgrid col-span-1 flex flex-col items-center">
		<img
			src={asset('/images/jenna.jpg')}
			alt="Jenna"
			class="h-40 w-40 rounded-full object-cover"
		/>
		<p class="mt-2 text-lg font-semibold">Jenna</p>
	</div>

	<div class="subgrid col-span-1 flex flex-col items-center">
		<img
			src={asset('/images/john.jpg')}
			alt="John"
			class="h-40 w-40 rounded-full object-cover"
		/>
		<p class="mt-2 text-lg font-semibold">John</p>
	</div>

	<div class="subgrid col-span-1 flex flex-col items-center">
		<img
			src={asset('/images/sam.jpg')}
			alt="Sam"
			class="h-40 w-40 rounded-full object-cover"
		/>
		<p class="mt-2 text-lg font-semibold">Sam</p>
	</div>


</div>


