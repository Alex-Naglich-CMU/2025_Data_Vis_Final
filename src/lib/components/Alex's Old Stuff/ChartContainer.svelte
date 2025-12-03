<script lang="ts">
	import * as d3 from 'd3';
	import type { PricePoint, AveragePrice, PlottablePricePoint , PlottableAveragePrice } from '$lib/scripts/drug-types';
	import { getAvAverageGenericPrice} from '$lib/scripts/helper-functions';
	import DataLine from '$lib/components/DataLine.svelte';

	// PROPS
	const { plottableData }: { plottableData: PricePoint[] } = $props();

	const rawGenericPrices: PricePoint[] = $derived(plottableData.filter((d) => d && !d.isBrand));

	const rawBrandPrices: PricePoint[] = $derived(plottableData.filter((d) => d && d.isBrand));

	const averageData: AveragePrice[] = $derived(getAveragePrices(rawGenericPrices));

	const genericPlottable: PlottablePricePoint[] = $derived(
		rawGenericPrices.map((d) => ({ ...d, date: new Date(d.date) })) as PlottablePricePoint[]
	);AverageGenericPriceandPlottable: PlottablePricePoint[] = $derived(
		rawBrandPrices.map((d) => ({ ...d, date: new Date(d.date) })) as PlottablePricePoint[]
	);

	const averagePlottable = $derived(
		averageData.map((d) => ({
			...d,
			date: new Date(d.date)
		}))
	);
	// CONSTANTS AND CONFIGURATION

	const colors : object = {
		red: '#9A2F1F',
		blue: '#54707C',
		orange: '#DF7C39',
		tan: '#BFA97F',
		cream: '#F6F5EC'
	}

	// chart Dimensions
	let containerWidth = $state(0);
	const height = $derived(containerWidth * 0.6);
	let margin = $state({ top: 40, right: 40, bottom: 80, left: 80 });

	// SCALES
	let xScale = $derived(
		d3
			.scaleTime()
			.range([margin.left, containerWidth - margin.right])
			.domain(d3.extent(genericPlottable, (d) => d.date) as [Date, Date])
	);

	let yScale = $derived(
		d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(genericPlottable, (d) => d.price) ?? 100])
			.nice()
	);

	// AXES
	let xAxis = $derived(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%b %Y') as any));
	let yAxis = $derived(d3.axisLeft(yScale).tickFormat((d) => `$${d}`));

	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;

	// render axes when data loads
	$effect(() => {
		if (xAxisRef && genericPlottable.length > 0) {
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
		if (yAxisRef && genericPlottable.length > 0) {
			d3.select(yAxisRef).call(yAxis);
		}
	});
</script>

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

		<!-- Data Lines -->
		{#each d3.groups(genericPlottable, (d) => d.ndc) as [ndc, pricesForNdc] (ndc)}
			<DataLine data={pricesForNdc} dataType="generic" {xScale} {yScale} />
		{/each}

		{#each d3.groups(brandPlottable, (d) => d.ndc) as [ndc, pricesForNdc] (ndc)}
			<DataLine data={pricesForNdc} dataType="brand" {xScale} {yScale} />
		{/each}

		{#if averagePlottable.length > 0}
			<DataLine data={averagePlottable} dataType="mean" {xScale} {yScale} />
		{/if}
	</svg>
</div>
