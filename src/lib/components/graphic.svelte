<script lang="ts">
	import * as d3 from 'd3';

	// Sample Viz, AI generated, we will of course replace this with something we wrote ourselves later.
	// This is just a placeholder.

	const data = [
		{ name: 'A', value: 30 },
		{ name: 'B', value: 80 },
		{ name: 'C', value: 45 },
		{ name: 'D', value: 60 },
		{ name: 'E', value: 20 },
		{ name: 'F', value: 90 }
	];

	// Reactive State
	let innerWidth = $state(0);
	let showLabels = $state(true);

	// Dimensions
	let width = $derived(innerWidth < 800 ? innerWidth - 40 : 600);
	let height = $derived(width * 0.67);
	let margin = $state({ top: 40, right: 30, bottom: 40, left: 50 });

	// Scales
	let xScale = $derived(
		d3
			.scaleBand()
			.domain(data.map((d) => d.name))
			.range([margin.left, width - margin.right])
			.padding(0.2)
	);

	let yScale = $derived(
		d3
			.scaleLinear()
			.domain([0, d3.max(data, (d) => d.value) || 100])
			.nice()
			.range([height - margin.bottom, margin.top])
	);

	let colorScale = $derived(
		d3
			.scaleSequential()
			.domain([0, data.length - 1])
			.interpolator(d3.interpolateViridis)
	);

	// Axes
	let xAxis = $derived(d3.axisBottom(xScale));
	let yAxis = $derived(d3.axisLeft(yScale));

	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;

	$effect(() => {
		if (xAxisRef) {
			d3.select(xAxisRef).call(xAxis);
		}
		if (yAxisRef) {
			d3.select(yAxisRef).call(yAxis);
		}
	});
</script>

<svelte:window bind:innerWidth />

<div class="flex flex-col items-center p-4">
	<h2 class="text-xl font-semibold">Generic Filler D3 Visualization</h2>

	<div class="gap-2">
		<label for="labels-toggle" class="text-sm font-medium"> Show Value Labels </label>
		<input
			id="labels-toggle"
			type="checkbox"
			bind:checked={showLabels}
			class="checkbox checkbox-sm checkbox-primary"
		/>
	</div>

	<svg {width} {height}>
		<!-- Bars - rendered directly in template -->
		<g>
			{#each data as item, i}
				<rect
					x={xScale(item.name)}
					y={yScale(item.value)}
					width={xScale.bandwidth()}
					height={height - margin.bottom - yScale(item.value)}
					fill={colorScale(i)}
					opacity="0.8"
					class="transition-opacity hover:opacity-100"
				/>

				{#if showLabels}
					<text
						x={(xScale(item.name) ?? 0) + xScale.bandwidth() / 2}
						y={yScale(item.value) - 5}
						text-anchor="middle"
						class="text-xs font-semibold"
						fill="currentColor"
					>
						{item.value}
					</text>
				{/if}
			{/each}
		</g>

		<!-- Axes - using refs and $effect -->
		<g class="x-axis" transform="translate(0, {height - margin.bottom})" bind:this={xAxisRef}></g>
		<g class="y-axis" transform="translate({margin.left}, 0)" bind:this={yAxisRef}></g>

		<!-- Title -->
		<text
			x={width / 2}
			y={height / 4}
			text-anchor="middle"
			transform="rotate(45, {width/2}, {height / 2})"
			class="text-fuchsia-600 font-bold"
			fill="currentColor"
		>
			Generic Bar Chart with Scales! Wow!
		</text>
	</svg>
</div>
