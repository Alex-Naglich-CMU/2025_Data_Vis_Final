<script lang="ts">
	import type { PageProps } from './$types';
	import { asset } from '$app/paths';
	import { onMount } from 'svelte';

	// Type definitions
	interface DrugPrices {
		[ndc: string]: {
			[date: string]: number;
		};
	}

	interface DrugData {
		searchName: string;
		RxCUI: string;
		Name: string;
		IsBrand: boolean;
		Brand_RxCUI: string | null;
		Generic_RxCUI: string | null;
		prices: DrugPrices;
	}

	interface SearchIndexEntry {
		rxcui: string;
		name: string;
		is_brand: boolean;
	}

	interface SearchIndex {
		[key: string]: SearchIndexEntry;
	}

	interface PricePoint {
		ndc: string;
		date: string;
		price: number;
		drugName: string;
		rxcui: string;
		isBrand: boolean;
	}

	interface AveragePrice {
		date: string;
		averagePrice: number;
		count: number;
	}

	// List of drugs we want to visualize (partial names)
	const drugSearchTerms: string[] = [
		'lipitor',
		'insulin',
		'synthroid',
		'metformin',
		'lisdexamfetamine',
		'fluoxetine',
		'isotretinoin',
		'amlodipine'
	];

	// State with proper types
	let drugsData = $state<DrugData[]>([]);
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			// Load the search index
			const searchIndexResponse = await fetch('/data/search_index.json');
			const searchIndex: SearchIndex = await searchIndexResponse.json();

			console.log('Search index loaded:', Object.keys(searchIndex).slice(0, 10)); // Debug: show first 10 keys

			// For each drug search term, find matching drugs
			const loadPromises = drugSearchTerms.map(async (searchTerm): Promise<DrugData | null> => {
				const searchTermLower = searchTerm.toLowerCase();
				
				// Find drug by partial match in the search index
				let drugInfo: SearchIndexEntry | null = null;
				let matchedKey: string | null = null;

				for (const [key, value] of Object.entries(searchIndex)) {
					if (key.includes(searchTermLower)) {
						drugInfo = value;
						matchedKey = key;
						break; // Take first match
					}
				}

				if (!drugInfo) {
					console.warn(`Drug matching "${searchTerm}" not found in search index`);
					return null;
				}

				console.log(`Found match: "${searchTerm}" → "${matchedKey}"`);

				// Load the price JSON file
				const rxcui = drugInfo.rxcui;
				const priceResponse = await fetch(`/data/prices/${rxcui}.json`);
				const priceData = await priceResponse.json();

				return {
					searchName: searchTerm,
					...priceData
				} as DrugData;
			});

			// Wait for all drugs to load
			const results = await Promise.all(loadPromises);
			drugsData = results.filter((drug): drug is DrugData => drug !== null);
			loading = false;
			
			console.log('Loaded drugs:', $state.snapshot(drugsData)); // Use $state.snapshot for logging
			
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('Error loading drug data:', err);
		}
	});

	// Helper function to get all prices as an array
	function getPricesArray(drug: DrugData): PricePoint[] {
		if (!drug || !drug.prices) return [];
		
		const pricesArray: PricePoint[] = [];
		
		for (const [ndc, dates] of Object.entries(drug.prices)) {
			for (const [date, price] of Object.entries(dates)) {
				pricesArray.push({
					ndc,
					date,
					price,
					drugName: drug.Name,
					rxcui: drug.RxCUI,
					isBrand: drug.IsBrand
				});
			}
		}
		
		pricesArray.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
		return pricesArray;
	}

	// Helper to get average price per date
	function getAveragePrices(drug: DrugData): AveragePrice[] {
		if (!drug || !drug.prices) return [];
		
		const dateMap: { [date: string]: number[] } = {};
		
		for (const [ndc, dates] of Object.entries(drug.prices)) {
			for (const [date, price] of Object.entries(dates)) {
				if (!dateMap[date]) {
					dateMap[date] = [];
				}
				dateMap[date].push(price);
			}
		}
		
		const averages: AveragePrice[] = Object.entries(dateMap).map(([date, prices]) => ({
			date,
			averagePrice: prices.reduce((sum, p) => sum + p, 0) / prices.length,
			count: prices.length
		}));
		
		averages.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
		return averages;
	}

	let { data }: PageProps = $props();
</script>

<div class="title-holder">
	<div class="title">
		<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
		<h2>a subtitle will go here</h2>
	</div>
	<div class="pillsImages"> 
		<img class="pillpics" src={asset('/images/pill01.png')} alt="red pill illustration"/>
		<img class="pillpics" src={asset('/images/pill02.png')} alt="blue pill illustration"/>
		<img class="pillpics" src={asset('/images/pill03.png')} alt="tan pill illustration"/>
	</div>
</div>

<!-- Data Loading Status & Drug Cards -->
{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="drug-section">
		<h3>Loaded {drugsData.length} Medications</h3>
		
		{#if drugsData.length === 0}
			<p class="no-data">No drugs found. Check console for details.</p>
		{:else}
			<div class="drug-grid">
				{#each drugsData as drug}
					<div class="drug-card">
						<h4>{drug.Name}</h4>
						<p><strong>Type:</strong> {drug.IsBrand ? 'Brand' : 'Generic'}</p>
						<p><strong>Data Points:</strong> {getPricesArray(drug).length}</p>
						
						{#if getPricesArray(drug).length > 0}
							{@const prices = getPricesArray(drug)}
							<p class="price-info">
								<span>First: ${prices[0].price.toFixed(2)}</span>
								<span>Latest: ${prices[prices.length - 1].price.toFixed(2)}</span>
							</p>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
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
	.loading, .error {
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
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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