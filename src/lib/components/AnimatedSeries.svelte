<script lang="ts">
	import * as d3 from 'd3';
	import type { DrugAllData, ChartPoint } from '$lib/scripts/types';
	import { getChartPoints } from '$lib/scripts/helper-functions';
	import { loadDrugData } from '$lib/scripts/drug-data-loader';
	import { isDarkMode } from '$lib/stores/theme';
	import { onMount } from 'svelte';

	// ================================================================================================
	// PROPS & STATE
	// ================================================================================================
	const drugSearchTerms: Record<string, string> = {
		'617320': 'lipitor', // brand - LIPITOR 40 MG TABLET        		// '617311': 'atorvastatin', // generic - ATORVASTATIN 40 MG TABLET
		'861008': 'glucophage', // brand - GLUCOPHAGE 500 MG TABLET   		// '861007': 'metformin', // generic - METFORMIN HCL 500 MG TABLET
		'854832': 'vyvanse', // brand - VYVANSE 20 MG CAPSULE				// '854830': 'lisdexamfetamine', // generic - LISDEXAMFETAMINE 20 MG CAPSULE
		'104849': 'prozac', // brand - PROZAC 20 MG PULVULE					// '310385': 'fluoxetine', // generic - FLUOXETINE HCL 20 MG CAPSULE
		'212549': 'norvasc', // brand - NORVASC 5 MG TABLET					// '197361': 'amlodipine', // generic - AMLODIPINE BESYLATE 5 MG TAB
		'208161': 'zoloft', // brand - ZOLOFT 50 MG TABLET					// '312941': 'sertraline', // generic - SERTRALINE HCL 50 MG TABLET
		'352272': 'lexapro', // brand - LEXAPRO 10 MG TABLET				// '349332': 'escitalopram', // generic - ESCITALOPRAM 10 MG TABLET
		'607020': 'lyrica', // brand - LYRICA 150 MG CAPSULE				// '483440': 'pregabalin', // generic - PREGABALIN 150 MG CAPSULE
		'285018': 'lantus', // brand - LANTUS 100 UNIT/ML VIAL				// '311041': 'insulin glargine', // generic - INSULIN GLARGINE 100 UNIT/ML VIAL
		'213471': 'provigil' // brand - PROVIGIL 200 MG TABLET				// '205324': 'modafinil' // generic - MODAFINIL 200 MG TABLET
	};

	let drugsData = $state<DrugAllData[]>([]);
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);

	// Track which drug pairs are selected (by brand drug index)
	let selectedDrugIndices = $state<Set<number>>(new Set());

	let tooltipData = $state<{ date: Date; prices: Map<string, number> } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let animationprogress = $state(0);
	let chartContainerRef = $state<HTMLDivElement>();

	// ================================================================================================
	// LAYOUT CONSTANTS
	// ================================================================================================
	// Color palette for drug pairs
	const drugColors = d3.schemeCategory10 as string[];
	// https://d3js.org/d3-scale-chromatic/categorical

	let containerWidth = $state(0);
	const width = $derived(containerWidth * 0.75 || 900);
	const height = $derived(width * 0.6);
	const margin = { top: 40, right: 40, bottom: 60, left: 80 };

	// ================================================================================================
	// DATA LOADING
	// ================================================================================================
	onMount(async () => {
		try {
			drugsData = await loadDrugData(drugSearchTerms);
			// Add all drug pairs to selection by default
			const initialSelection = new Set<number>();
			for (let i = 0; i < drugsData.length; i++) {
				initialSelection.add(i);
			}
			selectedDrugIndices = initialSelection;

			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('Error loading drug data:', err);
		}
	});

	// ================================================================================================
	// DATA PROCESSING
	// ================================================================================================
	// Get brand drug list (for UI)
	const brandDrugs = $derived(
		drugsData
			.map((drug, i) => ({ drug, i }))
			.filter(({ drug }) => drug.isBrand)
			.sort((a, b) => a.drug.friendlyName.localeCompare(b.drug.friendlyName))
	);

	// Interface for line data
	interface LineData {
		data: ChartPoint[];
		color: string;
		label: string;
		isBrand: boolean;
		drugIndex: number;
	}

	// Generate line data for all selected drugs using getChartPoints helper function
	const selectedLines = $derived.by(() => {
		const lines: LineData[] = [];

		selectedDrugIndices.forEach((drugIndex) => {
			const selectedDrug = drugsData[drugIndex];
			if (!selectedDrug) return;

			// Assign color based on position in brandDrugs list for consistency
			const brandDrugPosition = brandDrugs.findIndex(({ i }) => i === drugIndex);
			const color = drugColors[brandDrugPosition % drugColors.length];

			// Get brand drug
			const brandDrug = drugsData.find((d) => d.rxcui === selectedDrug.brandRxcui);
			if (brandDrug) {
				const brandData = getChartPoints(brandDrug);
				lines.push({
					data: brandData,
					color,
					label: brandDrug.friendlyName,
					isBrand: true,
					drugIndex
				});
			}

			// // Get generic drug
			// const genericDrug = drugsData.find((d) => d.rxcui === selectedDrug.genericRxcui);
			// if (genericDrug) {
			// 	const genericData = getChartPoints(genericDrug);
			// 	lines.push({
			// 		data: genericData,
			// 		color,
			// 		label: genericDrug.friendlyName,
			// 		isBrand: false,
			// 		drugIndex
			// 	});
			// }
		});

		return lines;
	});

	// Combine all data points for scale calculation
	const allDataPoints = $derived(selectedLines.flatMap((line) => line.data));

	// ================================================================================================
	// CHART SCALES & PATHS
	// ================================================================================================
	const mainScales = $derived(createScales(allDataPoints, width, height, margin));
	const baseXScale = $derived(mainScales.xScale);
	const baseYScale = $derived(mainScales.yScale);
	let xScale = $derived(baseXScale);
	let yScale = $derived(baseYScale);

	// Generate paths for each line
	const linePaths = $derived(
		selectedLines.map((line) => ({
			...line,
			path: createLinePath(line.data, xScale, yScale)
		}))
	);

	// SVG refs
	let mainSvgRef = $state<SVGSVGElement>();
	let xAxisRef = $state<SVGGElement>();
	let yAxisRef = $state<SVGGElement>();

	// ================================================================================================
	// EFFECTS - AXES RENDERING
	// ================================================================================================
	$effect(() => {
		renderXAxis(xAxisRef, xScale, allDataPoints.length);
		renderYAxis(yAxisRef, yScale, allDataPoints.length);
	});

	// ================================================================================================
	// EFFECTS - ZOOM BEHAVIOR
	// ================================================================================================
	function setupZoom(
		svgRef: SVGSVGElement,
		baseX: d3.ScaleTime<number, number>,
		baseY: d3.ScaleLinear<number, number>,
		w: number,
		h: number,
		onZoom: (newX: any, newY: any) => void
	) {
		const zoomBehavior = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([1, 10])
			.translateExtent([
				[0, 0],
				[w, h]
			])
			.on('zoom', (event: any) => {
				onZoom(event.transform.rescaleX(baseX), event.transform.rescaleY(baseY));
			});
		d3.select(svgRef).call(zoomBehavior);
	}

	$effect(() => {
		if (mainSvgRef)
			setupZoom(mainSvgRef, baseXScale, baseYScale, width, height, (x, y) => {
				xScale = x;
				yScale = y;
			});
	});

	// ================================================================================================
	// HELPER FUNCTIONS
	// ================================================================================================
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
			.domain([0, hasData ? (d3.max(data, (d) => d.price * 1.04) ?? 100) : 100])
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

		const multiFormat = (date: Date) =>
			(d3.timeSecond(date) < date
				? d3.timeFormat('.%L')
				: d3.timeMinute(date) < date
					? d3.timeFormat(':%S')
					: d3.timeHour(date) < date
						? d3.timeFormat('%I:%M')
						: d3.timeDay(date) < date
							? d3.timeFormat('%I %p')
							: d3.timeMonth(date) < date
								? d3.timeWeek(date) < date
									? d3.timeFormat('%a %d')
									: d3.timeFormat('%b %d')
								: d3.timeYear(date) < date
									? d3.timeFormat('%b')
									: d3.timeFormat('%Y'))(date);

		d3.select(ref).call(d3.axisBottom(scale).tickFormat(multiFormat as any));
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

	// Toggle drug selection
	function toggleDrugSelection(index: number) {
		const newSet = new Set(selectedDrugIndices);
		if (newSet.has(index)) {
			newSet.delete(index);
		} else {
			newSet.add(index);
		}
		selectedDrugIndices = newSet;
	}
</script>

<!---------------------------------- CONTENT AREA ---------------------------------->
{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="mt-20 text-center text-5xl">How did drug prices change over time?</div>
	<div class="width-tracker" bind:clientWidth={containerWidth}>
		<div class="content-wrapper">
			<!---------------------------------- MAIN CHART ---------------------------------->
			<div class="chart-wrapper" bind:this={chartContainerRef}>
				<svg {width} {height} role="img" bind:this={mainSvgRef}>
					<defs>
						<clipPath id="animated-series-clip">
							<rect
								x={margin.left}
								y={margin.top}
								width={width - margin.left - margin.right}
								height={height - margin.top - margin.bottom}
							/>
						</clipPath>
					</defs>

					<g clip-path="url(#animated-series-clip)">
						<!-- Draw all lines -->
						{#each linePaths as line}
							{@render chartLine(line.path, line.color, line.isBrand)}
						{/each}

						<!-- Draw all data points -->
						{#each linePaths as line}
							{@render dataPoints(line.data, xScale, yScale, line.color, line.isBrand)}
						{/each}

						<!-- Hover zones -->
						{@render monthlyHoverZones(
							allDataPoints,
							xScale,
							margin,
							height,
							width,
							(monthDate) => {
								const prices = new Map<string, number>();
								linePaths.forEach((line) => {
									const price = findPriceForMonth(line.data, monthDate);
									if (price !== undefined) {
										prices.set(line.label, price);
									}
								});
								if (prices.size > 0) {
									tooltipData = { date: monthDate, prices };
								}
							},
							() => {
								tooltipData = null;
							}
						)}
					</g>

					<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}
					></g>
					<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>
				</svg>
				<span class="text-center text-sm text-gray-500">
					Left click to drag, mouse wheel to zoom, mouseover for tooltip
				</span>

				<!---------------------------------- TOOLTIP (inside chart-wrapper for proper positioning because oh my god it hates scrolling otherwise) ---------------------------------->
				{#if tooltipData}
					{@const dateStr = tooltipData.date.toLocaleDateString('en-US', {
						month: 'long',
						year: 'numeric'
					})}
					{@const containerRect = chartContainerRef?.getBoundingClientRect()}
					{@const tooltipX = containerRect ? cursorX - containerRect.left + 15 : 0}
					{@const tooltipY = containerRect ? cursorY - containerRect.top : 0}

					<div class="tooltip" style="left: {tooltipX}px; top: {tooltipY}px;">
						<div class="tooltip-date"><strong>{dateStr}</strong></div>

						{#each Array.from(tooltipData.prices.entries()) as [label, price]}
							{@const lineData = linePaths.find((l) => l.label === label)}
							<div class="tooltip-row">
								<span class="label" style="color: {lineData?.color || '#000'}">
									{label}:
								</span>
								<span class="value">${price.toFixed(2)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!---------------------------------- SIDE BAR ---------------------------------->
			<div class="side-bar">
				<div class="controls">
					<div class="mb-2 flex items-center justify-between">
						<label for="drug-list" class="text-xl">Select Drugs:</label>
						<span class="text-sm text-gray-500">* For a 30 day supply</span>
					</div>
					<ul class="drug-list" role="listbox">
						{#each brandDrugs as { drug, i }}
							<!-- Get the position and color for the drug -->
							{@const brandDrugPosition = brandDrugs.findIndex(({ i: idx }) => idx === i)}
							{@const color = drugColors[brandDrugPosition % drugColors.length]}
							{@const isSelected = selectedDrugIndices.has(i)}
							<li
								class="drug-list-item"
								class:selected={isSelected}
								onclick={() => toggleDrugSelection(i)}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') toggleDrugSelection(i);
								}}
								role="option"
								aria-selected={isSelected}
								tabindex="0"
								style="border-left: 4px solid {color}; {isSelected
									? `background-color: ${color}70; color: ${color};`
									: ''}"
							>
								<span class="checkmark">{isSelected ? '✓' : ''}</span>
								{drug.friendlyName.toUpperCase()}

								<div style="flex-grow: 1; text-align: right;">
									<!-- This is for showing the inflation info if you like -->
									<input
										type="checkbox"
										class="rounded"
										aria-hidden="true"
										onclick={(e) => e.stopPropagation()}
									/>
								</div>
							</li>
						{/each}
					</ul>
				</div>
			</div>
		</div>
	</div>
{/if}

<!---------------------------------- SNIPPETS ---------------------------------->
{#snippet chartLine(linePath: string, color: string, isBrand: boolean)}
	{#if linePath}
		<path d={linePath} fill="none" style="stroke: {color}" stroke-width="3" />
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
			r="0"
			fill={color}
			stroke={$isDarkMode ? '#ddd' : '#222'}
			stroke-width="0"
			style="pointer-events: none;"
		/>
	{/each}
{/snippet}

{#snippet monthlyHoverZones(
	data: ChartPoint[],
	xScale: d3.ScaleTime<number, number>,
	margin: { top: number; bottom: number },
	height: number,
	width: number,
	onHover: (monthDate: Date) => void,
	onLeave: () => void
)}
	{#if data.length > 0}
		{@const minDate = d3.min(data, (d) => d.date) ?? new Date()}
		{@const maxDate = d3.max(data, (d) => d.date) ?? new Date()}
		{@const monthStarts = d3.utcMonth.range(d3.utcMonth.floor(minDate), d3.utcMonth.ceil(maxDate))}
		{#each monthStarts as monthStart}
			{@const nextMonth = d3.utcMonth.offset(monthStart, 1)}
			{@const midMonth = new Date(
				Date.UTC(monthStart.getUTCFullYear(), monthStart.getUTCMonth(), 15)
			)}
			{@const x1 = xScale(monthStart)}
			{@const x2 = xScale(nextMonth)}
			{@const xMid = xScale(midMonth)}
			{@const isActive = tooltipData?.date === midMonth}

			<rect
				x={x1}
				y={margin.top}
				width={x2 - x1}
				height={height - margin.top - margin.bottom}
				fill="grey"
				opacity={isActive ? 0.3 : 0}
				style="cursor: crosshair; pointer-events: all;"
				role="button"
				tabindex="0"
				onmouseenter={() => onHover(midMonth)}
				onmouseleave={onLeave}
				onmousemove={(e) => {
					cursorX = e.clientX;
					cursorY = e.clientY;
				}}
			/>
			<line
				x1={xMid}
				x2={xMid}
				y1={margin.top}
				y2={height - margin.bottom}
				stroke={$isDarkMode ? '#ddd' : '#222'}
				stroke-width="2"
				opacity={isActive ? 0.3 : 0}
				style="pointer-events: none;"
			/>
		{/each}
	{/if}
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

	.drug-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		max-height: 400px;
		overflow-y: auto;
		border: 2px solid rgba(128, 128, 128, 0.5);
		border-radius: 4px;
	}

	.drug-list-item {
		padding: 0.5rem 1rem;
		cursor: pointer;
		transition: background-color 0.2s;
		font-family: fustat;
		font-size: 14px;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background-color: rgba(75, 75, 75, 0.2);
		border-bottom: 1px solid rgba(128, 128, 128, 0.5);
	}

	.drug-list-item:last-child {
		border-bottom: none;
	}

	.drug-list-item .checkmark {
		width: 1rem;
		font-weight: bold;
	}

	.drug-list-item:hover {
		background-color: rgba(128, 128, 128, 0.15);
	}

	.drug-list-item.selected {
		font-weight: 600;
	}

	.drug-list-item:focus {
		outline: 2px solid #54707c;
		outline-offset: -2px;
	}

	/* Axis styling is in app.css */

	.width-tracker {
		margin: 20px 40px;
	}

	.content-wrapper {
		display: flex;
		justify-content: left;
		align-items: top;
		border: 3px solid #aaa;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		box-sizing: border-box;
	}

	.chart-wrapper {
		padding: 10px 0 0 0;
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
		position: relative;
	}

	.side-bar {
		padding: 10px 10px 0 20px;
		width: 25%;
		display: flex;
		flex-direction: column;
		border-left: 3px solid #aaa;
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
		min-width: 200px;
		max-height: 400px;
		overflow-y: auto;
		transform: translateY(-50%);
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
	}

	.tooltip-row .value {
		font-weight: 600;
		color: #000;
	}
</style>
