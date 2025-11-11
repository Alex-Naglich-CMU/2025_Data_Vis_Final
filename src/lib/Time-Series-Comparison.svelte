<script lang="ts">
	import * as d3 from 'd3';

	// TYPE DEFINITIONS
	interface DrugData {
		searchName: string;
		RxCUI: string;
		Name: string;
		IsBrand: boolean;
		Brand_RxCUI: string | null;
		Generic_RxCUI: string | null;
		prices: {
			[ndc: string]: {
				[date: string]: number;
			};
		};
	}

	interface PricePoint {
		date: Date;
		price: number;
	}

	// PROPS
	const { drugsData = [] }: { drugsData: DrugData[] } = $props();

	// STATE VARIABLES
	let selectedDrugIndex = $state<number>(0);

	// CONSTANTS AND CONFIGURATION
	// chart Dimensions
	const width = $state(800);
	const height = $state(400);
	let margin = $state({ top: 40, right: 40, bottom: 80, left: 80 });

	// DERIVED DATA
	let selectedDrug = $derived(drugsData[selectedDrugIndex]);

	// helper function to get average prices for a drug
	function getAveragePrices(drug: DrugData): PricePoint[] {
		if (!drug || !drug.prices) return [];

		const dateMap: { [date: string]: number[] } = {};

		for (const dates of Object.values(drug.prices)) {
			for (const [date, price] of Object.entries(dates)) {
				if (!dateMap[date]) {
					dateMap[date] = [];
				}
				dateMap[date].push(price);
			}
		}

		const averages: PricePoint[] = Object.entries(dateMap).map(([date, prices]) => ({
			date: new Date(date),
			price: prices.reduce((sum, p) => sum + p, 0) / prices.length
		}));

		averages.sort((a, b) => a.date.getTime() - b.date.getTime());
		return averages;
	}

	const priceData = $derived(selectedDrug ? getAveragePrices(selectedDrug) : []);

	// SCALES
	let xScale = $derived(
		d3
			.scaleTime()
			.range([margin.left, width - margin.right])
			.domain(d3.extent(priceData, (d) => d.date) as [Date, Date])
	);

	let yScale = $derived(
		d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(priceData, (d) => d.price) ?? 100])
			.nice()
	);

	// AXES
	let xAxis = $derived(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%b %Y') as any));
	let yAxis = $derived(d3.axisLeft(yScale).tickFormat((d) => `$${d}`));

	let xAxisRef: SVGGElement;
	let yAxisRef: SVGGElement;

	// render axes when data loads
	$effect(() => {
		if (xAxisRef && drugsData.length > 0) {
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
		if (yAxisRef && drugsData.length > 0) {
			d3.select(yAxisRef).call(yAxis);
		}
	});
</script>

<!-- CONTROLS -->
<div class="controls">
	<select bind:value={selectedDrugIndex}>
		{#each drugsData as drug, i}
			<option value={i}>
				{drug.Name} ({drug.IsBrand ? 'Brand' : 'Generic'})
			</option>
		{/each}
	</select>

	<br />

	{#if selectedDrug}
		<!-- svelte-ignore a11y_label_has_associated_control -->
		<label>
			Selected: {selectedDrug.Name}
		</label>
		<br />
		<!-- svelte-ignore a11y_label_has_associated_control -->
		<label>
			Data Points: {priceData.length}
		</label>
	{/if}
</div>

<br />

<div class="chart-wrapper">
	<svg {width} {height}>
		<!-- Axes -->
		<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}></g>
		<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

		<!-- Axis Labels -->
		<text
			class="axis-label"
			text-anchor="middle"
			x={width / 2}
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
	</svg>
</div>

