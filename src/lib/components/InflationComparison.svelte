<!-- inflation comparison chart
shows actual brand/generic prices vs inflation-adjusted expectation
x-axis: year, y-axis: price
-->

<script lang="ts">
	import * as d3 from 'd3';
	import { onMount } from 'svelte';
	import { isDarkMode } from '$lib/stores/theme';

	// the 10 drugs with correct brand/generic pairs
	const drugs = [
		// { name: 'GLUCOPHAGE', brandRxcui: '861008', genericRxcui: '861007' },
		{ name: 'LAMICTAL', brandRxcui: '105018', genericRxcui: '198427' },
		{ name: 'LANTUS', brandRxcui: '285018', genericRxcui: '311041' },
		{ name: 'LEXAPRO', brandRxcui: '352272', genericRxcui: '349332' },
		{ name: 'LIPITOR', brandRxcui: '617320', genericRxcui: '617311' },
		{ name: 'LYRICA', brandRxcui: '607020', genericRxcui: '483440' },
		{ name: 'NEURONTIN', brandRxcui: '105029', genericRxcui: '310431' },
		{ name: 'NORVASC', brandRxcui: '212549', genericRxcui: '197361' },
		{ name: 'PROVIGIL', brandRxcui: '213471', genericRxcui: '205324' },
		{ name: 'PROZAC', brandRxcui: '104849', genericRxcui: '310385' },
		{ name: 'SYNTHROID', brandRxcui: '966220', genericRxcui: '966219' },
		{ name: 'VYVANSE', brandRxcui: '854832', genericRxcui: '854830' },
		{ name: 'ZOLOFT', brandRxcui: '208161', genericRxcui: '312941' }
	];

	interface PricePoint {
		date: Date;
		price: number;
		year: number;
	}

	interface Props {
        selectedDrugIndex?: number;
    }   

	let { selectedDrugIndex = 2 }: Props = $props();

	let loading = $state(false);
	let error = $state<string | null>(null);
	
	let brandPrices = $state<PricePoint[]>([]);
	let inflationLine = $state<PricePoint[]>([]);
	
	let percentDifference = $state(0);
	let tooltipData = $state<{ x: number; y: number; date: Date; price: number; inflationPrice: number; diff: number } | null>(null);
	let chartContainerRef = $state<HTMLDivElement>();

	// layout constants
	let containerWidth = $state(0);
	const width = $derived(containerWidth || 900);
	const height = $derived(width * 0.65);
	const margin = { top: 50, right: 20, bottom: 60, left: 55 };

	// load data on mount and when drug selection changes
	$effect(() => {
		loadDrugData();
	});

	async function loadDrugData() {
		loading = true;
		error = null;
		
		try {
			const drug = drugs[selectedDrugIndex];
			console.log('loading data for:', drug.name);
			
			// load brand prices
			const brandModule = await import(`$lib/data/prices/${drug.brandRxcui}.json`);
			const brandData = brandModule.default;

			// parse brand prices
			const brandPoints: PricePoint[] = [];
			for (const ndc in brandData.prices) {
				for (const [dateStr, price] of Object.entries(brandData.prices[ndc])) {
					const date = parseDate(dateStr);
					if (date) {
						brandPoints.push({
							date,
							price: price as number,
							year: date.getFullYear()
						});
					}
				}
			}

			// sort and deduplicate
			brandPrices = deduplicateByDate(brandPoints);

			// calculate inflation line (use brand as baseline)
			if (brandPrices.length > 0) {
				inflationLine = calculateInflationLine(brandPrices);
				
				// calculate percent difference between final brand price and inflation expectation
				const finalBrand = brandPrices[brandPrices.length - 1].price;
				const finalInflation = inflationLine[inflationLine.length - 1].price;
				percentDifference = ((finalBrand - finalInflation) / finalInflation) * 100;
			}

			console.log('brand points:', brandPrices.length);
			console.log('inflation expectation:', inflationLine.length);
			console.log('percent above inflation:', percentDifference.toFixed(1) + '%');

			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error loading data';
			loading = false;
			console.error('error loading drug data:', err);
		}
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

	function deduplicateByDate(points: PricePoint[]): PricePoint[] {
		// sort by date
		points.sort((a, b) => a.date.getTime() - b.date.getTime());
		
		// keep last price for each date
		const dateMap = new Map<string, PricePoint>();
		for (const point of points) {
			const dateKey = point.date.toISOString().split('T')[0];
			dateMap.set(dateKey, point);
		}
		
		return Array.from(dateMap.values()).sort((a, b) => a.date.getTime() - b.date.getTime());
	}

	function calculateInflationLine(prices: PricePoint[]): PricePoint[] {
		if (prices.length === 0) return [];
		
		const inflationRate = 0.03; // 3% annual inflation
		const startPrice = prices[0].price;
		const startDate = prices[0].date;
		
		// create inflation points for each year from start to end
		const inflationPoints: PricePoint[] = [];
		
		for (const point of prices) {
			const years = (point.date.getTime() - startDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
			const inflatedPrice = startPrice * Math.pow(1 + inflationRate, years);
			
			inflationPoints.push({
				date: point.date,
				price: inflatedPrice,
				year: point.date.getFullYear()
			});
		}
		
		return inflationPoints;
	}

	// chart scales
	const allPoints = $derived([...brandPrices, ...inflationLine]);
	
	function createScales(data: PricePoint[], widthVal: number, heightVal: number) {
		const hasData = data.length > 0;

		const xScale = d3
			.scaleTime()
			.range([margin.left, widthVal - margin.right])
			.domain(
				hasData 
					? (d3.extent(data, (d) => d.date) as [Date, Date])
					: [new Date(2018, 0, 1), new Date(2025, 0, 1)]
			);

		const yScale = d3
			.scaleLinear()
			.range([heightVal - margin.bottom, margin.top])
			.domain([0, hasData ? (d3.max(data, (d) => d.price * 1.1) ?? 100) : 100])
			.nice();

		return { xScale, yScale };
	}

	const scales = $derived(createScales(allPoints, width, height));
	const xScale = $derived(scales.xScale);
	const yScale = $derived(scales.yScale);

	function createLinePath(
		data: PricePoint[],
		xScale: d3.ScaleTime<number, number>,
		yScale: d3.ScaleLinear<number, number>
	): string {
		if (data.length === 0) return '';
		const lineGen = d3
			.line<PricePoint>()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price))
			.curve(d3.curveLinear);
		return lineGen(data) || '';
	}

	const brandPath = $derived(createLinePath(brandPrices, xScale, yScale));
	const inflationPath = $derived(createLinePath(inflationLine, xScale, yScale));

	// svg refs
	let xAxisRef = $state<SVGGElement>();
	let yAxisRef = $state<SVGGElement>();

	// render axes
	$effect(() => {
		if (xAxisRef && allPoints.length > 0) {
			const xAxis = d3.axisBottom(xScale).tickFormat(d3.timeFormat('%Y') as any);
			d3.select(xAxisRef).call(xAxis);
		}
		if (yAxisRef && allPoints.length > 0) {
			const yAxis = d3.axisLeft(yScale).tickFormat((d) => `$${d}`);
			d3.select(yAxisRef).call(yAxis);
		}
	});
</script>

{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error: {error}</p>
	</div>
{:else}
	<div class="chart-container">
		<!-- drug selector -->
		<div class="controls">
			<!-- <label for="drug-select">Select Drug:</label>
			<select id="drug-select" bind:value={selectedDrugIndex} class="drug-dropdown">
				{#each drugs as drug, i}
					<option value={i}>{drug.name}</option>
				{/each}
			</select> -->
			
			{#if percentDifference !== 0}
				<div class="difference-display">
					Brand price is 
					<strong class:above={percentDifference > 0} class:below={percentDifference < 0}>
						{Math.abs(percentDifference).toFixed(1)}%
						{percentDifference > 0 ? 'above' : 'below'}
					</strong>
					inflation expectation
				</div>
			{/if}
		</div>

		<div class="width-tracker" bind:clientWidth={containerWidth}>
			<div class="chart-area" bind:this={chartContainerRef}>
				<svg {width} {height} role="img">
					<!-- shaded area between brand and inflation lines -->
					{#if brandPrices.length > 0 && inflationLine.length > 0}
						{@const areaPath = (() => {
							// create area path
							let path = `M ${xScale(brandPrices[0].date)} ${yScale(brandPrices[0].price)}`;
							
							// top line (brand prices)
							for (let i = 1; i < brandPrices.length; i++) {
								path += ` L ${xScale(brandPrices[i].date)} ${yScale(brandPrices[i].price)}`;
							}
							
							// bottom line (inflation, reversed)
							for (let i = inflationLine.length - 1; i >= 0; i--) {
								path += ` L ${xScale(inflationLine[i].date)} ${yScale(inflationLine[i].price)}`;
							}
							
							path += ' Z'; // close path
							return path;
						})()}
						<path
							d={areaPath}
							fill="#9a2f1f"
							opacity="0.2"
						/>
					{/if}

					<!-- brand price line -->
					{#if brandPath}
						<path
							d={brandPath}
							fill="none"
							stroke="#9a2f1f"
							stroke-width="1.5"
						/>
					{/if}

					<!-- inflation expectation line (solid gray) -->
					{#if inflationPath}
						<path
							d={inflationPath}
							fill="none"
							stroke="#666"
							stroke-width="1.5"
						/>
					{/if}

					<!-- data points on brand line -->
					{#each brandPrices as point, i}
						{@const inflationPoint = inflationLine[i]}
						{@const diff = inflationPoint ? ((point.price - inflationPoint.price) / inflationPoint.price) * 100 : 0}
						<circle
							cx={xScale(point.date)}
							cy={yScale(point.price)}
							r="3"
							fill="#9a2f1f"
							stroke="white"
							stroke-width="1"
						></circle>
						<circle
							cx={xScale(point.date)}
							cy={yScale(point.price)}
							r="4"
							fill="transparent"
							stroke="transparent"
							stroke-width="none"
							style="cursor: pointer;"
							onmouseenter={(e) => {
								const rect = chartContainerRef?.getBoundingClientRect();
								tooltipData = {
									x: rect ? e.clientX - rect.left : 0,
									y: rect ? e.clientY - rect.top : 0,
									date: point.date,
									price: point.price,
									inflationPrice: inflationPoint?.price || 0,
									diff: diff
								};
							}}
							onmouseleave={() => {
								tooltipData = null;
							}}
							onmousemove={(e) => {
								if (tooltipData) {
									const rect = chartContainerRef?.getBoundingClientRect();
									tooltipData = {
										...tooltipData,
										x: rect ? e.clientX - rect.left : 0,
										y: rect ? e.clientY - rect.top : 0
									};
								}
							}}
						/>
					{/each}

					<!-- axes -->
					<g
						class="x-axis"
						transform="translate(0,{height - margin.bottom})"
						bind:this={xAxisRef}
					></g>
					<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

					<!-- y-axis label -->
					<text
						transform="rotate(-90)"
						x={-(height / 2)}
						y={15}
						text-anchor="middle"
						class="axis-label"
					>
						Price (30-day supply)
					</text>

					<!-- x-axis label -->
					<text
						x={width / 2}
						y={height - 10}
						text-anchor="middle"
						class="axis-label"
					>
						Year
					</text>

					<!-- legend -->
						<g transform="translate({width - margin.right - 115}, {margin.top - 40})">
						<!-- brand -->
						<line x1="0" y1="0" x2="30" y2="0" stroke="#9a2f1f" stroke-width="2" />
						<text x="35" y="5" class="legend-text">Brand</text>

						<!-- inflation -->
						<line x1="0" y1="25" x2="30" y2="25" stroke="#666" stroke-width="2" />
						<text x="35" y="30" class="legend-text">Inflation (3%)</text>
					</g>
				</svg>

				<!-- tooltip -->
				{#if tooltipData}
					<div class="tooltip" style="left: {tooltipData.x + 15}px; top: {tooltipData.y}px;">
						<div class="tooltip-date">
							<strong>{tooltipData.date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</strong>
						</div>
						<div class="tooltip-row">
							<span class="label">Brand:</span>
							<span class="value">${tooltipData.price.toFixed(2)}</span>
						</div>
						<div class="tooltip-row">
							<span class="label">Inflation:</span>
							<span class="value">${tooltipData.inflationPrice.toFixed(2)}</span>
						</div>
						<div class="tooltip-row">
							<span class="label">Difference:</span>
							<span class="value" class:above={tooltipData.diff > 0} class:below={tooltipData.diff < 0}>
								{tooltipData.diff > 0 ? '+' : ''}{tooltipData.diff.toFixed(1)}%
							</span>
						</div>
					</div>
				{/if}
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
		margin: 0px;
	}

	.controls {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 2rem;
		padding: 1rem;
	}

	.controls label {
		font-family: Antonio;
		font-size: 1em;
		font-weight: 600;
	}

	.drug-dropdown {
		font-family: fustat;
		font-size: 1em;
		padding: 0.5rem 1rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		background-color: rgba(75, 75, 75, 0.1);
		cursor: pointer;
		min-width: 200px;
	}

	.drug-dropdown:focus {
		outline: 2px solid #54707c;
	}

	.difference-display {
		font-family: fustat;
		font-size: 1.1em;
		margin-left: auto;
	}

	.difference-display strong {
		font-weight: 700;
	}

	.difference-display .above {
		color: #9a2f1f;
	}

	.difference-display .below {
		color: #2D6A4F;
	}

	.chart-area {
		position: relative;
	}

	svg {
		display: block;
	}

	.tooltip {
		position: absolute;
		background: white;
		color: #000;
		border: 2px solid #333;
		border-radius: 8px;
		padding: 12px;
		pointer-events: none;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 1000;
		min-width: 150px;
		transform: translateY(-50%);
		font-family: fustat;
	}

	.tooltip-date {
		margin-bottom: 8px;
		padding-bottom: 8px;
		border-bottom: 1px solid #ddd;
		font-size: 14px;
		color: #000;
		font-weight: bold;
	}

	.tooltip-row {
		display: flex;
		justify-content: space-between;
		margin: 6px 0;
		font-size: 13px;
		color: #000;
	}

	.tooltip-row .label {
		font-weight: 600;
		margin-right: 1rem;
	}

	.tooltip-row .value {
		font-weight: 600;
		color: #000;
	}

	.tooltip-row .value.above {
		color: #9a2f1f;
	}

	.tooltip-row .value.below {
		color: #2D6A4F;
	}

	.axis-label {
		font-family: fustat;
		font-size: .9em;
		font-weight: 500;
	}

	.legend-text {
		font-family: fustat;
		font-size: 0.9em;
		fill: #333;
	}

	:global(.x-axis text),
	:global(.y-axis text) {
		font-family: Antonio;
	}
</style>