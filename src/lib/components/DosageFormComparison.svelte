<!-- how this works:
1. loads search_index_all.json to find all RxCUIs for the selected drug
2. loads individual json files for each RxCUI to get Strength and Form fields
3. averages the prices across multiple NDCs and groups them by strength or form
4. renders two separate side by side line charts 
-->

<script lang="ts">
	import * as d3 from 'd3';
	import { onMount } from 'svelte';
	import { isDarkMode } from '$lib/stores/theme';
    import searchIndexData from '$lib/data/search_index_all.json';


	// PROPS & STATE
	const brandDrugs = [
		{ name: 'GLUCOPHAGE', manufacturer: 'glucophage' },
		{ name: 'LANTUS', manufacturer: 'lantus' },
		{ name: 'LEXAPRO', manufacturer: 'lexapro' },
		{ name: 'LIPITOR', manufacturer: 'lipitor' },
		{ name: 'LYRICA', manufacturer: 'lyrica' },
		{ name: 'NORVASC', manufacturer: 'norvasc' },
		{ name: 'PROVIGIL', manufacturer: 'provigil' },
		{ name: 'PROZAC', manufacturer: 'prozac' },
		{ name: 'VYVANSE', manufacturer: 'vyvanse' },
		{ name: 'ZOLOFT', manufacturer: 'zoloft' }
	];

	interface DrugVariation {
		rxcui: string;
		name: string;
		strength: string;
		form: string;
		prices: { date: Date; price: number }[];
	}

	let selectedDrugIndex = $state(8); // Default to VYVANSE
	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchIndex = $state<any>({});
	let drugVariations = $state<DrugVariation[]>([]);
	
	let tooltipData = $state<{ date: Date; prices: Map<string, number> } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let strengthChartRef = $state<HTMLDivElement>();
	let formChartRef = $state<HTMLDivElement>();

	// LAYOUT CONSTANTS
	const colors = d3.schemeCategory10 as string[];
	let containerWidth = $state(0);
	const chartWidth = $derived((containerWidth * 0.48) || 500);
	const chartHeight = $derived(chartWidth * 0.7);
	const margin = { top: 40, right: 40, bottom: 60, left: 80 };

	// DATA LOADING
onMount(async () => {
	try {
		// Import search index directly
		const searchIndexModule = await import('$lib/data/search_index_all.json');
		searchIndex = searchIndexModule.default;
		console.log('✅ Search index loaded:', Object.keys(searchIndex).length, 'entries');
		loading = false;
		await loadDrugData();
	} catch (err) {
		error = err instanceof Error ? err.message : 'Unknown error';
		loading = false;
		console.error('❌ Error loading search index:', err);
	}
});

	// Load data for selected drug
	async function loadDrugData() {
		loading = true;
		error = null;
		drugVariations = [];

		try {
			const selectedDrug = brandDrugs[selectedDrugIndex];
			console.log('🔍 Loading data for:', selectedDrug.name);
			const variations: DrugVariation[] = [];

			// Find all RxCUIs for this drug
			for (const [rxcui, data] of Object.entries(searchIndex)) {
				const drugData = data as any;
				if (
					drugData.manufacturer_name &&
					drugData.manufacturer_name.toLowerCase().includes(selectedDrug.manufacturer) &&
					drugData.is_brand === true
				) {
					console.log('  ✓ Found variation:', rxcui, drugData.name);
					
					// load price data to get strength and form from JSON
					try {
						const priceResponse = await import(`$lib/data/prices/${rxcui}.json`);
						const priceData = priceResponse.default;
						
						// get strength and form directly from JSON
						const strength = priceData.Strength || '';
						const form = priceData.Form || '';
						console.log('    → Strength from JSON:', strength, '| Form from JSON:', form);
						
						if (strength && form) {
							const prices = parsePrices(priceData.prices);
							console.log('    → Loaded', prices.length, 'price points');

							variations.push({
								rxcui,
								name: drugData.name,
								strength,
								form,
								prices
							});
						}
					} catch (e) {
						console.warn(`    ⚠️ No price data for ${rxcui}`);
					}
				}
			}

			drugVariations = variations;
			console.log('📊 Total variations loaded:', variations.length);
			console.log('📦 Variations:', variations);
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error loading drug data';
			loading = false;
			console.error('❌ Error loading drug data:', err);
		}
	}

	// Parse prices from JSON format
	function parsePrices(pricesObj: any): { date: Date; price: number }[] {
		const allPrices: { date: Date; price: number }[] = [];
		const priceMap = new Map<string, number[]>();

		// Aggregate prices across all NDCs for each date
		for (const ndc in pricesObj) {
			for (const [dateStr, price] of Object.entries(pricesObj[ndc])) {
				if (!priceMap.has(dateStr)) {
					priceMap.set(dateStr, []);
				}
				priceMap.get(dateStr)!.push(price as number);
			}
		}

		// Average prices for each date
		for (const [dateStr, prices] of priceMap.entries()) {
			const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
			const date = parseDate(dateStr);
			if (date) {
				allPrices.push({ date, price: avgPrice });
			}
		}

		return allPrices.sort((a, b) => a.date.getTime() - b.date.getTime());
	}

	// Parse date string
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

	// Group variations by strength
	const strengthGroups = $derived.by(() => {
		const groups = new Map<string, DrugVariation[]>();
		for (const variation of drugVariations) {
			if (!groups.has(variation.strength)) {
				groups.set(variation.strength, []);
			}
			groups.get(variation.strength)!.push(variation);
		}
		return groups;
	});

	// Group variations by form
	const formGroups = $derived.by(() => {
		const groups = new Map<string, DrugVariation[]>();
		for (const variation of drugVariations) {
			if (!groups.has(variation.form)) {
				groups.set(variation.form, []);
			}
			groups.get(variation.form)!.push(variation);
		}
		return groups;
	});

	// Create line data for strength comparison
	const strengthLines = $derived.by(() => {
		const lines: { label: string; data: { date: Date; price: number }[]; color: string }[] = [];
		let colorIndex = 0;

		for (const [strength, variations] of strengthGroups.entries()) {
			// Average prices across all forms for this strength
			const priceMap = new Map<number, number[]>();
			
			for (const variation of variations) {
				for (const point of variation.prices) {
					const timestamp = point.date.getTime();
					if (!priceMap.has(timestamp)) {
						priceMap.set(timestamp, []);
					}
					priceMap.get(timestamp)!.push(point.price);
				}
			}

			const data: { date: Date; price: number }[] = [];
			for (const [timestamp, prices] of priceMap.entries()) {
				const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
				data.push({ date: new Date(timestamp), price: avgPrice });
			}

			if (data.length > 0) {
				lines.push({
					label: strength,
					data: data.sort((a, b) => a.date.getTime() - b.date.getTime()),
					color: colors[colorIndex % colors.length]
				});
				colorIndex++;
			}
		}

		return lines;
	});

	// Create line data for form comparison
	const formLines = $derived.by(() => {
		const lines: { label: string; data: { date: Date; price: number }[]; color: string }[] = [];
		let colorIndex = 0;

		for (const [form, variations] of formGroups.entries()) {
			// Average prices across all strengths for this form
			const priceMap = new Map<number, number[]>();
			
			for (const variation of variations) {
				for (const point of variation.prices) {
					const timestamp = point.date.getTime();
					if (!priceMap.has(timestamp)) {
						priceMap.set(timestamp, []);
					}
					priceMap.get(timestamp)!.push(point.price);
				}
			}

			const data: { date: Date; price: number }[] = [];
			for (const [timestamp, prices] of priceMap.entries()) {
				const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
				data.push({ date: new Date(timestamp), price: avgPrice });
			}

			if (data.length > 0) {
				lines.push({
					label: form,
					data: data.sort((a, b) => a.date.getTime() - b.date.getTime()),
					color: colors[colorIndex % colors.length]
				});
				colorIndex++;
			}
		}

		return lines;
	});

	// Combined data points for scales
	const allStrengthPoints = $derived(strengthLines.flatMap((line) => line.data));
	const allFormPoints = $derived(formLines.flatMap((line) => line.data));

	// Debug effect to log groups and lines
	$effect(() => {
		console.log('💪 Strength groups:', strengthGroups);
		console.log('📝 Form groups:', formGroups);
		console.log('📈 Strength lines:', strengthLines);
		console.log('📉 Form lines:', formLines);
	});

	// CHART SCALES
	function createScales(data: { date: Date; price: number }[], width: number, height: number) {
		const hasData = data.length > 0;

		const xScale = d3
			.scaleTime()
			.range([margin.left, width - margin.right])
			.domain(hasData ? (d3.extent(data, (d) => d.date) as [Date, Date]) : [new Date(), new Date()]);

		const yScale = d3
			.scaleLinear()
			.range([height - margin.bottom, margin.top])
			.domain([0, hasData ? (d3.max(data, (d) => d.price * 1.1) ?? 100) : 100])
			.nice();

		return { xScale, yScale };
	}

	const strengthScales = $derived(createScales(allStrengthPoints, chartWidth, chartHeight));
	const formScales = $derived(createScales(allFormPoints, chartWidth, chartHeight));

	// SVG refs
	let strengthSvgRef = $state<SVGSVGElement>();
	let formSvgRef = $state<SVGSVGElement>();
	let strengthXAxisRef = $state<SVGGElement>();
	let strengthYAxisRef = $state<SVGGElement>();
	let formXAxisRef = $state<SVGGElement>();
	let formYAxisRef = $state<SVGGElement>();

	// EFFECTS - AXES RENDERING
	$effect(() => {
		renderXAxis(strengthXAxisRef, strengthScales.xScale, allStrengthPoints.length);
		renderYAxis(strengthYAxisRef, strengthScales.yScale, allStrengthPoints.length);
		renderXAxis(formXAxisRef, formScales.xScale, allFormPoints.length);
		renderYAxis(formYAxisRef, formScales.yScale, allFormPoints.length);
	});

	// Watch for drug selection changes
	$effect(() => {
		if (selectedDrugIndex !== undefined && Object.keys(searchIndex).length > 0) {
			loadDrugData();
		}
	});

	// HELPER FUNCTIONS
	function createLinePath(
		data: { date: Date; price: number }[],
		xScale: d3.ScaleTime<number, number>,
		yScale: d3.ScaleLinear<number, number>
	): string {
		if (data.length === 0) return '';
		const lineGen = d3
			.line<{ date: Date; price: number }>()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price))
			.curve(d3.curveStepAfter);
		return lineGen(data) || '';
	}

	function renderXAxis(
		ref: SVGGElement | undefined,
		scale: d3.ScaleTime<number, number>,
		dataLength: number
	) {
		if (!ref || dataLength === 0) return;
		d3.select(ref).call(d3.axisBottom(scale).tickFormat(d3.timeFormat('%Y') as any));
	}

	function renderYAxis(
		ref: SVGGElement | undefined,
		scale: d3.ScaleLinear<number, number>,
		dataLength: number
	) {
		if (!ref || dataLength === 0) return;
		const yAxis = d3.axisLeft(scale).tickFormat((d) => `$${d}`);
		d3.select(ref).call(yAxis);
	}
</script>

<!--- CONTENT AREA --->
{#if loading}
	<div class="loading">
		<p>Loading drug data...</p>
	</div>
{:else if error}
	<div class="error">
		<p>Error loading data: {error}</p>
	</div>
{:else}
	<div class="mt-20">
		
		<!-- Drug Selector -->
		<div class="drug-selector">
			<label for="drug-select">Select Drug:</label>
			<select 
				id="drug-select" 
				bind:value={selectedDrugIndex}
				class="drug-dropdown"
			>
				{#each brandDrugs as drug, i}
					<option value={i}>{drug.name}</option>
				{/each}
			</select>
		</div>

		<div class="width-tracker" bind:clientWidth={containerWidth}>
			<div class="charts-container">
				<!-- STRENGTH COMPARISON CHART -->
				<div class="chart-wrapper" bind:this={strengthChartRef}>
					<h4 class="chart-title">By Dosage Strength</h4>
					<svg width={chartWidth} height={chartHeight} role="img" bind:this={strengthSvgRef}>
						<defs>
							<clipPath id="strength-clip">
								<rect
									x={margin.left}
									y={margin.top}
									width={chartWidth - margin.left - margin.right}
									height={chartHeight - margin.top - margin.bottom}
								/>
							</clipPath>
						</defs>

						<g clip-path="url(#strength-clip)">
							{#each strengthLines as line}
								{@const path = createLinePath(line.data, strengthScales.xScale, strengthScales.yScale)}
								{#if path}
									<path d={path} fill="none" style="stroke: {line.color}" stroke-width="2" />
								{/if}
							{/each}
						</g>

						<g class="x-axis" transform="translate(0,{chartHeight - margin.bottom})" bind:this={strengthXAxisRef}></g>
						<g class="y-axis" transform="translate({margin.left},0)" bind:this={strengthYAxisRef}></g>
					</svg>

					<!-- Legend -->
					<div class="legend">
						{#each strengthLines as line}
							<div class="legend-item">
								<div class="legend-color" style="background-color: {line.color}"></div>
								<span>{line.label}</span>
							</div>
						{/each}
					</div>
				</div>

				<!-- FORM COMPARISON CHART -->
				<div class="chart-wrapper" bind:this={formChartRef}>
					<h4 class="chart-title">By Form</h4>
					<svg width={chartWidth} height={chartHeight} role="img" bind:this={formSvgRef}>
						<defs>
							<clipPath id="form-clip">
								<rect
									x={margin.left}
									y={margin.top}
									width={chartWidth - margin.left - margin.right}
									height={chartHeight - margin.top - margin.bottom}
								/>
							</clipPath>
						</defs>

						<g clip-path="url(#form-clip)">
							{#each formLines as line}
								{@const path = createLinePath(line.data, formScales.xScale, formScales.yScale)}
								{#if path}
									<path d={path} fill="none" style="stroke: {line.color}" stroke-width="2" />
								{/if}
							{/each}
						</g>

						<g class="x-axis" transform="translate(0,{chartHeight - margin.bottom})" bind:this={formXAxisRef}></g>
						<g class="y-axis" transform="translate({margin.left},0)" bind:this={formYAxisRef}></g>
					</svg>

					<!-- Legend -->
					<div class="legend">
						{#each formLines as line}
							<div class="legend-item">
								<div class="legend-color" style="background-color: {line.color}"></div>
								<span>{line.label}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>
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
		color: red;
	}

	h4 {
		font-family: fustat;
		font-size: 1.2em;
		font-weight: 700;
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
		font-size: 1.1em;
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

	.legend {
		margin-top: 1rem;
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		justify-content: center;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: fustat;
		font-size: 0.9em;
	}

	.legend-color {
		width: 20px;
		height: 3px;
	}

	/* Axis styling is in app.css */
</style>