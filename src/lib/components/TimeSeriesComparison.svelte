<script lang="ts">
	import * as d3 from 'd3';
	import type { DrugAllData, ChartPoint } from '$lib/scripts/types';
	import { getChartPoints } from '$lib/scripts/helper-functions';
	import { loadDrugData } from '$lib/scripts/drug-data-loader';
	import { isDarkMode } from '$lib/stores/theme';
	import { onMount } from 'svelte';

	// PROPS & STATE
	const drugSearchTerms: Record<string, string> = {
		// index 0 
		'105018': 'lamictal', // brand - LAMICTAL 100 MG ORAL TABLET
		'198427': 'lamotrigine', // generic - LAMOTRIGINE 100 MG ORAL TABLET

		// index 1 
		'285018': 'lantus', // brand - LANTUS 100 UNIT/ML VIAL
		'311041': 'insulin glargine', // generic - INSULIN GLARGINE 100 UNIT/ML VIAL

		// index 2
		'352272': 'lexapro', // brand - LEXAPRO 10 MG TABLET
		'349332': 'escitalopram', // generic - ESCITALOPRAM 10 MG TABLET

		// index 3 
		'617320': 'lipitor', // brand - LIPITOR 40 MG TABLET
		'617311': 'atorvastatin', // generic - ATORVASTATIN 40 MG TABLET

		// index 4 
		'607020': 'lyrica', // brand - LYRICA 150 MG CAPSULE
		'483440': 'pregabalin', // generic - PREGABALIN 150 MG CAPSULE

		// index 5 
		'105029': 'neurontin', // brand - NEURONTIN 300 MG ORAL CAPSULE
		'310431': 'gabapentin', // generic - GABAPENTIN 300 MG ORAL CAPSULE

		// index 6 
		'212549': 'norvasc', // brand - NORVASC 5 MG TABLET
		'197361': 'amlodipine', // generic - AMLODIPINE BESYLATE 5 MG TAB

		// index 7 
		'213471': 'provigil', // brand - PROVIGIL 200 MG TABLET
		'205324': 'modafinil', // generic - MODAFINIL 200 MG TABLET

		// index 8 
		'104849': 'prozac', // brand - PROZAC 20 MG PULVULE
		'310385': 'fluoxetine', // generic - FLUOXETINE HCL 20 MG CAPSULE

		// index 9 
		'966158': 'synthroid', // brand - SYNTHROID 25 MG TABLET
		'966220': 'levothyroxine sodium', // generic - LEVOTHYROXINE SODIUM 25 MG TABLET

		// index 10 
		'854832': 'vyvanse', // brand - VYVANSE 20 MG CAPSULE
		'854830': 'lisdexamfetamine', // generic - LISDEXAMFETAMINE 20 MG CAPSULE

		// index 11 
		'208161': 'zoloft', // brand - ZOLOFT 50 MG TABLET
		'312941': 'sertraline' // generic - SERTRALINE HCL 50 MG TABLET
	};

	let drugsData = $state<DrugAllData[]>([]);
	let allLoadedDrugs = $state<DrugAllData[]>([]); // keep all drugs for brand/generic lookups
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);

	interface Props {
		selectedDrugIndex?: number;
	}

	let { selectedDrugIndex = $bindable(8) }: Props = $props();

	let tooltipData = $state<{ date: Date; brandPrice?: number; genericPrice?: number } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let contentWrapperRef = $state<HTMLDivElement>();

	// LAYOUT CONSTANTS
	const colors = { red: '#C9381A', blue: '#3A7CA5', green: '#2D6A4F' };
	let containerWidth = $state(0);
	const availableWidth = $derived(containerWidth - 40); 
	const width = $derived(availableWidth * 0.62 || 900);
	const height = $derived(width * 0.62);
	const margin = { top: 10, right: 5, bottom: 40, left: 40 };
	const smallWidth = $derived(availableWidth * 0.35); 
	const smallHeight = $derived(smallWidth * 0.6);
	const smallMargin = { top: 10, right: 20, bottom: 40, left: 0 };

	// DATA LOADING
	onMount(async () => {
		try {
			const loadedData = await loadDrugData(drugSearchTerms);
			
			// keep all the loaded drugs for brand/generic lookups
			allLoadedDrugs = loadedData;
			
			// there needs to be a specific order - brand RxCUIs in the correct order
			// this has to match the order in parent page's radio buttons/dropdown
			const brandRxcuisInOrder = [
				'105018',  // 0: LAMICTAL
				'285018',  // 1: LANTUS
				'352272',  // 2: LEXAPRO
				'617320',  // 3: LIPITOR
				'607020',  // 4: LYRICA
				'105029',  // 5: NEURONTIN
				'212549',  // 6: NORVASC
				'213471',  // 7: PROVIGIL
				'104849',  // 8: PROZAC
				'966158',  // 9: SYNTHROID
				'854832',  // 10: VYVANSE
				'208161'   // 11: ZOLOFT
			];
			
			drugsData = brandRxcuisInOrder
				.map(rxcui => loadedData.find(drug => drug.rxcui === rxcui))
				.filter(drug => drug !== undefined) as DrugAllData[];

			console.log('Brand drugs in order:');
			drugsData.forEach((drug, i) => console.log(`  ${i}: ${drug.friendlyName}`));

			// set initial to Prozac (index 8)
			selectedDrugIndex = 8;

			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('Error loading drug data:', err);
		}
	});

	// DATA PROCESSING
	const selectedDrug = $derived(drugsData[selectedDrugIndex]);
	const brandDrug = $derived(
		selectedDrug ? allLoadedDrugs.find((d) => d.rxcui === selectedDrug.brandRxcui) || null : null
	);
	const genericDrug = $derived(
		selectedDrug ? allLoadedDrugs.find((d) => d.rxcui === selectedDrug.genericRxcui) || null : null
	);

	const brandChartData = $derived(getChartPoints(brandDrug));
	const genericChartData = $derived(getChartPoints(genericDrug));
	const allDataPoints = $derived([...brandChartData, ...genericChartData]);

	// CHART SCALES & PATHS
	// main chart
	const mainScales = $derived(createScales(allDataPoints, width, height, margin));
	const baseXScale = $derived(mainScales.xScale);
	const baseYScale = $derived(mainScales.yScale);
	let xScale = $derived(baseXScale);
	let yScale = $derived(baseYScale);
	const brandLinePath = $derived(createLinePath(brandChartData, xScale, yScale));
	const genericLinePath = $derived(createLinePath(genericChartData, xScale, yScale));

	// generic chart
	const genericScales = $derived(createScales(genericChartData, smallWidth, smallHeight, margin));
	const baseGenericXScale = $derived(genericScales.xScale);
	const baseGenericYScale = $derived(genericScales.yScale);
	let genericXScale = $derived(baseGenericXScale);
	let genericYScale = $derived(baseGenericYScale);
	const smallGenericLinePath = $derived(
		createLinePath(genericChartData, genericXScale, genericYScale)
	);

	// SVG refs
	let mainSvgRef = $state<SVGSVGElement>();
	let genericSvgRef = $state<SVGSVGElement>();
	let xAxisRef = $state<SVGGElement>();
	let yAxisRef = $state<SVGGElement>();
	let genericXAxisRef = $state<SVGGElement>();
	let genericYAxisRef = $state<SVGGElement>();

	// EFFECTS - AXES RENDERING
	$effect(() => {
		renderXAxis(xAxisRef, xScale, allDataPoints.length);
		renderYAxis(yAxisRef, yScale, allDataPoints.length);
		renderXAxis(genericXAxisRef, genericXScale, genericChartData.length);
		renderYAxis(genericYAxisRef, genericYScale, genericChartData.length);
	});

	// HELPER FUNCTIONS
	function createScales(
		data: ChartPoint[],
		widthVal: number,
		heightVal: number,
		marginVal: typeof margin
	) {
		const hasData = data.length > 0;

		const xScale = d3
			.scaleTime()
			.range([marginVal.left, widthVal - marginVal.right])
			.domain(
				hasData ? (d3.extent(data, (d) => d.date) as [Date, Date]) : [new Date(), new Date()]
			);

		const yScale = d3
			.scaleLinear()
			.range([heightVal - marginVal.bottom, marginVal.top])
			.domain([0, hasData ? (d3.max(data, (d) => d.price * 1.2) ?? 100) : 100])
			.nice();

		return { xScale, yScale };
	}

	function createLinePath(
		data: ChartPoint[],
		xScale: d3.ScaleTime<number, number>,
		yScale: d3.ScaleLinear<number, number>
	): string {
		if (data.length === 0) return '';
		const lineGen = d3
			.line<ChartPoint>()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price))
			.curve(d3.curveStepAfter);
		return lineGen(data) || '';
	}

	function findPriceForMonth(data: ChartPoint[], monthDate: Date): number | undefined {
		if (data.length === 0) return undefined;
		const pointsBefore = data.filter((d) => d.date <= monthDate);
		if (pointsBefore.length === 0) return undefined;
		return pointsBefore[pointsBefore.length - 1].price;
	}

	function renderXAxis(
		ref: SVGGElement | undefined,
		scale: d3.ScaleTime<number, number>,
		dataLength: number
	) {
		if (!ref || dataLength === 0) return;

		d3.select(ref).call(d3.axisBottom(scale).tickFormat(d3.timeFormat('%Y') as any));
	}

	function renderYAxis(
		ref: SVGGElement | undefined,
		scale: d3.ScaleLinear<number, number>,
		dataLength: number
	) {
		if (!ref || dataLength === 0) return;
		const yAxis = d3.axisLeft(scale).tickFormat((d) => `$${d}`);
		d3.select(ref).call(yAxis);
	}
</script>

<!--- CONTENT AREA --->
{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="width-tracker" bind:clientWidth={containerWidth}>
		<div class="content-wrapper" bind:this={contentWrapperRef}>
			<!--- MAIN CHART --->
			<div class="chart-wrapper relative">
				<div class="chart-header">
					<h5 class='generic-label'>Brand Version:</h5>
				</div>
				<div>
					<h4 class='drug-label-brand'>
						{brandDrug ? brandDrug.friendlyName.toUpperCase() : 'Brand'}
					</h4>
					<svg class='chart' {width} {height} role="img" bind:this={mainSvgRef}>
						<defs>
							<clipPath id="timeseries-plot-clip">
								<rect
									x={margin.left}
									y={margin.top}
									width={width - margin.left - margin.right}
									height={height - margin.top - margin.bottom}
								/>
							</clipPath>
						</defs>

						<g clip-path="url(#timeseries-plot-clip)">
							{@render chartLine(brandLinePath, colors.red, true)}
							{@render chartLine(genericLinePath, colors.blue, false)}
							{@render dataPoints(brandChartData, xScale, yScale, colors.red, true)}
							{@render dataPoints(genericChartData, xScale, yScale, colors.blue, false)}
						</g>

						<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}></g>
						<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>
						{@render axisLabels(width, height)}
					</svg>
				</div>
				
			</div>

			<!--- SIDE BAR --->
			<div class="side-bar">
				<div class="controls">
					<div class="flex items-center justify-between">
						<label for="drug-select">Select Drug:</label>
						<span class="text-sm text-gray-500"> * For a 30 day supply</span>
					</div>
					<!-- <ul class="drug-list" role="listbox">
						{#each drugsData
							.map((drug, i) => ({ drug, i }))
							.filter(({ drug }) => drug.isBrand)
							.sort( (a, b) => a.drug.friendlyName.localeCompare(b.drug.friendlyName) ) as { drug, i }}
							<li
								class="drug-list-item"
								class:selected={i === selectedDrugIndex}
								onclick={() => (selectedDrugIndex = i)}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') selectedDrugIndex = i;
								}}
								role="option"
								aria-selected={i === selectedDrugIndex}
								tabindex="0"
							>
								{drug.friendlyName.toUpperCase()}
							</li>
						{/each}
					</ul> -->
				</div>

				<!--- GENERIC CHART --->
				<div class="individual-charts-container">
					<div class='relative'>
						<div class="chart-header">
							<h5 class='generic-label'>Generic Version:</h5>
						</div>
						<div>
							<div class='drug-title'>
								<h4 class='drug-label'>{genericDrug ? genericDrug.friendlyName : ''}</h4>
							</div>
							<svg width={smallWidth} height={smallHeight} role="img" bind:this={genericSvgRef}>
								<!-- Clipping Path Definition -->
								<defs>
									<clipPath id="generic-plot-clip">
										<rect
											x={margin.left}
											y={margin.top}
											width={smallWidth - smallMargin.left - smallMargin.right}
											height={smallHeight - smallMargin.top - smallMargin.bottom}
										/>
									</clipPath>
								</defs>

								<!-- Data Drawing Elements with clipping -->
								<g clip-path="url(#generic-plot-clip)">
									{@render chartLine(smallGenericLinePath, colors.blue, false)}
									{@render dataPoints(genericChartData, genericXScale, genericYScale, colors.blue, false)}
								</g>

								<!-- Axes -->
								<g
									class="x-axis"
									transform="translate(0,{smallHeight - margin.bottom})"
									bind:this={genericXAxisRef}
								></g>
								<g class="y-axis" transform="translate({margin.left},0)" bind:this={genericYAxisRef}></g>

								{@render axisLabels(smallWidth, smallHeight)}
							</svg>
						</div>
						
					</div>
				</div>
			</div>

			<!--- TOOLTIP --->
			{#if tooltipData}
				{@const dateStr = tooltipData.date.toLocaleDateString('en-US', {
					month: 'long',
					year: 'numeric'
				})}
				{@const savings =
					tooltipData.brandPrice !== undefined && tooltipData.genericPrice !== undefined
						? tooltipData.brandPrice - tooltipData.genericPrice
						: undefined}
				{@const savingsPercent =
					savings !== undefined && tooltipData.brandPrice !== undefined
						? (Math.abs(savings) / Math.max(tooltipData.brandPrice, tooltipData.genericPrice!)) *
							100
						: undefined}
				{@const containerRect = contentWrapperRef?.getBoundingClientRect()}
				{@const tooltipX = containerRect ? cursorX - containerRect.left + 15 : 0}
				{@const tooltipY = containerRect ? cursorY - containerRect.top : 0}

				<div class="tooltip" style="left: {tooltipX}px; top: {tooltipY}px;">
					<div class="tooltip-date"><strong>{dateStr}</strong></div>

					{#if tooltipData.brandPrice !== undefined}
						<div class="tooltip-row brand">
							<span class="label" style="color: {colors.red}">Brand:</span>
							<span class="value">${tooltipData.brandPrice.toFixed(2)}</span>
						</div>
					{/if}

					{#if tooltipData.genericPrice !== undefined}
						<div class="tooltip-row generic">
							<span class="label" style="color: {colors.blue}">Generic:</span>
							<span class="value">${tooltipData.genericPrice.toFixed(2)}</span>
						</div>
					{/if}

					{#if savings !== undefined && savingsPercent !== undefined}
						<div class="tooltip-row savings">
							<span class="label" style="color: {colors.green}">Savings:</span>
							<span class="value" style="color: {colors.green}">${savings.toFixed(2)} ({savingsPercent.toFixed(2)}%)</span
							>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}

<!--- SNIPPETS --->
{#snippet axisLabels(width: number, height: number)}

{/snippet}

{#snippet chartLine(linePath: string, color: string, generic: boolean)}
	{#if linePath}
		<path d={linePath} fill="none" style="stroke: {color}" stroke-width=2 />
	{/if}
{/snippet}

{#snippet dataPoints(
	data: ChartPoint[],
	xScale: d3.ScaleTime<number, number>,
	yScale: d3.ScaleLinear<number, number>,
	color: string,
	isBrand: boolean
)}
	{#each data as point}
		<circle
			cx={xScale(point.date)}
			cy={yScale(point.price)}
			r="2"
			fill={color}
			stroke={$isDarkMode ? '#ddd' : '#222'}
			style="cursor: pointer; pointer-events: all;"
			onmouseenter={(e) => {
				if (isBrand) {
					const genericPrice = findPriceForMonth(genericChartData, point.date);
					tooltipData = { date: point.date, brandPrice: point.price, genericPrice };
				} else {
					const brandPrice = findPriceForMonth(brandChartData, point.date);
					tooltipData = { date: point.date, brandPrice, genericPrice: point.price };
				}
				cursorX = e.clientX;
				cursorY = e.clientY;
			}}
			onmouseleave={() => {
				tooltipData = null;
			}}
			onmousemove={(e) => {
				cursorX = e.clientX;
				cursorY = e.clientY;
			}}
		/>
	{/each}
{/snippet}

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
		color: red;
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
		text-transform: uppercase;
	}
	
	h5  {
		font-family: fustat;
		font-size: 1em;
		font-weight: normal;
		text-transform: uppercase;
	}

	p {
		font-family: fustat;
		font-size: 1em;
		font-weight: normal;
	}

	p a {
		font-family: fustat;
		font-size: 16px;
		font-weight: normal;
		color: inherit;
		text-decoration: underline;
	}

	p b {
		font-family: fustat;
		font-size: 16px;
		font-weight: bold;
	}

	.drug-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		max-height: 200px;
		overflow-y: auto;
		border: 1px solid #989898;
		border-radius: 4px;
		display: grid;
		grid-template-columns: 1fr 1fr;
	}

	.drug-list-item {
		padding: 0.5rem 1rem;
		cursor: pointer;
		transition: background-color 0.2s;
		font-family: fustat;
		font-size: 14px;
		background-color: rgba(75, 75, 75, 0.2);
		border-bottom: 1px solid #989898;
		border-right: 1px solid #989898;
	}

	.drug-list-item:nth-child(even) {
		border-right: none;
	}

	.drug-list-item:nth-last-child(-n + 2) {
		border-bottom: none;
	}

	.drug-list-item:hover {
		background-color: rgba(128, 128, 128, 0.15);
	}

	.drug-list-item.selected {
		background-color: #9a2f1f;
		color: white;
		font-weight: 600;
	}

	.drug-list-item:focus {
		outline: 2px solid #54707c;
		outline-offset: -2px;
	}

	.width-tracker {
		margin: 20px 40px;
	}

	.content-wrapper {
		display: flex;
		justify-content: left;
		align-items: stretch;
		border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		box-sizing: border-box;
		position: relative;
		user-select: none;
		-webkit-user-select: none;
	}

	.chart-wrapper {
		padding: 15px;
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		min-width: 0;
	}

	.chart-header {
		margin-bottom: 10px;
	}

	.drug-title {
		margin-top: auto;
		margin-bottom: 10px;
		text-align: center;
	}

	.drug-label-brand {
		text-align: center;
	}

	.chart-header h5 {
		margin: 0 0 4px 0;
	}

	.chart-header h4 {
		margin: 0;
		text-align: center;
	}

	/* .chart-wrapper svg {
		margin-top: auto;
	} */

	.side-bar {
		padding: 15px;
		display: flex;
		flex-direction: column;
		border-left: 1px solid #ccc;
	}

	.controls {
		flex-shrink: 0;
		padding-bottom: 10px;
		border-bottom: 1px solid #ccc;
	}

	.controls > div:first-child {
		margin-bottom: 8px;
	}

	.individual-charts-container {
		margin-top: auto;
		padding-top: 10px;
	}

	svg {
		display: block;
	}

	.tooltip {
		position: absolute;
		background: white;
		color: #000;
		border: 1px solid #ccc;
		border-radius: 8px;
		padding: 12px;
		pointer-events: none;
		box-shadow: 0 0 3px #ccc;
		z-index: 1000;
		min-width: 200px;
		transform: translateY(-50%);
	}

	.tooltip-date {
		margin-bottom: 8px;
		padding-bottom: 8px;
		border-bottom: 1px solid #ddd;
		font-size: 14px;
		color: #000;
	}

	.tooltip-row {
		display: flex;
		justify-content: space-between;
		margin: 6px 0;
		font-size: 13px;
		color: #000;
	}

	.tooltip-row.brand .label {
		font-weight: 600;
		color: inherit;
	}

	.tooltip-row.generic .label {
		font-weight: 600;
		color: inherit;
	}

	.tooltip-row.savings {
		margin-top: 8px;
		padding-top: 8px;
		border-top: 1px solid #ddd;
		font-weight: 600;
		color: #059669;
	}

	.tooltip-row .value {
		font-weight: 600;
		color: #000;
	}

	.generic-label {
		font-family: Antonio;
	}

	.drug-label {
		font-size: 1.1em;
		color: #3A7CA5;
	}

	.drug-label-brand {
		font-size: 1.1em;
		color: #C9381A;
	}
</style>