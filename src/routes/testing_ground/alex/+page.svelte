<script lang="ts">
	import ChartContainer from '$lib/components/ChartContainer.svelte';
	import type { DrugData } from '$lib/scripts/drug-types';
	import { getPricesArray } from '$lib/scripts/helper-functions';

	// List of drugs we want to visualize (partial names)
	const curatedList: { [key: string]: string } = {
		lipitor: '617320',
		insulin: '2563971',
		synthroid: '892246',
		metformin: '861731',
		lisdexamfetamine: '1871466',
		fluoxetine: '104849',
		isotretinoin: '1242613',
		amlodipine: '1000000'
	};

	let loadedDrugs = $state<{ [rxcui: string]: DrugData }>({});
	let isLoading = $state<boolean>(true);
	let errorMessage = $state<string | null>(null);
	let loadingRxcui = $state<string | null>(null);

	async function fetchAndStoreDrug(rxcui: string) {
		// Check if already loaded
		if (loadedDrugs[rxcui]) {
			console.log(`${rxcui} already loaded. Skipping fetch.`);
			return;
		}

		// Set loading state
		loadingRxcui = rxcui;
		errorMessage = null;

		try {
			// Fetch Price Data
			const priceResponse = await fetch(`/data/prices/${rxcui}.json`);

			// Check for fetch errors, otherwise parse JSON
			if (!priceResponse.ok) {
				throw new Error(`Failed to fetch prices for RxCUI: ${rxcui}.`);
			}
			const newDrugData: DrugData = await priceResponse.json();

			// Check data is valid
			if (!newDrugData.RxCUI || !newDrugData.prices) {
				throw new Error('JSON is missing required fields (RxCUI or prices).');
			}

			// Update state
			loadedDrugs = {
				...loadedDrugs,
				[rxcui]: newDrugData
			};
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : 'An unknown error occurred.';
			console.error(`Error loading drug ${rxcui}:`, e);
		} finally {
			// Clear loading state
			loadingRxcui = null;
		}
	}

	// Remove drug from loaded list
	function removeDrug(rxcui: string) {
		const { [rxcui]: _, ...rest } = loadedDrugs;
		loadedDrugs = rest;
	}

	async function loadAllCuratedDrugs() {
		// Create an array of promises for concurrent fetching
		const rxcuisToLoad = Object.values(curatedList);

		// Wait for all fetches to complete
		await Promise.all(rxcuisToLoad.map((rxcui) => fetchAndStoreDrug(rxcui)));

		// Clear the global loading state
		isLoading = false;
		console.log(`Finished loading all ${rxcuisToLoad.length} curated drugs.`);
	}

	// Call the function to start loading on component mount
	loadAllCuratedDrugs();
</script>

<!-- Display the json -->
<!-- <pre>{JSON.stringify(loadedDrugs, null, 2)}</pre> -->

<!-- Data Loading Status & Drug Cards -->
{#if isLoading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if errorMessage}
	<div class="error">
		<p>Error loading data: {errorMessage}</p>
	</div>
{:else}
	<div class="drug-section">
		<h3>Loaded {Object.keys(loadedDrugs).length} Medications</h3>

		{#if Object.keys(loadedDrugs).length === 0}
			<p class="no-data">No drugs found. Check console for details.</p>
		{:else}
			<div class="drug-grid">
				{#each Object.values(loadedDrugs) as drug (drug.RxCUI)}
					<div class="drug-card">
						<h4>{drug.Name}</h4>
						<p><strong>Type:</strong> {drug.IsBrand ? 'Brand' : 'Generic'}</p>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

{#if !isLoading && !errorMessage && Object.keys(loadedDrugs).length > 0}
	{#each Object.values(loadedDrugs) as drug}
		<ChartContainer priceData={getPricesArray(drug)} />
	{/each}
{/if}
