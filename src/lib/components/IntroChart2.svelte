<!-- pie chart: % of drugs that increased/decreased/stayed same -->

<script lang="ts">
	import * as d3 from 'd3';
	import type { PriceChange } from '$lib/scripts/types';
	import introChartData from '$lib/scripts/introChartData';

	const width = 400;
	const height = 400;
	const radius = Math.min(width, height) / 2 - 40;
	const loading = false;
	const error: string | null = null;

	let viewMode: 'count' | 'dollars' = 'dollars';

	function getPriceChanges(mode: 'count' | 'dollars'): PriceChange[] {
		if (mode === 'count') {
			return [
				{
					category: 'Increased',
					count: introChartData.increased,
					percentage: Number(introChartData.increasedPct),
					color: '#9a2f1f'
				},
				{
					category: 'Decreased',
					count: introChartData.decreased,
					percentage: Number(introChartData.decreasedPct),
					color: '#355B75'
				},
				{
					category: 'Stayed the Same',
					count: introChartData.stayedSame,
					percentage: Number(introChartData.stayedSamePct),
					color: '#616161'
				}
			];
		} else {
			return [
				{
					category: 'Increased',
					count: introChartData.increasedDollars,
					percentage: Number(introChartData.increasedDollarsPct),
					color: '#9a2f1f'
				},
				{
					category: 'Decreased',
					count: introChartData.decreasedDollars,
					percentage: Number(introChartData.decreasedDollarsPct),
					color: '#355B75'
				},
				{
					category: 'Stayed the Same',
					count: introChartData.stayedSameDollars,
					percentage: Number(introChartData.stayedSameDollarsPct),
					color: '#616161'
				}
			];
		}
	}

	$: priceChanges = getPriceChanges(viewMode);
	$: arcs = pie(priceChanges);

	function toggleViewMode() {
		viewMode = viewMode === 'count' ? 'dollars' : 'count';
	}

	const pie = d3.pie<PriceChange>().value((d) => d.count);
	const arc = d3.arc<d3.PieArcDatum<PriceChange>>().innerRadius(0).outerRadius(radius);
	const labelArc = d3
		.arc<d3.PieArcDatum<PriceChange>>()
		.innerRadius(radius * 0.6)
		.outerRadius(radius * 0.6);
</script>

{#if loading}
	<div class="loading">
		<p>Analyzing drug price changes...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="chart-container">
		<div class="chart-wrapper">
			<svg {width} {height}>
				<g transform="translate({width / 2}, {height / 2})">
					{#each arcs as arcData}
						{@const pathData = arc(arcData)}
						{@const labelPos = labelArc.centroid(arcData)}

						<!-- pie slice -->
						<path d={pathData} fill={arcData.data.color} stroke="#fcfbf5" stroke-width="1.5" />

						<!-- label -->
						<text
							x={labelPos[0]}
							y={labelPos[1]}
							text-anchor="middle"
							class="slice-label"
							fill="#fcfbf5"
							font-weight="bold"
						>
							{arcData.data.percentage.toFixed(1)}%
						</text>
					{/each}
				</g>
			</svg>

			<!-- legend -->
			<div class="legend">
				{#if viewMode === 'count'}
					<h4>Between 2017 and 2025 ...</h4>
					{#each priceChanges as change}
						<div class="legend-item">
							<!-- <div class="legend-color" style="background-color: {change.color}"></div> -->
							<div class="legend-text">
								<h4 style="color: {change.color}">{change.percentage.toFixed(1)}%</h4>
								<h6 class="category">of drug prices <b>{change.category}</b></h6>
							</div>
						</div>
					{/each}
					<h6 class="hook">But is that the whole story?</h6>
				{:else}
					<div class="price-hook">
						<!-- <h4>The amount the price changed by:</h4> -->
					</div>
					{#each priceChanges as change}
						<div class="legend-item">
							<!-- <div class="legend-color" style="background-color: {change.color}"></div> -->
							<div class="legend-text">
								<h6>Combined Cost <b>{change.category}</b> by</h6>
								<h4 class="category" style="color: {change.color}">${change.count.toFixed(2)}</h4>
							</div>
						</div>
					{/each}
					<h6 class="price-hook hook">
						The total cost of drugs whose prices went up increased by <b>10x</b> more than the cost of
						the drugs whose prices went down decreased.
					</h6>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	* {
		font-family: Antonio;
	}

	h1 {
		font-size: 5em;
		font-weight: bold;
	}

	h2 {
		font-size: 2.5em;
		font-weight: bold;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
	}

	h4 {
		font-family: fustat;
		font-size: 1.3em;
		font-weight: 700;
	}

	h5 {
		font-family: fustat;
		font-size: 1em;
		font-weight: normal;
		text-transform: uppercase;
	}

	h6 {
		font-family: fustat;
		font-size: 1em;
		font-weight: 600;
		text-transform: uppercase;
	}

	h6 b {
		font-family: fustat;
		font-size: 1em;
		font-weight: 800;
		text-transform: uppercase;
	}

	p {
		font-family: fustat;
		font-size: 1.1em;
		font-weight: normal;
	}

	p a {
		font-family: fustat;
		font-weight: normal;
		color: inherit;
		text-decoration: underline;
	}

	p b {
		font-family: fustat;
		font-size: 1.1em;
		font-weight: bold;
	}

	.loading,
	.error {
		padding: 2em;
		text-align: center;
		font-family: fustat;
	}

	.error {
		color: #9a2f1f;
	}

	.chart-container {
		margin: 20px 10px;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
		margin-bottom: 0.5em;
		text-align: center;
	}

	.subtitle {
		font-family: fustat;
		text-align: center;
		color: #666;
		margin-bottom: 2em;
	}

	.chart-wrapper {
		display: flex;
		justify-content: start;
		align-items: center;
		gap: 1em;
	}

	svg {
		display: block;
	}

	.slice-label {
		font-family: fustat;
		font-size: 0.9em;
		pointer-events: none;
		padding: 0;
		margin: 0;
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 1em;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 1em;
	}

	/* .legend-color {
		width: 25px;
		height: 25px;
		border-radius: 4px;
		flex-shrink: 0;
	} */

	.legend-text {
		font-family: fustat;
		font-size: 1em;
		display: flex;
		align-items: center;
	}

	.legend-text strong {
		font-size: 1.1em;
	}

	.category {
		margin-left: 1em;
	}

	.hook {
		font-style: italic;
		font-weight: 400;
		text-transform: none;
	}
	.hook b {
		font-style: italic;
		font-weight: 700;
		text-transform: none;
	}

	.price-hook {
		max-width: 400px;
	}

	.toggle-container {
		display: flex;
		justify-content: center;
		gap: 0;
		margin-bottom: 2em;
	}

	.toggle-button {
		padding: 0.4em 1em;
		font-size: 0.9em;
		font-family: Fustat;
		background-color: #f6f5ec;
		color: #000000;
		border: 1px solid #ccc;
		cursor: pointer;
		transition: all 0.2s;
	}

	.left-button {
		min-width: 160px;
		border-radius: 20px 0 0 20px;
		border-right: 1px solid #ccc;
	}

	.right-button {
		min-width: 160px;
		border-radius: 0 20px 20px 0;
		border-left: 1px solid #ccc;
	}

	.toggle-button:hover:not(.active) {
		background-color: #dcdbd5;
	}

	.toggle-button.active {
		background-color: #656565;
		color: white;
		border-color: #3f5339;
	}
</style>
