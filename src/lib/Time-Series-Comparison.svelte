<script lang="ts">
	import * as d3 from 'd3';

	// TYPE DEFINITIONS
	interface PriceDataPoint {
		ndc: string;
		date: string;
		price: number;
		drugName: string;
		rxcui: string;
		isBrand: boolean;
	}

	interface DrugData {
		rxcui: string;
		friendlyName: string;
		fullName: string;
		isBrand: boolean;
		brandRxcui: string | null;
		genericRxcui: string | null;
		prices: PriceDataPoint[];
	}

	interface ChartPoint {
		date: Date;
		price: number;
	}

	interface TooltipData {
		date: Date;
		brandPrice?: number;
		genericPrice?: number;
		savings?: number;
		savingsPercent?: number;
	}

	// PROPS
	const { drugsData = [] }: { drugsData: DrugData[] } = $props();

	// STATE
	let selectedDrugIndex = $state<number>(0);
	let hoveredData = $state<TooltipData | null>(null);
	let mousePosition = $state({ x: 0, y: 0 });
	let hoveredBrandData = $state<ChartPoint | null>(null);
	let brandMousePosition = $state({ x: 0, y: 0 });
	let hoveredGenericData = $state<ChartPoint | null>(null);
	let genericMousePosition = $state({ x: 0, y: 0 });

	// CONSTANTS
	const width = 900;
	const height = 600;
	const margin = { top: 40, right: 40, bottom: 80, left: 80 };

	const smallWidth = 575;
	const smallHeight = 350;
	const smallMargin = { top: 40, right: 40, bottom: 80, left: 80 };

	const colors = {
		red: '#9A2F1F',
		blue: '#54707C',
		green: '#3F5339',
		orange: '#DF7C39',
		tan: '#BFA97F',
		cream: '#F6F5EC'
	};

	// DERIVED DATA
	let selectedDrug = $derived(drugsData[selectedDrugIndex]);

	// Find the matching brand/generic pair
	let brandDrug = $derived.by(() => {
		if (!selectedDrug) return null;
		const brandRxcui = selectedDrug.brandRxcui;
		return drugsData.find((d) => d.rxcui === brandRxcui) || null;
	});

	let genericDrug = $derived.by(() => {
		if (!selectedDrug) return null;
		const genericRxcui = selectedDrug.genericRxcui;
		return drugsData.find((d) => d.rxcui === genericRxcui) || null;
	});

	// Helper function to calculate average price per date
	function calculateChartData(drug: DrugData | null): ChartPoint[] {
		if (!drug || !drug.prices) return [];

		const dateMap: { [date: string]: number[] } = {};

		for (const point of drug.prices) {
			if (!dateMap[point.date]) {
				dateMap[point.date] = [];
			}
			dateMap[point.date].push(point.price);
		}

		const result: ChartPoint[] = Object.entries(dateMap).map(([dateStr, prices]) => ({
			date: new Date(dateStr),
			price: prices.reduce((sum, p) => sum + p, 0) / prices.length
		}));

		result.sort((a, b) => a.date.getTime() - b.date.getTime());
		return result;
	}

	let brandChartData = $derived(calculateChartData(brandDrug));
	let genericChartData = $derived(calculateChartData(genericDrug));

	// Combine all data points for scaling
	let allDataPoints = $derived([...brandChartData, ...genericChartData]);

	// MAIN CHART SCALES
	let xScale = $derived.by(() => {
		if (allDataPoints.length === 0) {
			return d3.scaleTime().range([margin.left, width - margin.right]);
		}

		return d3
			.scaleTime()
			.range([margin.left, width - margin.right])
			.domain(d3.extent(allDataPoints, (d) => d.date) as [Date, Date]);
	});

	let yScale = $derived.by(() => {
		if (allDataPoints.length === 0) {
			return d3
				.scaleLinear()
				.range([height - margin.bottom, margin.top])
				.domain([0, 100]);
		}

		return d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(allDataPoints, (d) => d.price) ?? 100])
			.nice();
	});

	// BRAND CHART SCALES (smaller)
	let brandXScale = $derived.by(() => {
		if (brandChartData.length === 0) {
			return d3.scaleTime().range([smallMargin.left, smallWidth - smallMargin.right]);
		}

		return d3
			.scaleTime()
			.range([smallMargin.left, smallWidth - smallMargin.right])
			.domain(d3.extent(brandChartData, (d) => d.date) as [Date, Date]);
	});

	let brandYScale = $derived.by(() => {
		if (brandChartData.length === 0) {
			return d3
				.scaleLinear()
				.range([smallHeight - smallMargin.bottom, smallMargin.top])
				.domain([0, 100]);
		}

		return d3
			.scaleLinear()
			.range([smallHeight - smallMargin.bottom, smallMargin.top])
			.domain([0, d3.max(brandChartData, (d) => d.price) ?? 100])
			.nice();
	});

	// GENERIC CHART SCALES (smaller)
	let genericXScale = $derived.by(() => {
		if (genericChartData.length === 0) {
			return d3.scaleTime().range([smallMargin.left, smallWidth - smallMargin.right]);
		}

		return d3
			.scaleTime()
			.range([smallMargin.left, smallWidth - smallMargin.right])
			.domain(d3.extent(genericChartData, (d) => d.date) as [Date, Date]);
	});

	let genericYScale = $derived.by(() => {
		if (genericChartData.length === 0) {
			return d3
				.scaleLinear()
				.range([smallHeight - smallMargin.bottom, smallMargin.top])
				.domain([0, 100]);
		}

		return d3
			.scaleLinear()
			.range([smallHeight - smallMargin.bottom, smallMargin.top])
			.domain([0, d3.max(genericChartData, (d) => d.price) ?? 100])
			.nice();
	});

	// MAIN CHART LINE PATHS
	let brandLinePath = $derived.by(() => {
		if (brandChartData.length === 0) return '';

		const lineGen = d3
			.line<ChartPoint>()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price))
			.curve(d3.curveMonotoneX);

		return lineGen(brandChartData) || '';
	});

	let genericLinePath = $derived.by(() => {
		if (genericChartData.length === 0) return '';

		const lineGen = d3
			.line<ChartPoint>()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price))
			.curve(d3.curveMonotoneX);

		return lineGen(genericChartData) || '';
	});

	// SMALL CHART LINE PATHS
	let smallBrandLinePath = $derived.by(() => {
		if (brandChartData.length === 0) return '';

		const lineGen = d3
			.line<ChartPoint>()
			.x((d) => brandXScale(d.date))
			.y((d) => brandYScale(d.price))
			.curve(d3.curveMonotoneX);

		return lineGen(brandChartData) || '';
	});

	let smallGenericLinePath = $derived.by(() => {
		if (genericChartData.length === 0) return '';

		const lineGen = d3
			.line<ChartPoint>()
			.x((d) => genericXScale(d.date))
			.y((d) => genericYScale(d.price))
			.curve(d3.curveMonotoneX);

		return lineGen(genericChartData) || '';
	});

	// MAIN CHART HOVER HANDLERS
	function handleMouseMove(event: MouseEvent) {
		if (allDataPoints.length === 0) return;

		const svgRect = (event.currentTarget as SVGElement).getBoundingClientRect();
		const mouseX = event.clientX - svgRect.left;

		mousePosition = { x: event.clientX, y: event.clientY };

		// Find closest date
		const hoveredDate = xScale.invert(mouseX);

		// Find closest brand point
		const closestBrandPoint =
			brandChartData.length > 0
				? brandChartData.reduce((prev, curr) => {
						return Math.abs(curr.date.getTime() - hoveredDate.getTime()) <
							Math.abs(prev.date.getTime() - hoveredDate.getTime())
							? curr
							: prev;
					})
				: null;

		// Find closest generic point
		const closestGenericPoint =
			genericChartData.length > 0
				? genericChartData.reduce((prev, curr) => {
						return Math.abs(curr.date.getTime() - hoveredDate.getTime()) <
							Math.abs(prev.date.getTime() - hoveredDate.getTime())
							? curr
							: prev;
					})
				: null;

		// Build tooltip data
		if (closestBrandPoint || closestGenericPoint) {
			const brandPrice = closestBrandPoint?.price;
			const genericPrice = closestGenericPoint?.price;

			let savings = undefined;
			let savingsPercent = undefined;

			if (brandPrice && genericPrice) {
				savings = brandPrice - genericPrice;
				// FIX: Calculate percent based on the HIGHER price
				const higherPrice = Math.max(brandPrice, genericPrice);
				savingsPercent = (Math.abs(savings) / higherPrice) * 100;
			}

			hoveredData = {
				date: closestBrandPoint?.date || closestGenericPoint!.date,
				brandPrice,
				genericPrice,
				savings,
				savingsPercent
			};
		}
	}

	function handleMouseLeave() {
		hoveredData = null;
	}

	// BRAND CHART HOVER HANDLERS
	function handleBrandMouseMove(event: MouseEvent) {
		if (brandChartData.length === 0) return;

		const svgRect = (event.currentTarget as SVGElement).getBoundingClientRect();
		const mouseX = event.clientX - svgRect.left;

		brandMousePosition = { x: event.clientX, y: event.clientY };

		const hoveredDate = brandXScale.invert(mouseX);

		const closestPoint = brandChartData.reduce((prev, curr) => {
			return Math.abs(curr.date.getTime() - hoveredDate.getTime()) <
				Math.abs(prev.date.getTime() - hoveredDate.getTime())
				? curr
				: prev;
		});

		hoveredBrandData = closestPoint;
	}

	function handleBrandMouseLeave() {
		hoveredBrandData = null;
	}

	// GENERIC CHART HOVER HANDLERS
	function handleGenericMouseMove(event: MouseEvent) {
		if (genericChartData.length === 0) return;

		const svgRect = (event.currentTarget as SVGElement).getBoundingClientRect();
		const mouseX = event.clientX - svgRect.left;

		genericMousePosition = { x: event.clientX, y: event.clientY };

		const hoveredDate = genericXScale.invert(mouseX);

		const closestPoint = genericChartData.reduce((prev, curr) => {
			return Math.abs(curr.date.getTime() - hoveredDate.getTime()) <
				Math.abs(prev.date.getTime() - hoveredDate.getTime())
				? curr
				: prev;
		});

		hoveredGenericData = closestPoint;
	}

	function handleGenericMouseLeave() {
		hoveredGenericData = null;
	}

	// AXES
	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;
	let brandXAxisRef: SVGGElement;
	let brandYAxisRef: SVGGElement;
	let genericXAxisRef: SVGGElement;
	let genericYAxisRef: SVGGElement;

	$effect(() => {
		if (xAxisRef && allDataPoints.length > 0) {
			const xAxis = d3.axisBottom(xScale).tickFormat(d3.timeFormat('%Y') as any);
			d3.select(xAxisRef)
				.call(xAxis)
				.selectAll('text')
				.attr('transform', 'rotate(-45)')
				.style('text-anchor', 'end')
				.attr('dx', '-.8em')
				.attr('dy', '.15em');
		}
	});

	$effect(() => {
		if (yAxisRef && allDataPoints.length > 0) {
			const yAxis = d3.axisLeft(yScale).tickFormat((d) => `$${d}`);
			d3.select(yAxisRef).call(yAxis);
		}
	});

	$effect(() => {
		if (brandXAxisRef && brandChartData.length > 0) {
			const xAxis = d3.axisBottom(brandXScale).tickFormat(d3.timeFormat('%Y') as any);
			d3.select(brandXAxisRef)
				.call(xAxis)
				.selectAll('text')
				.attr('transform', 'rotate(-45)')
				.style('text-anchor', 'end')
				.attr('dx', '-.8em')
				.attr('dy', '.15em');
		}
	});

	$effect(() => {
		if (brandYAxisRef && brandChartData.length > 0) {
			const yAxis = d3.axisLeft(brandYScale).tickFormat((d) => `$${d}`);
			d3.select(brandYAxisRef).call(yAxis);
		}
	});

	$effect(() => {
		if (genericXAxisRef && genericChartData.length > 0) {
			const xAxis = d3.axisBottom(genericXScale).tickFormat(d3.timeFormat('%Y') as any);
			d3.select(genericXAxisRef)
				.call(xAxis)
				.selectAll('text')
				.attr('transform', 'rotate(-45)')
				.style('text-anchor', 'end')
				.attr('dx', '-.8em')
				.attr('dy', '.15em');
		}
	});

	$effect(() => {
		if (genericYAxisRef && genericChartData.length > 0) {
			const yAxis = d3.axisLeft(genericYScale).tickFormat((d) => `$${d}`);
			d3.select(genericYAxisRef).call(yAxis);
		}
	});

	$effect(() => {
		console.log('ALL DRUGS DEBUG');
		drugsData.forEach((drug) => {
			console.log(`${drug.friendlyName} (${drug.rxcui}):`);
			console.log(`  isBrand: ${drug.isBrand}`);
			console.log(`  brandRxcui: ${drug.brandRxcui}`);
			console.log(`  genericRxcui: ${drug.genericRxcui}`);
		});
	});
</script>

<h4 class="chart-title">Comparing the Cost of Generic & Name-Brand Medications</h4>
<div class="combined-graphic-area">
	<div class="chart-wrapper">
		<svg
			{width}
			{height}
			on:mousemove={handleMouseMove}
			on:mouseleave={handleMouseLeave}
			style="cursor: crosshair;"
		>
			<!-- Brand line (RED) -->
			{#if brandLinePath}
				<path d={brandLinePath} fill="none" style="stroke: {colors.red}" stroke-width="3" />
			{/if}

			<!-- Generic line (BLUE) -->
			{#if genericLinePath}
				<path d={genericLinePath} fill="none" style="stroke: {colors.blue}" stroke-width="3" />
			{/if}

			<!-- Brand data points -->
			{#each brandChartData as point}
				<circle
					cx={xScale(point.date)}
					cy={yScale(point.price)}
					r="4"
					fill={colors.red}
					stroke="white"
					stroke-width="2"
				/>
			{/each}

			<!-- Generic data points -->
			{#each genericChartData as point}
				<circle
					cx={xScale(point.date)}
					cy={yScale(point.price)}
					r="4"
					fill={colors.blue}
					stroke="white"
					stroke-width="2"
				/>
			{/each}

			<!-- Axes -->
			<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}
			></g>
			<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

			<!-- Axis labels -->
			<text text-anchor="middle" x={width / 2} y={height - 10} font-size="14px"> Time </text>

			<text
				text-anchor="middle"
				transform="rotate(-90)"
				x={-height / 2}
				y={20}
				font-size="14px"
			>
				Price ($ Per 30 Day Supply)
			</text>
		</svg>
	</div>

	<div class="side-bar">
		<div class="controls">
			<label for="drug-select" class="dropdown-label">Select Drug:</label>
			<select id="drug-select" bind:value={selectedDrugIndex}>
				{#each drugsData as drug, i}
					{#if drug.isBrand}
						<option value={i}>
							{drug.friendlyName.toUpperCase()}
						</option>
					{/if}
				{/each}
			</select>
			<p>Brand data points: {brandChartData.length}</p>
			<p>Generic data points: {genericChartData.length}</p>
		</div>

		<!-- LEGEND -->
		<div class="legend">
			<h4>Legend</h4>
			{#if brandDrug}
				<div class="legend-item">
					<div class="legend-line" style="border-color: {colors.red}"></div>
					<span>{brandDrug.friendlyName} (Brand)</span>
				</div>
			{/if}
			{#if genericDrug}
				<div class="legend-item">
					<div class="legend-line" style="border-color: {colors.blue}"></div>
					<span>{genericDrug.friendlyName} (Generic)</span>
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- INDIVIDUAL CHARTS SECTION -->
<div class="individual-charts-container">
	<!-- BRAND CHART -->
	<div class="small-chart-wrapper">
		<h4>
			{brandDrug ? brandDrug.friendlyName.toUpperCase() + ' (BRAND)' : 'BRAND'}
		</h4>
		<svg
			width={smallWidth}
			height={smallHeight}
			on:mousemove={handleBrandMouseMove}
			on:mouseleave={handleBrandMouseLeave}
			style="cursor: crosshair;"
		>
			<!-- Brand line (RED) -->
			{#if smallBrandLinePath}
				<path d={smallBrandLinePath} fill="none" style="stroke: {colors.red}" stroke-width="3" />
			{/if}

			<!-- Brand data points -->
			{#each brandChartData as point}
				<circle
					cx={brandXScale(point.date)}
					cy={brandYScale(point.price)}
					r="4"
					fill={colors.red}
					stroke="white"
					stroke-width="2"
				/>
			{/each}

			<!-- Axes -->
			<g
				class="x-axis"
				transform="translate(0,{smallHeight - smallMargin.bottom})"
				bind:this={brandXAxisRef}
			></g>
			<g class="y-axis" transform="translate({smallMargin.left},0)" bind:this={brandYAxisRef}></g>

			<!-- Axis labels -->
			<text text-anchor="middle" x={smallWidth / 2} y={smallHeight - 10} font-size="14px">
				Time
			</text>

			<text
				text-anchor="middle"
				transform="rotate(-90)"
				x={-smallHeight / 2}
				y={20}
				font-size="14px"
			>
				Price ($ Per 30 Day Supply)
			</text>
		</svg>
	</div>

	<!-- GENERIC CHART -->
	<div class="small-chart-wrapper">
		<h4>
			{genericDrug ? genericDrug.friendlyName.toUpperCase() + ' (GENERIC)' : 'GENERIC'}
		</h4>
		<svg
			width={smallWidth}
			height={smallHeight}
			on:mousemove={handleGenericMouseMove}
			on:mouseleave={handleGenericMouseLeave}
			style="cursor: crosshair;"
		>
			<!-- Generic line (BLUE) -->
			{#if smallGenericLinePath}
				<path
					d={smallGenericLinePath}
					fill="none"
					style="stroke: {colors.blue}"
					stroke-width="3"
				/>
			{/if}

			<!-- Generic data points -->
			{#each genericChartData as point}
				<circle
					cx={genericXScale(point.date)}
					cy={genericYScale(point.price)}
					r="4"
					fill={colors.blue}
					stroke="white"
					stroke-width="2"
				/>
			{/each}

			<!-- Axes -->
			<g
				class="x-axis"
				transform="translate(0,{smallHeight - smallMargin.bottom})"
				bind:this={genericXAxisRef}
			></g>
			<g
				class="y-axis"
				transform="translate({smallMargin.left},0)"
				bind:this={genericYAxisRef}
			></g>

			<!-- Axis labels -->
			<text text-anchor="middle" x={smallWidth / 2} y={smallHeight - 10} font-size="14px">
				Time
			</text>

			<text
				text-anchor="middle"
				transform="rotate(-90)"
				x={-smallHeight / 2}
				y={20}
				font-size="14px"
			>
				Price ($ Per 30 Day Supply)
			</text>
		</svg>
	</div>
</div>

<!-- MAIN TOOLTIP -->
{#if hoveredData}
	<div
		class="tooltip"
		style="position: fixed; left: {mousePosition.x + 15}px; top: {mousePosition.y - 80}px;"
	>
		<div class="tooltip-date">
			<strong
				>{hoveredData.date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</strong
			>
		</div>

		{#if hoveredData.brandPrice !== undefined}
			<div class="tooltip-row brand">
				<span class="label" style="color: {colors.red}">Brand:</span>
				<span class="value">${hoveredData.brandPrice.toFixed(2)}</span>
			</div>
		{/if}

		{#if hoveredData.genericPrice !== undefined}
			<div class="tooltip-row generic">
				<span class="label" style="color: {colors.blue}">Generic:</span>
				<span class="value">${hoveredData.genericPrice.toFixed(2)}</span>
			</div>
		{/if}

		{#if hoveredData.savings !== undefined && hoveredData.savingsPercent !== undefined}
			<div class="tooltip-row savings">
				<span class="label" style="color: {colors.green}">Savings:</span>
				<span class="value" style="color: {colors.green}"
					>${hoveredData.savings.toFixed(2)} ({hoveredData.savingsPercent.toFixed(2)}%)</span
				>
			</div>
		{/if}
	</div>
{/if}

<!-- BRAND TOOLTIP -->
{#if hoveredBrandData}
	<div
		class="tooltip"
		style="position: fixed; left: {brandMousePosition.x + 15}px; top: {brandMousePosition.y - 60}px;"
	>
		<div class="tooltip-date">
			<strong
				>{hoveredBrandData.date.toLocaleDateString('en-US', {
					month: 'long',
					year: 'numeric'
				})}</strong
			>
		</div>

		<div class="tooltip-row brand">
			<span class="label" style="color: {colors.red}">Brand Price:</span>
			<span class="value">${hoveredBrandData.price.toFixed(2)}</span>
		</div>
	</div>
{/if}

<!-- GENERIC TOOLTIP -->
{#if hoveredGenericData}
	<div
		class="tooltip"
		style="position: fixed; left: {genericMousePosition.x + 15}px; top: {genericMousePosition.y -
			60}px;"
	>
		<div class="tooltip-date">
			<strong
				>{hoveredGenericData.date.toLocaleDateString('en-US', {
					month: 'long',
					year: 'numeric'
				})}</strong
			>
		</div>

		<div class="tooltip-row generic">
			<span class="label" style="color: {colors.blue}">Generic Price:</span>
			<span class="value">${hoveredGenericData.price.toFixed(2)}</span>
		</div>
	</div>
{/if}

<style>
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

	h4,
	.dropdown-label {
		font-family: fustat;
		font-size: 20px;
		font-weight: 700;
		text-transform: uppercase;
		margin-bottom: 20px;
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

	.controls h3 {
		margin-top: 0;
	}

	.controls select {
		width: 100%;
		max-width: 400px;
		padding: 0.5rem;
		font-size: 16px;
		margin: 10px 0;
	}

	.combined-graphic-area {
		display: flex;
		justify-content: left;
		align-items: top;
		margin-top: 20px;
	}

	.chart-wrapper {
		padding: 0 40px 40px 40px;
		display: flex;
		gap: 30px;
		align-items: flex-start;
	}

	.side-bar {
		padding: 20px 20px 20px 20px;
		border: 1px solid #ccc;
		max-height: 600px;
	}

	.chart-title {
		padding-left: 40px;
		margin-top: 100px;
		margin-bottom: 20px;
	}

	svg {
		border: 1px solid #ccc;
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

	.tooltip {
		background: white;
		border: 2px solid #333;
		border-radius: 8px;
		padding: 12px;
		pointer-events: none;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 1000;
		min-width: 200px;
	}

	.tooltip-date {
		margin-bottom: 8px;
		padding-bottom: 8px;
		border-bottom: 1px solid #ddd;
		font-size: 14px;
	}

	.tooltip-row {
		display: flex;
		justify-content: space-between;
		margin: 6px 0;
		font-size: 13px;
	}

	.tooltip-row.brand .label {
		font-weight: 600;
	}

	.tooltip-row.generic .label {
		font-weight: 600;
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
	}

	/* INDIVIDUAL CHARTS STYLING */
	.individual-charts-container {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-top: 40px;
		padding: 0 40px;
		gap: 20px;
	}

	.small-chart-wrapper {
		margin-bottom: 80px;
	}
</style>