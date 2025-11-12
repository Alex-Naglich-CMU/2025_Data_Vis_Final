<script lang="ts">
	import * as d3 from 'd3';
	import type { PricePoint, AveragePrice } from '$lib/scripts/drug-types';
	import { getAveragePrices } from '$lib/scripts/helper-functions';
	import DataLine from '$lib/components/DataLine.svelte';

	// PROPS
	const { priceData = [] }: { priceData: PricePoint[] } = $props();
	const averageData: AveragePrice[] = $derived(getAveragePrices(priceData || []));

	// Prepare data with Date objects for D3
	const individualPlottable = $derived(priceData.map((d) => ({ ...d, date: new Date(d.date) })));
	const averagePlottable = $derived(averageData.map((d) => ({ ...d, date: new Date(d.date) })));

	// CONSTANTS AND CONFIGURATION
	// chart Dimensions
	let containerWidth = $state(0);
	const height = $derived(containerWidth * 0.6);
	let margin = $state({ top: 40, right: 40, bottom: 80, left: 80 });

	// SCALES
	let xScale = $derived(
		d3
			.scaleTime()
			.range([margin.left, containerWidth - margin.right])
			.domain(d3.extent(individualPlottable, (d) => d.date) as [Date, Date])
	);

	let yScale = $derived(
		d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(individualPlottable, (d) => d.price) ?? 100])
			.nice()
	);

	// AXES
	let xAxis = $derived(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%b %Y') as any));
	let yAxis = $derived(d3.axisLeft(yScale).tickFormat((d) => `$${d}`));

	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;

	// render axes when data loads
	$effect(() => {
		if (xAxisRef && individualPlottable.length > 0) {
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
		if (yAxisRef && individualPlottable.length > 0) {
			d3.select(yAxisRef).call(yAxis);
		}
	});
</script>

<!-- CONTROLS -->
<!-- <div class="controls">
	<select bind:value={selectedDrugIndex}>
		{#each drugsData as drug, i}
			<option value={i}>
				{drug.Name} ({drug.IsBrand ? 'Brand' : 'Generic'})
			</option>
		{/each}
	</select>

	<br />

	{#if selectedDrug}
		<label>
			Selected: {selectedDrug.Name}
		</label>
		<br />
		<label>
			Data Points: {priceData.length}
		</label>
	{/if}
</div> -->

<div class="chart-wrapper" bind:clientWidth={containerWidth}>
	<svg width={containerWidth} {height}>
		<!-- Axes -->
		<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}></g>
		<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

		<!-- Axis Labels -->
		<text
			class="axis-label"
			text-anchor="middle"
			x={containerWidth / 2}
			y={height - 10}
			font-family="fustat, sans-serif"
			font-size="14px"
			font-weight="600"
		>
			Date
		</text>

		<text
			class="axis-label"
			text-anchor="middle"
			transform="rotate(-90)"
			x={-height / 2}
			y={20}
			font-family="fustat, sans-serif"
			font-size="14px"
			font-weight="600"
		>
			Price Per Pill (USD)
		</text>

		<!-- Individual Drug Price Lines -->
		{#each d3.groups(individualPlottable, (d) => d.ndc) as [ndc, pricesForNdc] (ndc)}
			<DataLine data={pricesForNdc} dataType="individual" {xScale} {yScale} />
		{/each}

		<!-- Average Drug Price Line -->
		<DataLine data={averagePlottable} dataType="average" {xScale} {yScale} />
	</svg>
</div>
