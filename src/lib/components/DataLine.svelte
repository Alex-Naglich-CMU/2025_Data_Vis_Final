<script lang="ts">
	import * as d3 from 'd3';
	import type { ScaleTime, ScaleLinear } from 'd3';
	import type { PricePoint, AveragePrice } from '$lib/scripts/drug-types';

	const {
		data = [],
		dataType,
		xScale,
		yScale
	} = $props<{
		data: PricePoint[] | AveragePrice[]; // Can be either type
		dataType: 'individual' | 'average';
		xScale: ScaleTime<number, number>;
		yScale: ScaleLinear<number, number>;
	}>();

	const lineGenerator = $derived(
		d3
			.line<any>() // Use 'any' here due to the mixed input types
			.curve(d3.curveStepAfter)
			.x((d) => xScale(d.date))
			.y((d) => yScale(dataType === 'average' ? d.averagePrice : d.price))
	);

	const pathD = $derived(data.length > 0 ? lineGenerator(data) : '');

	// Styling Placeholder
	const strokeColor = $derived(dataType === 'average' ? 'red' : '#888888');
	const strokeWidth = $derived(dataType === 'average' ? 3 : 1.5);
	const opacity = $derived(dataType === 'average' ? 1.0 : 0.3);
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
