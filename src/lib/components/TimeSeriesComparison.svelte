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
		'617320': 'lipitor', // brand - LIPITOR 40 MG TABLET
		'617311': 'atorvastatin', // generic - ATORVASTATIN 40 MG TABLET

		'861008': 'glucophage', // brand - GLUCOPHAGE 500 MG TABLET
		'861007': 'metformin', // generic - METFORMIN HCL 500 MG TABLET

		'854832': 'vyvanse', // brand - VYVANSE 20 MG CAPSULE
		'854830': 'lisdexamfetamine', // generic - LISDEXAMFETAMINE 20 MG CAPSULE

		'104849': 'prozac', // brand - PROZAC 20 MG PULVULE
		'310385': 'fluoxetine', // generic - FLUOXETINE HCL 20 MG CAPSULE

		'212549': 'norvasc', // brand - NORVASC 5 MG TABLET
		'197361': 'amlodipine', // generic - AMLODIPINE BESYLATE 5 MG TAB

		'208161': 'zoloft', // brand - ZOLOFT 50 MG TABLET
		'312941': 'sertraline', // generic - SERTRALINE HCL 50 MG TABLET

		'352272': 'lexapro', // brand - LEXAPRO 10 MG TABLET
		'349332': 'escitalopram', // generic - ESCITALOPRAM 10 MG TABLET

		'607020': 'lyrica', // brand - LYRICA 150 MG CAPSULE
		'483440': 'pregabalin', // generic - PREGABALIN 150 MG CAPSULE

		'285018': 'lantus', // brand - LANTUS 100 UNIT/ML VIAL
		'311041': 'insulin glargine', // generic - INSULIN GLARGINE 100 UNIT/ML VIAL

		'213471': 'provigil', // brand - PROVIGIL 200 MG TABLET
		'205324': 'modafinil' // generic - MODAFINIL 200 MG TABLET
	};

	let drugsData = $state<DrugAllData[]>([]);
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);

	let selectedDrugIndex = $state<number>(0);

	let tooltipData = $state<{ date: Date; brandPrice?: number; genericPrice?: number } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);

	// ================================================================================================
	// LAYOUT CONSTANTS
	// ================================================================================================
	const colors = { red: '#C9381A', blue: '#3A7CA5', green: '#2D6A4F' };
	let containerWidth = $state(0);
	const availableWidth = $derived(containerWidth - 40); // Account for content-wrapper padding
	const width = $derived(availableWidth * 0.6 || 900);
	const height = $derived(width * 0.6);
	const margin = { top: 40, right: 40, bottom: 60, left: 80 };
	const smallWidth = $derived(availableWidth * 0.4); // Slightly less to account for sidebar padding
	const smallHeight = $derived(smallWidth * 0.5);

	// ================================================================================================
	// DATA LOADING
	// ================================================================================================
	onMount(async () => {
		try {
			drugsData = await loadDrugData(drugSearchTerms);

			// Set initial selected drug to vyvanse if available
			const vyvanseIndex = drugsData.findIndex((d) =>
				d.friendlyName.toLowerCase().includes('vyvanse')
			);
			selectedDrugIndex = vyvanseIndex !== -1 ? vyvanseIndex : 0;

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
	const selectedDrug = $derived(drugsData[selectedDrugIndex]);
	const brandDrug = $derived(
		selectedDrug ? drugsData.find((d) => d.rxcui === selectedDrug.brandRxcui) || null : null
	);
	const genericDrug = $derived(
		selectedDrug ? drugsData.find((d) => d.rxcui === selectedDrug.genericRxcui) || null : null
	);

	const brandChartData = $derived(getChartPoints(brandDrug));
	const genericChartData = $derived(getChartPoints(genericDrug));
	const allDataPoints = $derived([...brandChartData, ...genericChartData]);

	// ================================================================================================
	// CHART SCALES & PATHS
	// ================================================================================================
	// Main chart
	const mainScales = $derived(createScales(allDataPoints, width, height, margin));
	const baseXScale = $derived(mainScales.xScale);
	const baseYScale = $derived(mainScales.yScale);
	let xScale = $derived(baseXScale);
	let yScale = $derived(baseYScale);
	const brandLinePath = $derived(createLinePath(brandChartData, xScale, yScale));
	const genericLinePath = $derived(createLinePath(genericChartData, xScale, yScale));

	// Generic chart
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

	// ================================================================================================
	// EFFECTS - AXES RENDERING
	// ================================================================================================
	$effect(() => {
		renderXAxis(xAxisRef, xScale, allDataPoints.length);
		renderYAxis(yAxisRef, yScale, allDataPoints.length);
		renderXAxis(genericXAxisRef, genericXScale, genericChartData.length);
		renderYAxis(genericYAxisRef, genericYScale, genericChartData.length);
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

	$effect(() => {
		if (genericSvgRef)
			setupZoom(
				genericSvgRef,
				baseGenericXScale,
				baseGenericYScale,
				smallWidth,
				smallHeight,
				(x, y) => {
					genericXScale = x;
					genericYScale = y;
				}
			);
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
	<div class="text-center text-5xl">How much cheaper are generics?</div>
	<div class="width-tracker" bind:clientWidth={containerWidth}>
		<div class="content-wrapper">
			<!---------------------------------- MAIN CHART ---------------------------------->
			<div class="chart-wrapper relative">
				<div
					class="absolute z-10 w-full text-center text-3xl"
					style="font-family: Calibri, sans-serif; font-weight: bold; color: {colors.red};"
				>
					{brandDrug ? brandDrug.friendlyName.toUpperCase() : 'Brand'}
				</div>
				<svg {width} {height} role="img" bind:this={mainSvgRef}>
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
						{@render dataPoints(brandChartData, xScale, yScale, colors.red)}
						{@render dataPoints(genericChartData, xScale, yScale, colors.blue)}
						{@render monthlyHoverZones(
							allDataPoints,
							xScale,
							margin,
							height,
							width,
							(monthDate) => {
								const brandPrice = findPriceForMonth(brandChartData, monthDate);
								const genericPrice = findPriceForMonth(genericChartData, monthDate);
								if (brandPrice !== undefined || genericPrice !== undefined) {
									tooltipData = { date: monthDate, brandPrice, genericPrice };
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
					{@render axisLabels(width, height)}
				</svg>
				<span class="text-center text-sm text-gray-500">
					Left click to drag, mouse wheel to zoom, mouseover for tooltip</span
				>
			</div>

			<!---------------------------------- SIDE BAR ---------------------------------->
			<div class="side-bar">
				<div class="controls mb-6">
					<div class="flex items-center justify-between">
						<label for="drug-select" class="text-xl">Select Drug:</label>
						<span class="text-sm text-gray-500"> * For a 30 day supply</span>
					</div>
					<ul class="drug-list" role="listbox">
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
					</ul>
				</div>

				<!---------------------------------- GENERIC CHART ---------------------------------->
				<div class="individual-charts-container">
					<div class="small-chart-wrapper relative">
						<div
							class="absolute -top-10 z-10 w-full text-center text-3xl"
							style="font-family: Calibri, sans-serif; font-weight: bold; color: {colors.blue};"
						>
							<div>Generic:</div>
							<div>{genericDrug ? genericDrug.friendlyName.toUpperCase() : ''}</div>
						</div>
						<svg width={smallWidth} height={smallHeight} role="img" bind:this={genericSvgRef}>
							<!-- Clipping Path Definition -->
							<defs>
								<clipPath id="generic-plot-clip">
									<rect
										x={margin.left}
										y={margin.top}
										width={smallWidth - margin.left - margin.right}
										height={smallHeight - margin.top - margin.bottom}
									/>
								</clipPath>
							</defs>

							<!-- Data Drawing Elements with clipping -->
							<g clip-path="url(#generic-plot-clip)">
								{@render chartLine(smallGenericLinePath, colors.blue, false)}
								<!-- {@render dataPoints(genericChartData, genericXScale, genericYScale, colors.blue)} -->
								{@render monthlyHoverZones(
									genericChartData,
									genericXScale,
									margin,
									smallHeight,
									smallWidth,
									(monthDate) => {
										const price = findPriceForMonth(genericChartData, monthDate);
										if (price !== undefined) {
											tooltipData = { date: monthDate, genericPrice: price };
										}
									},
									() => {
										tooltipData = null;
									}
								)}
							</g>

							<!-- Axes -->
							<g
								class="x-axis"
								transform="translate(0,{smallHeight - margin.bottom})"
								bind:this={genericXAxisRef}
							></g>
							<g class="y-axis" transform="translate({margin.left},0)" bind:this={genericYAxisRef}
							></g>

							{@render axisLabels(smallWidth, smallHeight)}
						</svg>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
<!---------------------------------- TOOLTIP ---------------------------------->
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
			? (Math.abs(savings) / Math.max(tooltipData.brandPrice, tooltipData.genericPrice!)) * 100
			: undefined}

	<div class="tooltip" style="left: {cursorX}px; top: {cursorY}px;">
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
				<span class="value" style="color: {colors.green}"
					>${savings.toFixed(2)} ({savingsPercent.toFixed(2)}%)</span
				>
			</div>
		{/if}
	</div>
{/if}

<!---------------------------------- SNIPPETS ---------------------------------->
{#snippet axisLabels(width: number, height: number)}
	<!-- X Axis Label -->
	<!-- <text
		text-anchor="middle"
		x={width / 2}
		y={height - 10}
		font-family="Arial, sans-serif"
		font-size="14px"
		font-weight="600"
	>
		Time
	</text> -->

	<!-- Y Axis Label -->
	<!-- <text
		text-anchor="middle"
		transform="rotate(-90)"
		x={-height / 2}
		y={20}
		font-family="Arial, sans-serif"
		font-size="14px"
		font-weight="600"
	>
		Price ($ Per 30 Day Supply)
	</text> -->
{/snippet}

{#snippet chartLine(linePath: string, color: string, generic: boolean)}
	{#if linePath}
		<path d={linePath} fill="none" style="stroke: {color}" stroke-width="{generic ? 4 : 2}" />
	{/if}
{/snippet}

{#snippet dataPoints(
	data: ChartPoint[],
	xScale: d3.ScaleTime<number, number>,
	yScale: d3.ScaleLinear<number, number>,
	color: string
)}
	{#each data as point}
		<circle
			cx={xScale(point.date)}
			cy={yScale(point.price)}
			r="0"
			fill={color}
			stroke={$isDarkMode ? '#ddd' : '#222'}
			stroke-width="0.0"
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

	/* p {
		font-family: fustat;
		font-size: 16px;
		font-weight: normal;
	} */

	.drug-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		max-height: 200px;
		overflow-y: auto;
		border: 1px solid #ccc;
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
	}

	.drug-list-item:hover {
		background-color: #f0f0f0;
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

	:global(body[data-theme='dark']) .drug-list {
		background-color: #2a2a2a;
		border-color: #444;
	}

	:global(body[data-theme='dark']) .drug-list-item:hover {
		background-color: #3a3a3a;
	}

	/* Axis styling is in app.css */	

	.width-tracker {
		margin: 20px 40px;
	}

	.content-wrapper {
		display: flex;
		justify-content: left;
		align-items: top;
		padding: 10px;
		border: 2px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		box-sizing: border-box;
	}

	.chart-wrapper {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.side-bar {
		padding: 0 0 0 20px;
		display: flex;
		flex-direction: column;
		border-left: 2px solid #ccc;
	}

	svg {
		display: block;
	}

	:global(.tooltip) {
		position: fixed;
		background: white;
		color: #000;
		border: 2px solid #333;
		border-radius: 8px;
		padding: 12px;
		pointer-events: none;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 1000;
		min-width: 200px;
		transform: translate(15px, -50%);
	}

	:global(.tooltip-date) {
		margin-bottom: 8px;
		padding-bottom: 8px;
		border-bottom: 1px solid #ddd;
		font-size: 14px;
		color: #000;
	}

	:global(.tooltip-row) {
		display: flex;
		justify-content: space-between;
		margin: 6px 0;
		font-size: 13px;
		color: #000;
	}

	:global(.tooltip-row.brand .label) {
		font-weight: 600;
		color: inherit;
	}

	:global(.tooltip-row.generic .label) {
		font-weight: 600;
		color: inherit;
	}

	:global(.tooltip-row.savings) {
		margin-top: 8px;
		padding-top: 8px;
		border-top: 1px solid #ddd;
		font-weight: 600;
		color: #059669;
	}

	:global(.tooltip-row .value) {
		font-weight: 600;
		color: #000;
	}

	.individual-charts-container {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-top: 40px;
		gap: 60px;
		max-width: 1200px;
	}
</style>
