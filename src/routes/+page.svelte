<script lang="ts">
	import { asset } from '$app/paths';
	import ChartContainer from '$lib/components/ChartContainer.svelte';
	import type { DrugData, PricePoint } from '$lib/scripts/drug-types';
	import { getPricesArray } from '$lib/scripts/helper-functions';

	// List of drugs we want to visualize (partial names)
	const curatedList: { [key: string]: string } = {
		lipitor: '617320',
		lantus: '285018',
		synthroid: '966201',
		glucophage: '861008',
		vyvanse: '854832',
		prozac: '104849',
		isotretinoin: '643488',
		norvasc: '212549'
	};

	let loadedDrugs = $state<{ [rxcui: string]: DrugData }>({});
	let isLoading = $state<boolean>(true);
	let errorMessage = $state<string | null>(null);
	let loadingRxcui = $state<string | null>(null);

	// Combine all loaded drug prices into one array for plotting
	const allPlottablePrices: PricePoint[] = $derived(
		Object.values(loadedDrugs).flatMap((drug) => getPricesArray(drug))
	);

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

			const companionRxcui = newDrugData.IsBrand
				? newDrugData.Generic_RxCUI
				: newDrugData.Brand_RxCUI;

			// Ensure companionRxcui is a non-null string and not the current RxCUI
			if (companionRxcui && companionRxcui !== rxcui) {
				console.log(`Fetching companion drug: ${companionRxcui}`);
				await fetchAndStoreDrug(companionRxcui);
			}
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

<div class="title-holder">
	<div class="title">
		<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
		<h2>a subtitle will go here</h2>
	</div>
	<div class="pillsImages">
		<img class="pillpics" src={asset('/images/pill01.png')} alt="red pill illustration" />
		<img class="pillpics" src={asset('/images/pill02.png')} alt="blue pill illustration" />
		<img class="pillpics" src={asset('/images/pill03.png')} alt="tan pill illustration" />
	</div>
</div>

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
		<h3>Loaded {Object.keys(curatedList).length} Brands</h3>
		<h3>Loaded {Object.keys(loadedDrugs).length} Total</h3>

		<div class="drug-grid">
			{#each Object.values(curatedList) as curatedRxcui}
				{@const drug = loadedDrugs[curatedRxcui]}
				{#if drug}
					<div class="drug-card">
						<h4>{drug.Name}</h4>
						<p><strong>Type:</strong> {drug.IsBrand ? 'Brand' : 'Generic'}</p>
						<ChartContainer
							plottableData={[
								getPricesArray(loadedDrugs[drug.Brand_RxCUI]),
								getPricesArray(loadedDrugs[drug.Generic_RxCUI])
							]
								.flat()
								.filter(Boolean)}
						/>
					</div>
				{/if}
			{/each}
		</div>
		<ChartContainer plottableData={allPlottablePrices} />
	</div>
{/if}

<style>
	/* global(sheet) styling */

	* {
		font-family: Antonio;
	}

	h1 {
		font-size: 96px;
		font-weight: bold;
	}

	h2 {
		font-size: 40px;
		font-weight: bold;
	}

	h3 {
		font-family: fustat;
		font-size: 32px;
		font-weight: 700;
		text-transform: uppercase;
	}

	h4 {
		font-family: fustat;
		font-size: 20px;
		font-weight: 700;
		text-transform: uppercase;
	}

	h5 {
		font-family: fustat;
		font-size: 20px;
		font-weight: normal;
		text-transform: uppercase;
	}

	p {
		font-family: fustat;
		font-size: 16px;
		font-weight: normal;
	}

	.title-holder {
		padding: 40px 40px 40px 40px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.title {
		max-width: 70%;
	}

	.headerTitle {
		margin-bottom: 60px;
	}

	.pillsImages {
		position: relative;
		width: 30%;
		display: flex;
		align-items: center;
	}

	.pillpics {
		position: absolute;
	}

	/* Drug data section styling */
	.loading,
	.error {
		padding: 2rem;
		text-align: center;
		font-family: fustat;
	}

	.error {
		color: red;
	}

	.drug-section {
		padding: 40px;
	}

	.no-data {
		text-align: center;
		padding: 2rem;
		color: #666;
	}

	.drug-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1.5rem;
		margin-top: 2rem;
	}

	.drug-card {
		border: 2px solid #333;
		padding: 1.5rem;
		border-radius: 12px;
		background: #f9f9f9;
		transition: transform 0.2s;
	}

	.drug-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.drug-card h4 {
		margin-top: 0;
		color: #333;
		margin-bottom: 1rem;
	}

	.drug-card p {
		margin: 0.5rem 0;
		font-size: 14px;
	}

	.price-info {
		display: flex;
		justify-content: space-between;
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #ddd;
		font-weight: 600;
	}
</style>
