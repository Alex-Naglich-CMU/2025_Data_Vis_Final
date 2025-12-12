<script lang="ts">
	import type { DrugData } from '$lib/scripts/types';
	import sampledDrugsRaw from '$lib/scripts/dropChartData';
	import * as d3 from 'd3';
	import { onMount } from 'svelte';

	function convertDates(drugs: any[]): DrugData[] {
		return drugs.map((drug) => ({
			...drug,
			prices: drug.prices.map((p: any) => ({
				...p,
				date: typeof p.date === 'string' ? new Date(p.date) : p.date
			}))
		}));
	}

	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchIndex = $state<any>({});
	let allDrugs = $state<DrugData[]>([]);
	let sampledDrugs: DrugData[] = convertDates(sampledDrugsRaw);
	let displayedDrugs = $state<DrugData[]>(sampledDrugs);
	let currentStage = $state(0); // Start at 0
	let sliderValue = $state(0); // Slider from 0 to 2

	// SVG dimensions
	const maxWidth = 860;
	const width = maxWidth;
	const height = 600;
	const margin = { top: 40, right: 40, bottom: 60, left: 80 };
	const chartWidth = width - margin.left - margin.right;
	const chartHeight = height - margin.top - margin.bottom;

	let svgRef: SVGSVGElement;
	let xScale: d3.ScaleTime<number, number>;
	let yScale: d3.ScaleLogarithmic<number, number>;

	function generateLogTicks(min: number, max: number): number[] {
		const ticks: number[] = [];

		// only use powers of 10 - NO intermediate values
		let magnitude = Math.floor(Math.log10(min));
		const maxMagnitude = Math.ceil(Math.log10(max)) + 1;

		while (magnitude <= maxMagnitude) {
			const tick = Math.pow(10, magnitude);
			if (tick >= min * 0.5 && tick <= max * 2) {
				ticks.push(tick);
			}
			magnitude++;
		}

		// remove the first tick if there are multiple ticks to prevent overlap at bottom
		if (ticks.length > 1) {
			ticks.shift();
		}

		return ticks;
	}

	function initializeChart() {
		if (displayedDrugs.length === 0) {
			console.error('No drugs to display!');
			loading = false;
			return;
		}

		console.log('Initializing chart with', displayedDrugs.length, 'drugs');
		console.log('SVG ref:', svgRef);

		const svg = d3.select(svgRef);
		svg.selectAll('*').remove();

		const g = svg
			.append('g')
			.attr('class', 'chart-group')
			.attr('transform', `translate(${margin.left},${margin.top})`);

		// find price range
		let minPrice = Infinity;
		let maxPrice = -Infinity;

		displayedDrugs.forEach((drug) => {
			drug.prices.forEach((p) => {
				if (p.price > 0) {
					minPrice = Math.min(minPrice, p.price);
					maxPrice = Math.max(maxPrice, p.price);
				}
			});
		});

		console.log('price range:', minPrice, 'to', maxPrice);

		// time extent
		const allDates = displayedDrugs.flatMap((d) => d.prices.map((p) => p.date));
		const minDate = d3.min(allDates) || new Date(2017, 0, 1);
		const maxDate = d3.max(allDates) || new Date(2025, 11, 31);

		// scales
		xScale = d3.scaleTime().domain([minDate, maxDate]).range([0, chartWidth]);

		yScale = d3
			.scaleLog()
			.domain([Math.max(0.01, minPrice * 0.5), maxPrice * 1.2])
			.range([chartHeight, 0])
			.clamp(true);

		// add shaded region centered on Jan 1, 2024 (initially hidden)
		const jan2024 = new Date(2024, 0, 1);
		const shadeStart = new Date(2023, 6, 1); // July 1, 2023 (6 months before Jan 1)
		const shadeEnd = new Date(2024, 6, 1); // July 1, 2024 (6 months after Jan 1)

		g.append('rect')
			.attr('class', 'shade-region')
			.attr('x', xScale(shadeStart))
			.attr('y', 0)
			.attr('width', xScale(shadeEnd) - xScale(shadeStart))
			.attr('height', chartHeight)
			.attr('fill', '#e0e0e0')
			.attr('opacity', 0); // Start hidden

		// add vertical line at Jan 1, 2024 (initially hidden)
		g.append('line')
			.attr('class', 'jan-2024-line')
			.attr('x1', xScale(jan2024))
			.attr('y1', 0)
			.attr('x2', xScale(jan2024))
			.attr('y2', chartHeight)
			.attr('stroke', '#666')
			.attr('stroke-width', 2)
			.attr('stroke-dasharray', '5,5')
			.attr('opacity', 0); // Start hidden

		// axes
		const xAxis = d3.axisBottom(xScale).ticks(8);
		const tickValues = generateLogTicks(minPrice, maxPrice);

		const yAxis = d3
			.axisLeft(yScale)
			.tickValues(tickValues)
			.tickFormat((d) => {
				const num = d as number;
				if (num >= 1) return `$${num}`;
				return `$${num.toFixed(2)}`;
			});

		const xAxisG = g
			.append('g')
			.attr('class', 'x-axis')
			.attr('transform', `translate(0,${chartHeight})`)
			.call(xAxis);

		const yAxisG = g.append('g').attr('class', 'y-axis').call(yAxis);

		// axis labels
		xAxisG
			.append('text')
			.attr('x', chartWidth / 2)
			.attr('y', 45)
			.attr('fill', 'black')
			.attr('font-size', '14px')
			.attr('font-family', 'Antonio')
			.attr('text-anchor', 'middle')
			.text('Year');

		yAxisG
			.append('text')
			.attr('transform', 'rotate(-90)')
			.attr('x', -chartHeight / 2)
			.attr('y', -55)
			.attr('fill', 'black')
			.attr('font-size', '14px')
			.attr('font-family', 'Antonio')
			.attr('text-anchor', 'middle')
			.text('Price per Unit ($)');

		// line generator
		const lineGenerator = d3
			.line<{ date: Date; price: number }>()
			.defined((d) => d.price > 0)
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price));

		// draw lines - initial state
		g.selectAll('.drug-line')
			.data(displayedDrugs)
			.enter()
			.append('path')
			.attr('class', 'drug-line')
			.attr('fill', 'none')
			.attr('stroke', (d) => d.color)
			.attr('stroke-width', 0.3)
			.attr('opacity', 0.95)
			.attr('d', (d) => lineGenerator(d.prices));

		console.log(`Drew ${displayedDrugs.length} lines`);

		// apply initial slider state
		updateChartFromSlider();
		loading = false;
	}

	onMount(async () => {
		setTimeout(() => {
			if (svgRef) {
				initializeChart();
			} else {
				console.error('SVG ref not available');
			}
		}, 100);
	});

	function updateChartFromSlider() {
		const svg = d3.select(svgRef);
		const lines = svg.selectAll('.drug-line');
		const g = svg.select('.chart-group');
		const shadedRegion = g.select('.shade-region');
		const verticalLine = g.select('.jan-2024-line');

		// remove existing annotation if any
		g.selectAll('.annotation').remove();

		if (sliderValue === 0) {
			// Stage 0: Show all drugs, hide line and shade
			lines.attr('opacity', 0.95).attr('stroke-width', 0.3);
			shadedRegion.attr('opacity', 0);
			verticalLine.attr('opacity', 0);
		} else if (sliderValue === 1) {
			// Stage 1: Show only highlighted drugs + show line and shade
			lines
				.attr('opacity', (d: any) => (d.isHighlighted ? 0.75 : 0))
				.attr('stroke-width', (d: any) => (d.isHighlighted ? 1 : 0.3));
			shadedRegion.attr('opacity', 0.3);
			verticalLine.attr('opacity', 1);
		} else {
			// Stage 2: Show highlighted + annotation + line and shade
			lines
				.attr('opacity', (d: any) => (d.isHighlighted ? 0.75 : 0))
				.attr('stroke-width', (d: any) => (d.isHighlighted ? 1 : 0.3));
			shadedRegion.attr('opacity', 0.3);
			verticalLine.attr('opacity', 1);

			addAnnotation();
		}
	}

	function addAnnotation() {
		const svg = d3.select(svgRef);
		const g = svg.select('.chart-group');

		// calculate actual position of highlighted drugs in 2024
		const highlightedDrugs = displayedDrugs.filter((d) => d.isHighlighted);

		// get prices in 2024 for highlighted drugs
		let totalPrice = 0;
		let count = 0;
		const targetDate = new Date(2024, 0, 1); // Jan 1, 2024

		highlightedDrugs.forEach((drug) => {
			const prices2024 = drug.prices.filter((p) => p.date.getFullYear() === 2024);
			if (prices2024.length > 0) {
				const avgPrice = prices2024.reduce((sum, p) => sum + p.price, 0) / prices2024.length;
				totalPrice += avgPrice;
				count++;
			}
		});

		const avgPrice = count > 0 ? totalPrice / count : 5; // fallback to $5

		// calculate data point position
		const dataX = xScale(targetDate);
		const dataY = yScale(avgPrice);

		console.log('Annotation pointing to:', {
			date: targetDate,
			price: avgPrice,
			x: dataX,
			y: dataY
		});

		// position annotation in lower left of chart area (in white space)
		const annotationX = 275; // Left side with padding
		const annotationY = chartHeight - 175; // Near bottom but inside chart

		const annotation = g.append('g').attr('class', 'annotation');

		// arrow pointing from annotation box up to data point
		annotation
			.append('line')
			.attr('x1', annotationX + 200) // From right edge of text box
			.attr('y1', annotationY + 10) // From top area of box
			.attr('x2', dataX - 15)
			.attr('y2', dataY + 75)
			.attr('stroke', '#2D6A4F')
			.attr('stroke-width', 2)
			.attr('marker-end', 'url(#arrowhead)');

		// define arrowhead marker
		svg.select('defs').remove(); // Remove old defs if any
		svg
			.append('defs')
			.append('marker')
			.attr('id', 'arrowhead')
			.attr('markerWidth', 10)
			.attr('markerHeight', 10)
			.attr('refX', 5)
			.attr('refY', 3)
			.attr('orient', 'auto')
			.append('polygon')
			.attr('points', '0 0, 10 3, 0 6')
			.attr('fill', '#2D6A4F');

		// text box
		const textBox = annotation
			.append('g')
			.attr('transform', `translate(${annotationX}, ${annotationY})`);

		textBox
			.append('rect')
			.attr('x', 0)
			.attr('y', 0)
			.attr('width', 200)
			.attr('height', 60)
			.attr('fill', 'white')
			.attr('stroke', '#2D6A4F')
			.attr('stroke-width', 2)
			.attr('rx', 5);

		textBox
			.append('text')
			.attr('x', 100)
			.attr('text-anchor', 'middle')
			.attr('dominant-baseline', 'middle')
			.attr('y', 21)
			.attr('font-family', 'Antonio')
			.attr('font-size', '13px')
			.attr('font-weight', 'bold')
			.attr('fill', '#2D6A4F')
			.text('Driven by American Rescue Plan Act');

		textBox
			.append('text')
			.attr('x', 100)
			.attr('text-anchor', 'middle')
			.attr('dominant-baseline', 'middle')
			.attr('y', 39)
			.attr('font-family', 'Antonio')
			.attr('font-size', '13px')
			.attr('font-weight', 'bold')
			.attr('fill', '#2D6A4F')
			.text('and Medicaid Drug Rebate Program');
	}

	function handleSliderChange(event: Event) {
		const target = event.target as HTMLInputElement;
		sliderValue = parseInt(target.value);
		updateChartFromSlider();
	}

	function reset() {
		sliderValue = 0;
		updateChartFromSlider();
	}
</script>

{#if loading}
	<div class="loading">
		<p>Loading drug price data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="container">
		<p class="subtitle">
			{displayedDrugs.length.toLocaleString()} drugs (sampled from 5,895 total)
		</p>

		<div class="legend">
			<div class="legend-item">
				<div class="legend-color" style="background-color: #355b75"></div>
				<span>Increased (>1%)</span>
			</div>
			<div class="legend-item">
				<div class="legend-color" style="background-color: #95A5A6"></div>
				<span>Stayed Same (±1%)</span>
			</div>
			<div class="legend-item">
				<div class="legend-color" style="background-color: #9a2f1f"></div>
				<span>Decreased (&lt;-1%)</span>
			</div>
		</div>

		<div class="chart-container">
			<svg bind:this={svgRef} {width} {height}></svg>
		</div>

		<div class="slider-container">
			<div class="slider-labels">
				<span>All Drugs</span>
				<span>Key Drugs</span>
				<span>+ Context</span>
			</div>
			<input
				type="range"
				min="0"
				max="2"
				step="1"
				bind:value={sliderValue}
				oninput={handleSliderChange}
				class="slider"
			/>
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

	.container {
		margin: 20px 40px;
		max-width: 860px;
		margin-left: auto;
		margin-right: auto;
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
		margin-bottom: 1rem;
	}

	.legend {
		display: flex;
		justify-content: center;
		gap: 2rem;
		margin-bottom: 1.5rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: fustat;
	}

	.legend-color {
		width: 30px;
		height: 4px;
		border-radius: 2px;
	}

	.chart-container {
		display: flex;
		justify-content: center;
		margin-bottom: 1.5rem;
	}

	.slider-container {
		max-width: 600px;
		margin: 0 auto;
		padding: 1rem 0;
	}

	.slider-labels {
		display: flex;
		justify-content: space-between;
		font-family: fustat;
		font-size: 0.9em;
		color: #666;
		margin-bottom: 0.5rem;
		padding: 0 10px;
	}

	.slider {
		width: 100%;
		height: 8px;
		border-radius: 5px;
		background: #d3d3d3;
		outline: none;
		-webkit-appearance: none;
		appearance: none;
	}

	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #2d6a4f;
		cursor: pointer;
	}

	.slider::-moz-range-thumb {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #2d6a4f;
		cursor: pointer;
		border: none;
	}

	:global(.x-axis text, .y-axis text) {
		font-family: fustat;
		font-size: 12px;
	}

	:global(.x-axis path, .y-axis path, .x-axis line, .y-axis line) {
		stroke: #666;
	}
</style>
