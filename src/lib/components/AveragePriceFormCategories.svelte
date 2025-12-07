<!-- average price by form category bar chart -->

<script lang="ts">
	import * as d3 from 'd3';
	import { onMount } from 'svelte';
	import { categorizeDosageForm } from '$lib/scripts/formCategorizer';

	interface DrugData {
		rxcui: string;
		name: string;
		form: string;
		formCategory: string;
		mostRecentPrice: number;
	}

	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchIndex = $state<any>({});
	let drugsData = $state<DrugData[]>([]);

	// layout constants
	let containerWidth = $state(0);
	const chartWidth = $derived(containerWidth || 900);
	const chartHeight = $derived(chartWidth * 0.6);
	const margin = { top: 40, right: 40, bottom: 100, left: 80 };

	onMount(async () => {
		try {
			// load search index
			const searchIndexModule = await import('$lib/data/search_index_all.json');
			searchIndex = searchIndexModule.default;
			console.log('search index loaded:', Object.keys(searchIndex).length, 'entries');

			await loadAllDrugs();
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('error loading search index:', err);
		}
	});

	async function loadAllDrugs() {
		loading = true;
		const loadedDrugs: DrugData[] = [];

		try {
			// load data for all brand drugs
			for (const [rxcui, data] of Object.entries(searchIndex)) {
				const drugData = data as any;
				if (drugData.is_brand === true) {
					try {
						const priceModule = await import(`$lib/data/prices/${rxcui}.json`);
						const priceData = priceModule.default;

						if (!priceData.prices || Object.keys(priceData.prices).length === 0) {
							continue;
						}

						const form = priceData.Form || 'Unknown';
						const formCategory = categorizeDosageForm(form);
						const mostRecentPrice = getMostRecentPrice(priceData.prices);

						if (mostRecentPrice !== null && formCategory !== 'Other') {
							loadedDrugs.push({
								rxcui,
								name: drugData.name || 'Unknown',
								form,
								formCategory,
								mostRecentPrice: mostRecentPrice / 30 // divide by 30 for daily price
							});
						}
					} catch (e) {
						// skip drugs without price data
					}
				}
			}

			drugsData = loadedDrugs;
			console.log('loaded', loadedDrugs.length, 'brand drugs');
			loading = false;
		} catch (err) {
			console.error('error loading drug data:', err);
			loading = false;
		}
	}

	function getMostRecentPrice(pricesObj: any): number | null {
		let mostRecentDate: Date | null = null;
		let mostRecentPrice: number | null = null;

		for (const ndc in pricesObj) {
			for (const [dateStr, price] of Object.entries(pricesObj[ndc])) {
				const date = parseDate(dateStr);
				if (date && (mostRecentDate === null || date > mostRecentDate)) {
					mostRecentDate = date;
					mostRecentPrice = price as number;
				}
			}
		}

		return mostRecentPrice;
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

	// calculate average price by form category
	const categoryBars = $derived.by(() => {
		const categoryMap = new Map<string, { total: number; count: number }>();

		for (const drug of drugsData) {
			const key = drug.formCategory;
			if (!categoryMap.has(key)) {
				categoryMap.set(key, { total: 0, count: 0 });
			}
			const entry = categoryMap.get(key)!;
			entry.total += drug.mostRecentPrice;
			entry.count += 1;
		}

		const bars = Array.from(categoryMap.entries()).map(([label, data]) => ({
			label,
			value: data.total / data.count,
			count: data.count
		}));

		// sort by price (highest to lowest)
		return bars.sort((a, b) => b.value - a.value);
	});

	// chart scales
	function createScales(data: any[], width: number, height: number) {
		const xScale = d3
			.scaleBand()
			.range([margin.left, width - margin.right])
			.domain(data.map((d) => d.label))
			.padding(0.2);

		const yScale = d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(data, (d) => d.value * 1.1) ?? 1])
			.nice();

		return { xScale, yScale };
	}

	const scales = $derived(createScales(categoryBars, chartWidth, chartHeight));
	const xScale = $derived(scales.xScale);
	const yScale = $derived(scales.yScale);

	// svg refs
	let xAxisRef = $state<SVGGElement>();
	let yAxisRef = $state<SVGGElement>();

	// render axes
	$effect(() => {
		if (xAxisRef && categoryBars.length > 0) {
			d3.select(xAxisRef).call(
				d3.axisBottom(xScale).tickFormat((d) => {
					// wrap long labels
					const text = d as string;
					return text.length > 15 ? text.substring(0, 15) + '...' : text;
				})
			);
		}
		if (yAxisRef && categoryBars.length > 0) {
			d3.select(yAxisRef).call(d3.axisLeft(yScale).tickFormat((d) => `$${d}`));
		}
	});
</script>

{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="chart-container">		
		<div class="width-tracker" bind:clientWidth={containerWidth}>
			<svg width={chartWidth} height={chartHeight} role="img">
				<g>
					{#each categoryBars as bar}
						{@const x = xScale(bar.label) ?? 0}
						{@const y = yScale(bar.value)}
						{@const barWidth = xScale.bandwidth()}
						{@const barHeight = chartHeight - margin.bottom - y}

						<rect
							{x}
							{y}
							width={barWidth}
							height={barHeight}
							fill="#54707c"
							opacity="0.9"
						/>
						<text
							x={x + barWidth / 2}
							y={y - 5}
							text-anchor="middle"
							class="bar-label"
						>
							${bar.value.toFixed(2)}
						</text>
					{/each}
				</g>

				<g
					class="x-axis"
					transform="translate(0,{chartHeight - margin.bottom})"
					bind:this={xAxisRef}
				></g>
				<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

				<!-- Y-axis label -->
				<text
					transform="rotate(-90)"
					x={-(chartHeight / 2)}
					y={15}
					text-anchor="middle"
					class="axis-label"
				>
					Average Daily Price
				</text>

				<!-- X-axis label -->
				<text x={chartWidth / 2} y={chartHeight - 10} text-anchor="middle" class="axis-label">
					Dosage Form Category
				</text>
			</svg>
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
		margin-bottom: 2rem;
		text-align: center;
	}

	.width-tracker {
		border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		padding: 2rem;
		user-select: none;
		-webkit-user-select: none;
	}

	svg {
		display: block;
	}

	.bar-label {
		font-family: fustat;
		font-size: 0.85em;
		font-weight: 600;
		fill: #333;
	}

	.axis-label {
		font-family: fustat;
		font-size: 1em;
		font-weight: 600;
	}

	:global(.x-axis text) {
		font-family: Antonio;
		font-size: 0.9em;
	}

	:global(.y-axis text) {
		font-family: Antonio;
	}
</style>