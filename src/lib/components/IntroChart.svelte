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

	let increased = $state(0);
	let decreased = $state(0);
	let stayedSame = $state(0);
	let total = $state(0);

	// layout
	const width = 600;
	const height = 600;
	const radius = Math.min(width, height) / 2 - 40;

	onMount(async () => {
		try {
			const searchIndexModule = await import('$lib/data/search_index_all.json');
			searchIndex = searchIndexModule.default;
			console.log('search index loaded:', Object.keys(searchIndex).length, 'entries');

			await analyzeAllDrugs();
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('error loading search index:', err);
		}
	});

	async function analyzeAllDrugs() {
		loading = true;
		let increasedCount = 0;
		let decreasedCount = 0;
		let stayedSameCount = 0;
		let totalCount = 0;
		let skippedCount = 0;

		try {
			let processed = 0;
			const totalEntries = Object.keys(searchIndex).length;

			for (const [rxcui, data] of Object.entries(searchIndex)) {
				processed++;
				if (processed % 500 === 0) {
					console.log(`processed ${processed}/${totalEntries} drugs`);
				}

				const drugData = data as any;

				try {
					const priceModule = await import(`$lib/data/prices/${rxcui}.json`);
					const priceData = priceModule.default;

					if (!priceData.prices || Object.keys(priceData.prices).length === 0) {
						skippedCount++;
						console.log(`SKIPPED ${rxcui} (${drugData.name}): no prices object`);
						continue;
					}

					// get first and last prices
					const { firstPrice, lastPrice, firstDate, lastDate } = getFirstAndLastPrices(priceData.prices);

					if (firstPrice === null || lastPrice === null || firstPrice <= 0) {
						skippedCount++;
						console.log(`SKIPPED ${rxcui} (${drugData.name}): invalid prices (first: ${firstPrice}, last: ${lastPrice})`);
						continue;
					}

					totalCount++;

					// check if it's a single entry drug
					const isSingleEntry = firstDate && lastDate && firstDate.getTime() === lastDate.getTime();
					
					const percentChange = ((lastPrice - firstPrice) / firstPrice) * 100;

					if (percentChange > 1) {
						increasedCount++;
						console.log(`INCREASED: ${drugData.name} - first: $${firstPrice.toFixed(2)}, last: $${lastPrice.toFixed(2)}, change: +${percentChange.toFixed(1)}%`);
					} else if (percentChange < -1) {
						decreasedCount++;
						console.log(`DECREASED: ${drugData.name} - first: $${firstPrice.toFixed(2)}, last: $${lastPrice.toFixed(2)}, change: ${percentChange.toFixed(1)}%`);
					} else {
						stayedSameCount++;
						if (isSingleEntry) {
							console.log(`STAYED SAME (single entry): ${drugData.name} - price: $${firstPrice.toFixed(2)}`);
						} else {
							console.log(`STAYED SAME: ${drugData.name} - first: $${firstPrice.toFixed(2)}, last: $${lastPrice.toFixed(2)}, change: ${percentChange.toFixed(1)}%`);
						}
					}
				} catch (e) {
					skippedCount++;
					console.log(`SKIPPED ${rxcui} (${drugData.name}): no price file found`);
					// skip drugs without price data
				}
			}

			increased = increasedCount;
			decreased = decreasedCount;
			stayedSame = stayedSameCount;
			total = totalCount;

			priceChanges = [
				{
					category: 'Increased',
					count: increasedCount,
					percentage: (increasedCount / totalCount) * 100,
					color: '#9a2f1f'
				},
				{
					category: 'Decreased',
					count: decreasedCount,
					percentage: (decreasedCount / totalCount) * 100,
					color: '#2D6A4F'
				},
				{
					category: 'Stayed Same',
					count: stayedSameCount,
					percentage: (stayedSameCount / totalCount) * 100,
					color: '#A5A5A5'
				}
			];

			console.log('='.repeat(80));
			console.log('ANALYSIS COMPLETE SUMMARY:');
			console.log(`Total drugs in search index: ${totalEntries}`);
			console.log(`Drugs SKIPPED (no data/invalid): ${skippedCount}`);
			console.log(`Drugs ANALYZED: ${totalCount}`);
			console.log(`  - Increased: ${increasedCount} (${((increasedCount/totalCount)*100).toFixed(1)}%)`);
			console.log(`  - Decreased: ${decreasedCount} (${((decreasedCount/totalCount)*100).toFixed(1)}%)`);
			console.log(`  - Stayed Same: ${stayedSameCount} (${((stayedSameCount/totalCount)*100).toFixed(1)}%)`);
			console.log('='.repeat(80));
			loading = false;
		} catch (err) {
			console.error('error analyzing drug data:', err);
			loading = false;
		}
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
		<h3>Drug Price Changes Over Time</h3>
		<p class="subtitle">Comparing first vs. last recorded price for {total.toLocaleString()} drugs</p>

		<div class="chart-wrapper">
			<svg {width} {height}>
				<g transform="translate({width / 2}, {height / 2})">
					{#each arcs as arcData}
						{@const pathData = arc(arcData)}
						{@const labelPos = labelArc.centroid(arcData)}

						<!-- pie slice -->
						<path d={pathData} fill={arcData.data.color} stroke="white" stroke-width="2" />

						<!-- label -->
						<text
							x={labelPos[0]}
							y={labelPos[1]}
							text-anchor="middle"
							class="slice-label"
							fill="white"
							font-weight="bold"
						>
							{arcData.data.percentage.toFixed(1)}%
						</text>
					{/each}
				</g>
			</svg>

			<!-- legend -->
			<div class="legend">
				{#each priceChanges as change}
					<div class="legend-item">
						<div class="legend-color" style="background-color: {change.color}"></div>
						<div class="legend-text">
							<strong>{change.category}</strong>
							<br />
							{change.count.toLocaleString()} drugs ({change.percentage.toFixed(1)}%)
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}

<style>
	* {
		font-family: Antonio;
	}

	.loading,
	.error {
		padding: 2rem;
		text-align: center;
		font-family: fustat;
	}

	.error {
		color: #9a2f1f;
	}

	.chart-container {
		margin: 20px 40px;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
		margin-bottom: 0.5rem;
		text-align: center;
	}

	.subtitle {
		font-family: fustat;
		text-align: center;
		color: #666;
		margin-bottom: 2rem;
	}

	.chart-wrapper {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 3rem;
	}

	svg {
		display: block;
	}

	.slice-label {
		font-family: Antonio;
		font-size: 1.5em;
		pointer-events: none;
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.legend-color {
		width: 40px;
		height: 40px;
		border-radius: 4px;
		flex-shrink: 0;
	}

	.legend-text {
		font-family: fustat;
		font-size: 1em;
	}

	.legend-text strong {
		font-size: 1.1em;
	}
</style>