<script lang="ts">
	let rxcui = '860975'; // Example RXCUI for a drug
    // THIS NEEDS TO BE DYNAMIC

	// async function fetchDrugPrices(rxcui: string) {
	// 	// Assuming your data files are hosted in a public 'data' folder
	// 	const url = `/data/${rxcui}.json`;
    //     // THIS IS NOT GOING TO BE THE RIGHT SPOT

	// 	try {
	// 		const response = await fetch(url);
	// 		if (!response.ok) {
	// 			throw new Error(`Failed to fetch ${rxcui} data.`);
	// 		}
	// 		const data = await response.json();
	// 		return data;
	// 	} catch (error) {
	// 		console.error('Error fetching drug data:', error);
	// 		return [];
	// 	}
	// }
</script>

<h1 class="text-2xl font-bold p-4">Local Fetch Example</h1>
<!-- {#each await fetchDrugPrices(rxcui) as prices}
	<h2 class="text-xl font-semibold p-4">Prices for RXCUI: {rxcui}</h2>
	<ul class="list-disc list-inside p-4">
		{#each prices as price}
			<li>
				<strong>{price.pharmacy_name}:</strong> ${price.price} (Date: {price.date})
			</li>
		{/each}
	</ul>
{/each} -->
