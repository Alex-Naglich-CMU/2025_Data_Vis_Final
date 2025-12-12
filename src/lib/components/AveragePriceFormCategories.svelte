<!-- average price by form category bar chart -->

<script lang="ts">
	import * as d3 from 'd3';
	const categoryBars = [
		{ label: 'Injection', value: 52.79, count: 0 },
		{ label: 'Inhalation', value: 1.81, count: 0 },
		{ label: 'Delayed/Extended Release Oral Tablets', value: 1.17, count: 0 },
		{ label: 'Oral Capsule', value: 1.12, count: 0 },
		{ label: 'Oral Tablet', value: 0.94, count: 0 },
		{ label: 'Topical', value: 0.81, count: 0 },
		{ label: 'Delayed/Extended Release Oral Capsules', value: 0.41, count: 0 }
	].sort((a, b) => b.value - a.value); // sort by price (highest to lowest)

	// layout constants
	let containerWidth = $state(0);
	const chartWidth = $derived(containerWidth || 900);
	const chartHeight = $derived(chartWidth * 0.65);
	const margin = { top: 8, right: 10, bottom: 80, left: 60 };

	// chart scales
	function createScales(data: any[], width: number, height: number) {
		const xScale = d3
			.scaleBand()
			.range([margin.left, width - margin.right])
			.domain(data.map((d) => d.label))
			.padding(0.2);

		const yScale = d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(data, (d) => d.value * 1.1) ?? 1])
			.nice();

		return { xScale, yScale };
	}

	const scales = $derived(createScales(categoryBars, chartWidth, chartHeight));
	const xScale = $derived(scales.xScale);
	const yScale = $derived(scales.yScale);

	// svg refs
	let xAxisRef = $state<SVGGElement>();
	let yAxisRef = $state<SVGGElement>();

	// render axes
	$effect(() => {
		if (xAxisRef && categoryBars.length > 0) {
			d3.select(xAxisRef).call(d3.axisBottom(xScale));

			// Wrap long labels to multiple lines
			d3.select(xAxisRef)
				.selectAll('.tick text')
				.each(function () {
					const text = d3.select(this);
					const words = (text.text() as string).split(/\s+/);
					const lineHeight = 1.1;
					const y = text.attr('y');
					const dy = parseFloat(text.attr('dy') || '0');
					const maxWidth = xScale.bandwidth();

					text.text(null);

					let line: string[] = [];
					let lineNumber = 0;
					let tspan = text
						.append('tspan')
						.attr('x', 0)
						.attr('y', y)
						.attr('dy', dy + 'em');

					for (const word of words) {
						line.push(word);
						tspan.text(line.join(' '));

						const node = tspan.node();
						if (node) {
							const textLength = node.getComputedTextLength();

							if (textLength > maxWidth && line.length > 1) {
								line.pop();
								tspan.text(line.join(' '));
								line = [word];
								lineNumber++;
								tspan = text
									.append('tspan')
									.attr('x', 0)
									.attr('y', y)
									.attr('dy', lineNumber * lineHeight + dy + 'em')
									.text(word);
							}
						}
					}
				});
		}
		if (yAxisRef && categoryBars.length > 0) {
			d3.select(yAxisRef).call(d3.axisLeft(yScale).tickFormat((d) => `$${d}`));
		}
	});
</script>

<div class="chart-container">
	<div class="width-tracker" bind:clientWidth={containerWidth}>
		<svg width={chartWidth} height={chartHeight} role="img">
			<g>
				{#each categoryBars as bar}
					{@const x = xScale(bar.label) ?? 0}
					{@const y = yScale(bar.value)}
					{@const barWidth = xScale.bandwidth()}
					{@const barHeight = chartHeight - margin.bottom - y}

					<rect
						{x}
						{y}
						width={barWidth}
						height={barHeight}
						fill="#355B75"
						opacity={bar === categoryBars[0] ? 1 : 0.8}
					/>
					<text x={x + barWidth / 2} y={y - 5} text-anchor="middle" class="bar-label">
						${bar.value.toFixed(2)}
					</text>
				{/each}
			</g>

			<g
				class="x-axis"
				transform="translate(0,{chartHeight - margin.bottom})"
				bind:this={xAxisRef}
			></g>
			<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

			<!-- Y-axis label -->
			<text
				transform="rotate(-90)"
				x={-(chartHeight / 2) + 30}
				y={15}
				text-anchor="middle"
				class="axis-label"
			>
				Average Price Per Dose
			</text>

			<!-- X-axis label -->
			<text x={chartWidth / 2} y={chartHeight - 10} text-anchor="middle" class="axis-label">
				Dosage Form Category
			</text>
		</svg>
	</div>
</div>

<style>
	* {
		font-family: Antonio;
	}

	/* 
	.width-tracker {
		border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		padding: 2rem;
		user-select: none;
		-webkit-user-select: none;
	} */

	svg {
		display: block;
	}

	.bar-label {
		font-family: fustat;
		font-size: 0.85em;
		font-weight: 600;
		fill: #355b75;
	}

	.axis-label {
		font-family: fustat;
		font-size: 0.9em;
		font-weight: 400;
	}

	:global(.x-axis text) {
		font-family: Antonio;
		font-size: 0.9em;
	}

	:global(.y-axis text) {
		font-family: Antonio;
	}
</style>