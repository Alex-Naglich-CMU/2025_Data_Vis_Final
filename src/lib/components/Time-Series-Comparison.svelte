<script lang="ts">
	import * as d3 from 'd3';
	import type { DrugAllData, ChartPoint } from '../scripts/drug-types';
	import { getChartPoints } from '../scripts/helper-functions';

	// ================================================================================================
	// PROPS & STATE
	// ================================================================================================
	const { drugsData = [] }: { drugsData: DrugAllData[] } = $props();

	let selectedDrugIndex = $state<number>(
		drugsData.findIndex((d) => d.friendlyName.toLowerCase().includes('lantus')) !== -1
			? drugsData.findIndex((d) => d.friendlyName.toLowerCase().includes('lantus'))
			: 0
	);

	let tooltipData = $state<{ date: Date; brandPrice?: number; genericPrice?: number } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);

	// ================================================================================================
	// LAYOUT CONSTANTS
	// ================================================================================================
	const colors = { red: '#9A2F1F', blue: '#54707C', green: '#3F5339' };
	let containerWidth = $state(0);
	const width = $derived(containerWidth || 900);
	const height = $derived(width * 0.67);
	const margin = { top: 40, right: 40, bottom: 80, left: 80 };
	const smallWidth = $derived(width * 0.64);
	const smallHeight = $derived(width * 0.39);

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

	// Brand chart
	const brandScales = $derived(createScales(brandChartData, smallWidth, smallHeight, margin));
	const baseBrandXScale = $derived(brandScales.xScale);
	const baseBrandYScale = $derived(brandScales.yScale);
	let brandXScale = $derived(baseBrandXScale);
	let brandYScale = $derived(baseBrandYScale);
	const smallBrandLinePath = $derived(createLinePath(brandChartData, brandXScale, brandYScale));

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
	let mainSvgRef: SVGSVGElement;
	let brandSvgRef: SVGSVGElement;
	let genericSvgRef: SVGSVGElement;
	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;
	let brandXAxisRef: SVGGElement;
	let brandYAxisRef: SVGGElement;
	let genericXAxisRef: SVGGElement;
	let genericYAxisRef: SVGGElement;

	// ================================================================================================
	// EFFECTS - AXES RENDERING
	// ================================================================================================
	$effect(() => {
		renderXAxis(xAxisRef, xScale, allDataPoints.length);
		renderYAxis(yAxisRef, yScale, allDataPoints.length);
		renderXAxis(brandXAxisRef, brandXScale, brandChartData.length);
		renderYAxis(brandYAxisRef, brandYScale, brandChartData.length);
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
		if (brandSvgRef)
			setupZoom(brandSvgRef, baseBrandXScale, baseBrandYScale, smallWidth, smallHeight, (x, y) => {
				brandXScale = x;
				brandYScale = y;
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
			.domain([0, hasData ? (d3.max(data, (d) => d.price) ?? 100) : 100])
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

		d3.select(ref)
			.call(d3.axisBottom(scale).tickFormat(multiFormat as any))
			.selectAll('text')
			.attr('transform', 'rotate(-45)')
			.style('text-anchor', 'end')
			.attr('dx', '-.8em')
			.attr('dy', '.15em');
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

<!---------------------------------- MAIN CONTENT ---------------------------------->
<h4 class="chart-title">Comparing the Cost of Generic & Name-Brand Medications</h4>
<div class="combined-graphic-area">
	<div class="chart-wrapper" bind:clientWidth={containerWidth}>
		<svg {width} {height} role="img" bind:this={mainSvgRef}>
			<defs>
				<clipPath id="main-plot-clip">
					<rect
						x={margin.left}
						y={margin.top}
						width={width - margin.left - margin.right}
						height={height - margin.top - margin.bottom}
					/>
				</clipPath>
			</defs>

			<g clip-path="url(#main-plot-clip)">
				{@render chartLine(brandLinePath, colors.red)}
				{@render chartLine(genericLinePath, colors.blue)}
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

			<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}></g>
			<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>
			{@render axisLabels(width, height)}
		</svg>
	</div>

	<div class="side-bar">
		<div class="controls">
			<label for="drug-select" class="dropdown-label">Select Drug:</label>
			<ul class="drug-list" role="listbox">
				{#each drugsData
					.map((drug, i) => ({ drug, i }))
					.filter(({ drug }) => drug.isBrand)
					.sort((a, b) => a.drug.friendlyName.localeCompare(b.drug.friendlyName)) as { drug, i }}
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

		<!-- LEGEND -->

			{#if genericDrug}
				<div class="legend-item">
					<div class="legend-line" style="border-color: {colors.blue}"></div>
					<span>{genericDrug.friendlyName}</span>
				</div>
			{/if}



	</div>
</div>

<!---------------------------------- INDIVIDUAL CHARTS ---------------------------------->
<div class="individual-charts-container">
	<!---------------- BRAND CHART ------------------>

	<div class="small-chart-wrapper">
		<h4>
			{brandDrug ? brandDrug.friendlyName.toUpperCase() + ' (BRAND)' : 'BRAND'}
		</h4>
		<svg width={smallWidth} height={smallHeight} role="img" bind:this={brandSvgRef}>
			<!-- Clipping Path Definition -->
			<defs>
				<clipPath id="brand-plot-clip">
					<rect
						x={margin.left}
						y={margin.top}
						width={smallWidth - margin.left - margin.right}
						height={smallHeight - margin.top - margin.bottom}
					/>
				</clipPath>
			</defs>

			<!-- Data Drawing Elements with clipping -->
			<g clip-path="url(#brand-plot-clip)">
				{@render chartLine(smallBrandLinePath, colors.red)}
				{@render dataPoints(brandChartData, brandXScale, brandYScale, colors.red)}
				{@render monthlyHoverZones(
					brandChartData,
					brandXScale,
					margin,
					smallHeight,
					smallWidth,
					(monthDate) => {
						const price = findPriceForMonth(brandChartData, monthDate);
						if (price !== undefined) {
							tooltipData = { date: monthDate, brandPrice: price };
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
				bind:this={brandXAxisRef}
			></g>
			<g class="y-axis" transform="translate({margin.left},0)" bind:this={brandYAxisRef}></g>

			{@render axisLabels(smallWidth, smallHeight)}
		</svg>
	</div>

	<!------------------ GENERIC CHART ------------------>

	<div class="small-chart-wrapper">
		<h4>
			{genericDrug ? genericDrug.friendlyName.toUpperCase() + ' (GENERIC)' : 'GENERIC'}
		</h4>
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
				{@render chartLine(smallGenericLinePath, colors.blue)}
				{@render dataPoints(genericChartData, genericXScale, genericYScale, colors.blue)}
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
			<g class="y-axis" transform="translate({margin.left},0)" bind:this={genericYAxisRef}></g>

			{@render axisLabels(smallWidth, smallHeight)}
		</svg>
	</div>
</div>

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
	<text
		text-anchor="middle"
		x={width / 2}
		y={height - 10}
		font-family="Arial, sans-serif"
		font-size="14px"
		font-weight="600"
	>
		Time
	</text>
	<text
		text-anchor="middle"
		transform="rotate(-90)"
		x={-height / 2}
		y={20}
		font-family="Arial, sans-serif"
		font-size="14px"
		font-weight="600"
	>
		Price ($ Per 30 Day Supply)
	</text>
{/snippet}

{#snippet chartLine(linePath: string, color: string)}
	{#if linePath}
		<path d={linePath} fill="none" style="stroke: {color}" stroke-width="3" />
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
			r="4"
			fill={color}
			stroke="white"
			stroke-width="2"
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
				stroke="grey"
				stroke-width="1"
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

	h4,
	.dropdown-label {
		font-family: fustat;
		font-size: 20px;
		font-weight: 700;
		text-transform: uppercase;
		margin-bottom: 20px;
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
		max-height: 300px;
		overflow-y: auto;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	.drug-list-item {
		padding: 0.75rem 1rem;
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

	/* Dark mode support */
	@media (prefers-color-scheme: dark) {
		.drug-list {
			background-color: #2a2a2a;
			border-color: #444;
		}

		.drug-list-item:hover {
			background-color: #3a3a3a;
		}

		svg text {
			fill: #fff;
		}
	}

	:global(body[data-theme='dark']) .drug-list {
		background-color: #2a2a2a;
		border-color: #444;
	}

	:global(body[data-theme='dark']) .drug-list-item:hover {
		background-color: #3a3a3a;
	}

	:global(body[data-theme='dark']) svg text {
		fill: #fff;
	}

	/* Axis styling */
	:global(.x-axis text),
	:global(.y-axis text) {
		font-family: Arial, sans-serif;
		font-size: 12px;
	}

	:global(.x-axis line),
	:global(.y-axis line),
	:global(.x-axis path),
	:global(.y-axis path) {
		stroke: currentColor;
	}

	.combined-graphic-area {
		display: flex;
		justify-content: left;
		align-items: top;
		margin-top: 20px;
		padding: 0 40px;
	}

	.chart-wrapper {
		flex: 1;
		display: flex;
		gap: 30px;
		align-items: flex-start;
		min-width: 0;
	}

	.side-bar {
		padding: 20px 20px 20px 20px;
		border: 1px solid #ccc;
		box-shadow: 0 0 3px #ccc inset;
		max-height: 600px;
	}

	.chart-title {
		padding-left: 40px;
		margin-top: 100px;
		margin-bottom: 20px;
	}

	svg {
		border: 1px solid #ccc;
		box-shadow: 0 0 3px #ccc inset;
		display: block;
	}

	.legend {
		margin-top: 2rem;
		padding-top: 2rem;
		min-width: 200px;
		border-radius: 8px;
	}
	.legend {
		margin: 0 0 10px 0;
		font-size: 14px;
		text-transform: uppercase;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 14px;
		margin: 8px 0;
	}

	.legend-line {
		width: 30px;
		height: 3px;
		border-radius: 2px;
		border-width: 2px;
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
		padding: 0 40px;
		gap: 60px;
		max-width: 1200px;
	}

	.small-chart-wrapper {
		margin-bottom: 80px;
	}
</style>
