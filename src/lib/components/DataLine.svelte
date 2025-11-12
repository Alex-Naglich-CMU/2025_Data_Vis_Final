<script lang="ts">
	import * as d3 from 'd3';
	import type { ScaleTime, ScaleLinear } from 'd3';
	import type { PlottableAveragePrice, PlottablePricePoint } from '$lib/scripts/drug-types';

	const {
		data = [],
		dataType,
		xScale,
		yScale
	} = $props<{
		data: PlottablePricePoint[] | PlottableAveragePrice[]; // Can be either type
		dataType: 'generic' | 'mean' | 'brand';
		xScale: ScaleTime<number, number>;
		yScale: ScaleLinear<number, number>;
	}>();

	const lineGenerator = $derived(
		d3
			.line<any>() // Use 'any' here due to the mixed input types
			.curve(d3.curveStepAfter)
			.x((d) => xScale(d.date))
			.y((d) => yScale(dataType === 'mean' ? d.averagePrice : d.price))
	);

	const pathD = $derived(data.length > 0 ? lineGenerator(data) : '');

	// Styling Placeholder
	const strokeColor = $derived(
		dataType === 'mean' ? 'red' : dataType === 'brand' ? 'blue' : 'green'
	);
	const strokeWidth = $derived(dataType === 'mean' ? 3 : dataType === 'brand' ? 5 : 2);
	const opacity = $derived(dataType === 'mean' ? 1.0 : dataType === 'brand' ? 0.7 : 0.5);
</script>

{#if pathD}
	<path
		d={pathD}
		stroke={strokeColor}
		stroke-width={strokeWidth}
		fill="none"
		{opacity}
		class={dataType}
	/>
{/if}
