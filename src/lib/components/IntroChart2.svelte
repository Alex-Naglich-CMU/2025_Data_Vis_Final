<!-- pie chart: % of drugs that increased/decreased/stayed same -->

<script lang="ts">
	import * as d3 from 'd3';
	import { onMount } from 'svelte';

	interface PriceChange {
		category: string;
		count: number;
		percentage: number;
		color: string;
	}

	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchIndex = $state<any>({});
	let priceChanges = $state<PriceChange[]>([]);

	//variables for increase/decrease percentages
	let increased = $state(0);
	let decreased = $state(0);
	let stayedSame = $state(0);
	let total = $state(0);

	//variables for dollar amount increases/decreases
	let increasedDollars = $state(0);
	let decreasedDollars = $state(0);
	let stayedSameDollars = $state(0);
	let totalDollars = $state(0);

	// variable for view mode control
	let viewMode = $state<'dollars' | 'count'>('dollars');

	// layout
	const width = 400;
	const height = 400;
	const radius = Math.min(width, height) / 2 - 40;

	onMount(async () => {
		try {
			const searchIndexModule = await import('$lib/data/search_index_all.json');
			searchIndex = searchIndexModule.default;

			await analyzeAllDrugs();
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
		}
	});

	async function analyzeAllDrugs() {
		loading = true;
		//increase count values 
		let increasedCount = 0;
		let decreasedCount = 0;
		let stayedSameCount = 0;
		let totalCount = 0;
		let skippedCount = 0;
		// Dollar sum values
		let increasedDollarSum = 0;
		let decreasedDollarSum = 0;
		let stayedSameDollarSum = 0;
		let totalDollarSum = 0;

		try {
			let processed = 0;
			const totalEntries = Object.keys(searchIndex).length;

			for (const [rxcui, data] of Object.entries(searchIndex)) {
				processed++;
				if (processed % 500 === 0) {
				}

				const drugData = data as any;

				try {
					const priceModule = await import(`$lib/data/prices/${rxcui}.json`);
					const priceData = priceModule.default;

					if (!priceData.prices || Object.keys(priceData.prices).length === 0) {
						skippedCount++;
						continue;
					}

					// get first and last prices
					const { firstPrice, lastPrice, firstDate, lastDate } = getFirstAndLastPrices(priceData.prices);

					if (firstPrice === null || lastPrice === null || firstPrice <= 0) {
						skippedCount++;
						continue;
					}

					totalCount++;

					// check if it's a single entry drug
					const isSingleEntry = firstDate && lastDate && firstDate.getTime() === lastDate.getTime();
					
					const percentChange = ((lastPrice - firstPrice) / firstPrice) * 100;

					const dollarChange = Math.abs(lastPrice - firstPrice);
					totalDollarSum += dollarChange;

					if (percentChange > 1) {
						increasedCount++;
						increasedDollarSum += dollarChange;
					} else if (percentChange < -1) {
						decreasedCount++;
						decreasedDollarSum += dollarChange;
					} else {
						stayedSameCount++;
						stayedSameDollarSum += dollarChange;
						if (isSingleEntry) {
						} else {
						}
					}
				} catch (e) {
					skippedCount++;
					// skip drugs without price data
				}
			}

			//increase/decrease count
			increased = increasedCount;
			decreased = decreasedCount;
			stayedSame = stayedSameCount;
			total = totalCount;

			//dollar change
			increasedDollars = increasedDollarSum;
			decreasedDollars = decreasedDollarSum;
			stayedSameDollars = stayedSameDollarSum;
			totalDollars = totalDollarSum;

			updatePriceChanges();
			loading = false;

		} catch (err) {
			console.error('error analyzing drug data:', err);
			loading = false;
		}
	}

	function updatePriceChanges() {
		if (viewMode === 'count') {
			priceChanges = [
				{
					category: 'Increased',
					count: increased,
					percentage: (increased / total) * 100,
					color: '#9a2f1f'
				},
				{
					category: 'Decreased',
					count: decreased,
					percentage: (decreased / total) * 100,
					color: '#355B75'
				},
				{
					category: 'Stayed the Same',
					count: stayedSame,
					percentage: (stayedSame / total) * 100,
					color: '#616161'
				}
			];
		} else {
			priceChanges = [
				{
					category: 'Increased',
					count: increasedDollars,
					percentage: (increasedDollars / totalDollars) * 100,
					color: '#9a2f1f'
				},
				{
					category: 'Decreased',
					count: decreasedDollars,
					percentage: (decreasedDollars / totalDollars) * 100,
					color: '#355B75'
				}
			];
		}
	}

	function toggleViewMode() {
		viewMode = viewMode === 'dollars' ? 'count' : 'dollars';
		updatePriceChanges();
	}

	function getFirstAndLastPrices(pricesObj: any): { 
		firstPrice: number | null; 
		lastPrice: number | null;
		firstDate: Date | null;
		lastDate: Date | null;
	} {
		let earliestDate: Date | null = null;
		let latestDate: Date | null = null;
		let firstPrice: number | null = null;
		let lastPrice: number | null = null;

		// find earliest and latest dates across all NDCs
		for (const ndc in pricesObj) {
			for (const [dateStr, price] of Object.entries(pricesObj[ndc])) {
				const date = parseDate(dateStr);
				if (!date) continue;

				if (earliestDate === null || date < earliestDate) {
					earliestDate = date;
					firstPrice = price as number;
				}

				if (latestDate === null || date > latestDate) {
					latestDate = date;
					lastPrice = price as number;
				}
			}
		}

		return { firstPrice, lastPrice, firstDate: earliestDate, lastDate: latestDate };
	}

	function parseDate(dateStr: string): Date | null {
		try {
			const parts = dateStr.split('/');
			if (parts.length === 3) {
				const month = parseInt(parts[0]) - 1;
				const day = parseInt(parts[1]);
				const year = parseInt(parts[2]);
				return new Date(year, month, day);
			}
		} catch (e) {
			console.warn('failed to parse date:', dateStr);
		}
		return null;
	}

	// create pie chart
	const pie = d3.pie<PriceChange>().value((d) => d.count);

	const arc = d3
		.arc<d3.PieArcDatum<PriceChange>>()
		.innerRadius(0)
		.outerRadius(radius);

	const labelArc = d3
		.arc<d3.PieArcDatum<PriceChange>>()
		.innerRadius(radius * 0.6)
		.outerRadius(radius * 0.6);

	const arcs = $derived(pie(priceChanges));
</script>

{#if loading}
	<div class="loading">
		<p>Analyzing drug price changes...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="chart-container">
		<div class="chart-wrapper">
			<svg {width} {height}>
				<g transform="translate({width / 2}, {height / 2})">
					{#each arcs as arcData}
						{@const pathData = arc(arcData)}
						{@const labelPos = labelArc.centroid(arcData)}

						<!-- pie slice -->
						<path d={pathData} fill={arcData.data.color} stroke="#fcfbf5" stroke-width="1.5" />

						<!-- label -->
						<text
							x={labelPos[0]}
							y={labelPos[1]}
							text-anchor="middle"
							class="slice-label"
							fill="#fcfbf5"
							font-weight="bold"
						>
							{arcData.data.percentage.toFixed(1)}%
						</text>
					{/each}
				</g>
			</svg>

			<!-- legend -->
			<div class="legend">
				{#if viewMode === 'count'}
					<h4>Between 2017 and 2025 ...</h4>
					{#each priceChanges as change}
						<div class="legend-item">
							<!-- <div class="legend-color" style="background-color: {change.color}"></div> -->
							<div class="legend-text">
								<h4 style="color: {change.color}">{change.percentage.toFixed(1)}%</h4>
								<h6 class="category"> of drug prices <b>{change.category}</b></h6>
							</div>
						</div>
					{/each}
					<h6 class='hook'>But is that the whole story?</h6>
				{:else}
					<div class='price-hook'>
						<!-- <h4>The amount the price changed by:</h4> -->
					</div>
					{#each priceChanges as change}
						<div class="legend-item">
							<!-- <div class="legend-color" style="background-color: {change.color}"></div> -->
							<div class="legend-text">
								<h6>Combined Cost <b>{change.category}</b> by</h6>
								<h4 class="category" style="color: {change.color}">${change.count.toFixed(2)}</h4>
							</div>
						</div>
					{/each}
					<h6 class='price-hook hook'>The total cost of drugs whose prices went up increased by <b>10x</b> more than the cost of the drugs whose prices went down decreased.</h6>

				{/if}
					
			</div>
		</div>
	</div>
{/if}

<style>
	* {
		font-family: Antonio;
	}
	
	h1 {
		font-size: 5em;
		font-weight: bold;
	}

	h2 {
		font-size: 2.5em;
		font-weight: bold;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
	}

	h4 {
		font-family: fustat;
		font-size: 1.3em;
		font-weight: 700;
	}
	
	h5 {
		font-family: fustat;
		font-size: 1em;
		font-weight: normal;
		text-transform: uppercase;
	}

	h6 {
		font-family: fustat;
		font-size: 1em;
		font-weight: 600;
		text-transform: uppercase;
	}

	h6 b{
		font-family: fustat;
		font-size: 1em;
		font-weight: 800;
		text-transform: uppercase;
	}

	p {
		font-family: fustat;
		font-size: 1.1em;
		font-weight: normal;
	}

	p a {
		font-family: fustat;
		font-weight: normal;
		color: inherit;
		text-decoration: underline;
	}

	p b {
		font-family: fustat;
		font-size: 1.1em;
		font-weight: bold;
	}

	.loading,
	.error {
		padding: 2em;
		text-align: center;
		font-family: fustat;
	}

	.error {
		color: #9a2f1f;
	}

	.chart-container {
		margin: 20px 10px;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
		margin-bottom: 0.5em;
		text-align: center;
	}

	.subtitle {
		font-family: fustat;
		text-align: center;
		color: #666;
		margin-bottom: 2em;
	}

	.chart-wrapper {
		display: flex;
		justify-content: start;
		align-items: center;
		gap: 1em;
	}

	svg {
		display: block;
	}

	.slice-label {
		font-family: fustat;
		font-size: .9em;
		pointer-events: none;
		padding: 0;
		margin: 0;
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 1em;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 1em;
	}

	/* .legend-color {
		width: 25px;
		height: 25px;
		border-radius: 4px;
		flex-shrink: 0;
	} */

	.legend-text {
		font-family: fustat;
		font-size: 1em;
		display: flex;
		align-items: center;
	}

	.legend-text strong {
		font-size: 1.1em;
	}

	.category {
		margin-left: 1em;
	}

	.hook {
		font-style: italic;
		font-weight: 400;
		text-transform: none;
	}
	.hook b {
		font-style: italic;
		font-weight: 700;
		text-transform: none;
	}

	.price-hook {
		max-width: 400px;
	}

	.toggle-container {
		display: flex;
		justify-content: center;
		gap: 0;
		margin-bottom: 2em;
	}

	.toggle-button {
		padding: 0.4em 1em;
		font-size: .9em;
		font-family: Fustat;
		background-color: #F6F5EC;
		color: #000000;
		border: 1px solid #ccc;
		cursor: pointer;
		transition: all 0.2s;
	}

	.left-button  {
		min-width: 160px;
		border-radius: 20px 0 0 20px;
		border-right: 1px solid #ccc;
	}

	.right-button {
		min-width: 160px;
		border-radius: 0 20px 20px 0;
		border-left: 1px solid #ccc;
	}

	.toggle-button:hover:not(.active) {
		background-color: #dcdbd5;
	}

	.toggle-button.active {
		background-color: #656565;
		color: white;
		border-color: #3F5339;
	}

</style>