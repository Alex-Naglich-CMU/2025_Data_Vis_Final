<!-- price per mg form file
shows the most cost-effective dosage strength and form for a selected drug
by calculating price per MG and displaying as sorted bar charts
-->

<script lang="ts">
	import * as d3 from 'd3';
	import { onMount } from 'svelte';

	// props and state stuff
	const brandDrugs = [
		// { name: 'GLUCOPHAGE', manufacturer: 'glucophage' },
		{ name: 'LAMICTAL', manufacturer: 'lamictal' },
		{ name: 'LANTUS', manufacturer: 'lantus' },
		{ name: 'LEXAPRO', manufacturer: 'lexapro' },
		{ name: 'LIPITOR', manufacturer: 'lipitor' },
		{ name: 'LYRICA', manufacturer: 'lyrica' },
		{ name: 'NEURONTIN', manufacturer: 'neurontin' },
		{ name: 'NORVASC', manufacturer: 'norvasc' },
		{ name: 'PROVIGIL', manufacturer: 'provigil' },
		{ name: 'PROZAC', manufacturer: 'prozac' },
		{ name: 'SYNTHROID', manufacturer: 'synthroid' },
		{ name: 'VYVANSE', manufacturer: 'vyvanse' },
		{ name: 'ZOLOFT', manufacturer: 'zoloft' }
	];

	interface DrugVariation {
		rxcui: string;
		name: string;
		strengthValue: number; // numeric value extracted from strength
		strengthLabel: string; // display label (e.g 20 MG)
		form: string;
		mostRecentPrice: number;
		pricePerUnit: number;
	}

	interface Props {
		selectedDrugIndex: number;
	}

	let { selectedDrugIndex = 8 }: Props = $props();

	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchIndex = $state<any>({});
	let drugVariations = $state<DrugVariation[]>([]);

	// layout constants for the charts
	let containerWidth = $state(0);
	const chartWidth = $derived(containerWidth * 0.48 || 410);
	const chartHeight = $derived(chartWidth * 0.8);
	const margin = { top: 10, right: 8, bottom: 30, left: 40 };

	// data loading on mount
	onMount(async () => {
		try {
			const searchIndexModule = await import('$lib/data/search_index_all.json');
			searchIndex = searchIndexModule.default;
			console.log('search index loaded:', Object.keys(searchIndex).length, 'entries');
			loading = false;
			await loadDrugData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('error loading search index:', err);
		}
	});

	// load data for selected drug
	async function loadDrugData() {
		loading = true;
		error = null;
		drugVariations = [];

		try {
			const selectedDrug = brandDrugs[selectedDrugIndex];
			console.log('loading data for:', selectedDrug.name);
			const variations: DrugVariation[] = [];

			// find all RxCUIs for this drug
			for (const [rxcui, data] of Object.entries(searchIndex)) {
				const drugData = data as any;
				if (
					drugData.manufacturer_name &&
					drugData.manufacturer_name.toLowerCase().includes(selectedDrug.manufacturer) &&
					drugData.is_brand === true
				) {
					try {
						const priceResponse = await import(`$lib/data/prices/${rxcui}.json`);
						const priceData = priceResponse.default;

						// extract strength value and label from Strength field
						const strengthValue = extractStrengthValue(priceData.Strength);
						const strengthLabel = priceData.Strength || '';
						const form = priceData.Form || '';

						// only include if we have valid data
						if (strengthValue && strengthLabel && form) {
							const mostRecentPrice = getMostRecentPrice(priceData.prices);

							if (mostRecentPrice !== null) {
								const pricePerUnit = mostRecentPrice / strengthValue;

								variations.push({
									rxcui,
									name: drugData.name,
									strengthValue,
									strengthLabel,
									form,
									mostRecentPrice,
									pricePerUnit
								});

								console.log(
									`found ${strengthLabel} ${form}: $${mostRecentPrice.toFixed(2)} = $${pricePerUnit.toFixed(2)}/MG`
								);
							}
						}
					} catch (e) {
						console.warn(`no price data for ${rxcui}`);
					}
				}
			}

			drugVariations = variations;
			console.log('total variations loaded:', variations.length);
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error loading drug data';
			loading = false;
			console.error('error loading drug data:', err);
		}
	}

	// extract numeric value from strength string (e.g., "20 MG" -> 20)
	function extractStrengthValue(strengthStr: string): number {
		if (!strengthStr) return 0;
		const match = strengthStr.match(/(\d+\.?\d*)/);
		return match ? parseFloat(match[1]) : 0;
	}

	// get most recent price from price data
	function getMostRecentPrice(pricesObj: any): number | null {
		let mostRecentDate: Date | null = null;
		let mostRecentPrice: number | null = null;

		// find the most recent date across all NDCs
		for (const ndc in pricesObj) {
			for (const [dateStr, price] of Object.entries(pricesObj[ndc])) {
				const date = parseDate(dateStr);
				if (date && (mostRecentDate === null || date > mostRecentDate)) {
					mostRecentDate = date;
					mostRecentPrice = price as number;
				}
			}
		}

		return mostRecentPrice;
	}

	// parse date string
	function parseDate(dateStr: string): Date | null {
		try {
			const parts = dateStr.split('/');
			if (parts.length === 3) {
				const month = parseInt(parts[0]) - 1;
				const day = parseInt(parts[1]);
				const year = parseInt(parts[2]);
				return new Date(year, month, day);
			}
		} catch (e) {
			console.warn('Failed to parse date:', dateStr);
		}
		return null;
	}

	// group and calculate average price per mg by strength
	const strengthBars = $derived.by(() => {
		const strengthMap = new Map<string, { total: number; count: number; strengthValue: number }>();

		for (const variation of drugVariations) {
			const key = variation.strengthLabel;
			if (!strengthMap.has(key)) {
				strengthMap.set(key, { total: 0, count: 0, strengthValue: variation.strengthValue });
			}
			const entry = strengthMap.get(key)!;
			entry.total += variation.pricePerUnit;
			entry.count += 1;
		}

		const bars = Array.from(strengthMap.entries()).map(([label, data]) => ({
			label,
			value: Math.round((data.total / data.count) * 100) / 100,
			strengthValue: data.strengthValue
		}));

		// sort by strengthValue (numeric) for proper ordering
		return bars.sort((a, b) => b.value - a.value);
	});

	// group and calculate average price per mg by form
	const formBars = $derived.by(() => {
		const formMap = new Map<string, { total: number; count: number }>();

		for (const variation of drugVariations) {
			const key = variation.form;
			if (!formMap.has(key)) {
				formMap.set(key, { total: 0, count: 0 });
			}
			const entry = formMap.get(key)!;
			entry.total += variation.pricePerUnit;
			entry.count += 1;
		}

		const bars = Array.from(formMap.entries()).map(([label, data]) => ({
			label,
			value: data.total / data.count
		}));

		/// sort alphabetically for easier side-by-side comparison
		return bars.sort((a, b) => a.label.localeCompare(b.label));
	});

	// find cheapest options
	const cheapestStrength = $derived(
		strengthBars.length > 0
			? strengthBars.reduce((min, bar) => (bar.value < min.value ? bar : min))
			: null
	);
	const cheapestForm = $derived(
		formBars.length > 0 ? formBars.reduce((min, bar) => (bar.value < min.value ? bar : min)) : null
	);

	// chart scales
	function createStrengthScales(data: any[], width: number, height: number) {
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

	function createFormScales(data: any[], width: number, height: number) {
		const xScale = d3
			.scaleBand()
			.range([margin.left, width - margin.right])
			.domain(data.map((d) => d.label))
			.padding(0.3);

		const yScale = d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, d3.max(data, (d) => d.value * 1.1) ?? 1])
			.nice();

		return { xScale, yScale };
	}

	const strengthScales = $derived(createStrengthScales(strengthBars, chartWidth, chartHeight));
	const formScales = $derived(createFormScales(formBars, chartWidth, chartHeight));

	// svg refs
	let strengthXAxisRef = $state<SVGGElement>();
	let strengthYAxisRef = $state<SVGGElement>();
	let formXAxisRef = $state<SVGGElement>();
	let formYAxisRef = $state<SVGGElement>();

	// effects - axes rendering
	$effect(() => {
		if (strengthXAxisRef && strengthBars.length > 0) {
			d3.select(strengthXAxisRef).call(d3.axisBottom(strengthScales.xScale));
		}
		if (strengthYAxisRef && strengthBars.length > 0) {
			d3.select(strengthYAxisRef).call(
				d3.axisLeft(strengthScales.yScale).tickFormat((d) => `$${Number(d).toFixed(2)}`)
			);
		}
		if (formXAxisRef && formBars.length > 0) {
			d3.select(formXAxisRef).call(d3.axisBottom(formScales.xScale));
		}
		if (formYAxisRef && formBars.length > 0) {
			d3.select(formYAxisRef).call(d3.axisLeft(formScales.yScale).tickFormat((d) => `$${d}`));
		}
	});

	// watch for drug selection changes
	$effect(() => {
		const currentIndex = selectedDrugIndex;

		if (currentIndex !== undefined && Object.keys(searchIndex).length > 0) {
			loadDrugData();
		}
	});
</script>

<!--- content area --->
{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div>
		<!-- form comparison chart -->
		<div class="chart-wrapper">
			<h6 class="chart-title">Average Price Per MG by Form</h6>
			<svg width={chartWidth} height={chartHeight} role="img">
				<g>
					{#each formBars as bar}
						{@const x = formScales.xScale(bar.label) ?? 0}
						{@const y = formScales.yScale(bar.value)}
						{@const barWidth = formScales.xScale.bandwidth()}
						{@const barHeight = chartHeight - margin.bottom - y}
						{@const roundedValue = Math.round(bar.value * 100) / 100}
						{@const cheapestRounded = cheapestForm
							? Math.round(cheapestForm.value * 100) / 100
							: null}
						{@const isCheapest = cheapestRounded !== null && roundedValue === cheapestRounded}
						{@const barOpacity = isCheapest ? 1.0 : 0.8}

						<rect {x} {y} width={barWidth} height={barHeight} fill="#9a2f1f" opacity={barOpacity} />
						<text
							x={x + barWidth / 2}
							y={y - 5}
							text-anchor="middle"
							class="bar-label"
							fill="#333"
							font-weight="bold"
						>
							${bar.value.toFixed(2)}
						</text>
					{/each}
				</g>

				<g
					class="x-axis"
					transform="translate(0,{chartHeight - margin.bottom})"
					bind:this={formXAxisRef}
				></g>
				<g class="y-axis" transform="translate({margin.left},0)" bind:this={formYAxisRef}></g>

				<!-- Y-axis label -->
				<!-- <text
					transform="rotate(-90)"
					x={-(chartHeight / 2)}
					y={15}
					text-anchor="middle"
					class="axis-label"
				>
					Price per MG
				</text> -->
			</svg>

			<!-- {#if cheapestForm}
				<div class="best-value">
					Best Value: <strong>{cheapestForm.label}</strong> at
					<strong>${cheapestForm.value.toFixed(3)}/MG</strong>
				</div>
			{/if} -->
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
		color: 9a2f1f;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
		margin-bottom: 2rem;
	}

	h4 {
		font-family: fustat;
		font-size: 1.2em;
		font-weight: 700;
		text-transform: uppercase;
	}

	h6 {
		font-family: fustat;
		font-size: 1em;
		font-weight: 600;
		text-transform: uppercase;
	}

	.drug-selector {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.drug-selector label {
		font-family: Antonio;
		font-size: 1em;
		font-weight: 600;
		padding-left: 40px;
	}

	.drug-dropdown {
		font-family: fustat;
		font-size: 1em;
		padding: 0.5rem 1rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		background-color: rgba(75, 75, 75, 0.1);
		cursor: pointer;
		min-width: 200px;
	}

	.drug-dropdown:focus {
		outline: 2px solid #54707c;
	}

	.width-tracker {
		margin: 20px 40px;
	}

	.charts-container {
		display: flex;
		gap: 2rem;
		justify-content: space-between;
		border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		padding: 2rem;
		user-select: none;
		-webkit-user-select: none;
	}

	.chart-wrapper {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.chart-title {
		margin-bottom: 1rem;
		text-align: center;
	}

	svg {
		display: block;
	}

	.bar-label {
		font-family: fustat;
		font-size: 0.75em;
	}

	.axis-label {
		font-family: fustat;
		font-size: 0.9em;
		font-weight: 500;
	}

	.best-value {
		font-family: Antonio;
		font-size: 1em;
		text-align: center;
		color: #000000;
	}

	.best-value strong {
		color: #355b75;
	}

	/* y-axis font */
	:global(.y-axis text) {
		font-family: Antonio;
	}
</style>
