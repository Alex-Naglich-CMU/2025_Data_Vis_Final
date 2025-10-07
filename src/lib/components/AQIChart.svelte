<script lang="ts">
	import * as d3 from 'd3';
	import qualityLevels from '$lib/a3/qualityLevels.json';

	interface Item {
		city: string;
		country: string;
		mainPollutant: string;
		pm25: number;
		state: string;
		stationName: string;
		timestamp: Date;
		usAqi: number;
	}

	interface MonthlyStat {
		dateRange: [Date, Date];
		averageAqi: number;
		percentile10: number;
		percentile90: number;
	}

	let innerWidth = $state(0);

	const { data }: { data: Item[] } = $props();

	//	let width = $derived(innerWidth < 800 ? innerWidth - 20 : 800);
	let width = $state(800);
	let height = $derived(width * 0.6);
	let margin = $state({ top: 80, right: 20, bottom: 20, left: 40 });
	let showRaw = $state(false);

	let xScale = $derived(
		d3
			.scaleTime()
			.domain([
				d3.min(data, (d) => d.timestamp) ?? new Date(),
				d3.max(data, (d) => d.timestamp) ?? new Date()
			])
			.range([margin.left, width - margin.right])
	);

	let yScale = $derived(
		d3
			.scaleLinear()
			.domain([0, d3.max(data, (d) => d.usAqi) ?? 500])
			.range([height - margin.bottom, margin.top])
	);

	let xAxis = $derived(d3.axisBottom(xScale));
	let yAxis = $derived(d3.axisLeft(yScale));
	let yAxisGrid = $derived(
		d3
			.axisLeft(yScale)
			.tickSize(-(width - margin.left - margin.right))
			.tickFormat(null)
	);

	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;
	let yAxisGridRef: SVGGElement;

	$effect(() => {
		if (xAxisRef && data.length > 0) {
			d3.select(xAxisRef).call(xAxis);
		}
		if (yAxisRef && data.length > 0) {
			d3.select(yAxisRef).call(yAxis);
		}
		if (yAxisGridRef && data.length > 0) {
			d3.select(yAxisGridRef).call(yAxisGrid);
		}
	});

	let monthlyBin = $derived(
		d3
			.bin<Item, Date>()
			.value((d) => d.timestamp)
			.thresholds(
				d3.utcMonth.range(
					d3.min(data, (d) => d.timestamp) ?? new Date(),
					d3.max(data, (d) => d.timestamp) ?? new Date()
				)
			)(data)
	);

	let monthlyStats = $derived(
		monthlyBin.map((bin) => {
			return {
				// @ts-ignore
				dateRange: [bin.x0, bin.x1],
				averageAqi: d3.mean(bin, (d) => d.usAqi) ?? 0,
				percentile10: d3.quantile(bin.map((d) => d.usAqi).sort(d3.ascending), 0.1) ?? 0,
				percentile90: d3.quantile(bin.map((d) => d.usAqi).sort(d3.ascending), 0.9) ?? 0
			};
		}) as MonthlyStat[]
	);

	let averageLine = $derived(
		d3
			.line<MonthlyStat>()
			.x((d) => {
				const midpointTime = (d.dateRange[0].getTime() + d.dateRange[1].getTime()) / 2;
				return xScale(new Date(midpointTime));
			})
			.y((d) => yScale(d.averageAqi))
			.curve(d3.curveMonotoneX)(monthlyStats)
	);

	let percentileArea = $derived(
		d3
			.area<MonthlyStat>()
			.x((d) => {
				const midpointTime = (d.dateRange[0].getTime() + d.dateRange[1].getTime()) / 2;
				return xScale(new Date(midpointTime));
			})
			.y0((d) => yScale(d.percentile10))
			.y1((d) => yScale(d.percentile90))
			.curve(d3.curveMonotoneX)(monthlyStats)
	);
</script>

<svelte:window bind:innerWidth />

<div class="flex items-center gap-2">
	<label for="raw-data-toggle" class="text-xl font-semibold"> Show Raw Data </label>

	<input
		id="raw-data-toggle"
		type="checkbox"
		bind:checked={showRaw}
		class="checkbox checkbox-primary"
	/>
</div>

<div class="mb-4 text-xl font-semibold">Number of Records: {data.length}</div>

<div class="mb-4 flex gap-4 text-xs">
	{#each qualityLevels as level}
		<div
			class="flex w-40 items-center justify-between gap-1 rounded-2xl p-2 text-black"
			style="background-color: {level.color};"
		>
			<div class="flex-wrap text-center">{level.name}</div>
			<div class="whitespace-nowrap">({level.min} - {level.max ?? '∞'})</div>
		</div>
	{/each}
</div>

<svg {width} {height}>
	<g>
		{#each qualityLevels as level}
			{#if yScale(level.min) > margin.top}
				<rect
					x={margin.left}
					width={width - margin.left - margin.right}
					y={yScale(level.max ?? 500) > margin.top ? yScale(level.max ?? 500) : margin.top}
					height={yScale(level.max ?? 500) > margin.top
						? yScale(level.min - 1) - yScale(level.max ?? 500)
						: yScale(level.min - 1) - margin.top}
					fill={level.color}
					opacity=".7"
				/>
			{/if}
		{/each}
	</g>

	{#if showRaw}
		<g>
			{#each data as item}
				<circle
					cx={xScale(item.timestamp)}
					cy={yScale(item.usAqi)}
					r="1.5"
					fill="blue"
					opacity="0.7"
				/>
			{/each}
		</g>
	{/if}
	<path d={averageLine} fill="none" stroke="black" stroke-width="1.5" />
	<path d={percentileArea} fill="black" opacity="0.1" />

	<g class="x-axis" transform="translate(0, {height - margin.bottom})" bind:this={xAxisRef}></g>
	<g class="y-axis" transform="translate({margin.left}, 0)" bind:this={yAxisRef}></g>
	<g
		class="y-axis-grid"
		transform="translate({margin.left}, 0)"
		bind:this={yAxisGridRef}
		style="color:black; opacity:0.2;"
	></g>
</svg>
