<script lang="ts">
	import { onMount } from 'svelte';
	import { loadDrugData } from '$lib/scripts/drug-data-loader';
	import type { DrugAllData } from '$lib/scripts/types';

	// Only load data for insulin comparison
	const insulinDrugSearchTerms: Record<string, string> = {
		'285018': 'lantus', // brand - LANTUS 100 UNIT/ML VIAL
		'311041': 'insulin glargine' // generic - INSULIN GLARGINE 100 UNIT/ML VIAL
	};

	// Make props where this component receives a drug rxcui and it exports the old price, new price, percent change, old year, new year


	let drugsData = $state<DrugAllData[]>([]);
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			drugsData = await loadDrugData(insulinDrugSearchTerms);
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('Error loading insulin data:', err);
		}
	});

	// Find insulin glargine (generic) data - rxcui 311041
	let insulinData = $derived(drugsData.find((d) => d.rxcui === '285018'));

	let oldPrice = $derived(
		insulinData && insulinData.prices.length > 0 ? Math.round(insulinData.prices[0].price) : 0
	);

	let newPrice = $derived(
		insulinData && insulinData.prices.length > 0
			? Math.round(insulinData.prices[insulinData.prices.length - 1].price)
			: 0
	);

	let oldYear = $derived(
		insulinData && insulinData.prices.length > 0
			? new Date(insulinData.prices[0].date).getFullYear()
			: 2018
	);

	let newYear = $derived(
		insulinData && insulinData.prices.length > 0
			? new Date(insulinData.prices[insulinData.prices.length - 1].date).getFullYear()
			: 2025
	);

	let percentChange = $derived(
		oldPrice > 0 ? Math.round(((newPrice - oldPrice) / oldPrice) * 100) : 0
	);
</script>

<div class="comparison-container">
	<div class="price-boxes">
		<div class="price-box">
			<span class="year">{oldYear}</span>
			<span class="price">${oldPrice}</span>
			<span class="period">per month</span>
		</div>

		<span class="arrow">→</span>

		<div class="price-box">
			<span class="year">{newYear}</span>
			<span class="price">${newPrice}</span>
			<span class="period">per month</span>
		</div>
	</div>

	<p class="note">
		{Math.abs(percentChange)}% {percentChange < 0 ? 'decrease' : 'increase'} in price
	</p>
</div>

<style>
	.comparison-container {
		margin: 60px 40px;
		max-width: 750px;
	}

	/* h3 {
		font-family: Antonio;
		font-size: 32px;
		font-weight: bold;
		margin-bottom: 30px;
	} */

	.price-boxes {
		display: flex;
		align-items: center;
		gap: 40px;
	}

	.price-box {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.year {
		font-family: Fustat;
		font-size: 16px;
		text-transform: uppercase;
		font-weight: 700;
	}

	.price {
		font-family: Antonio;
		font-size: 64px;
		font-weight: bold;
	}

	.period {
		font-family: Fustat;
		font-size: 14px;
	}

	.arrow {
		font-size: 32px;
		color: #999;
	}

	.note {
		font-family: Fustat;
		font-size: 14px;
		margin-top: 20px;
		color: #666;
	}
</style>
