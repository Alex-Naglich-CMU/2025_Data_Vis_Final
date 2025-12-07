<!-- paginated version of automated series chart
shows groups of 250 brand drugs at a time with prev/next buttons
loads all brand drugs from search_index_all.json
TWO-LEVEL FILTERING: filter by dosage form, then select individual drugs
-->

<script lang="ts">
	import * as d3 from 'd3';
	import type { ChartPoint } from '$lib/scripts/types';
	import { isDarkMode } from '$lib/stores/theme';
	import { onMount } from 'svelte';
	import { categorizeDosageForm } from '$lib/scripts/formCategorizer';

	// pagination settings
	const DRUGS_PER_PAGE = 250;

	// state for all available drugs
	let allBrandDrugs = $state<{ rxcui: string; name: string }[]>([]);
	let searchIndex = $state<any>({});
	let currentPage = $state(0);
	let loading = $state(true);
	let loadingPage = $state(false);
	let error = $state<string | null>(null);

	// current page drugs data
	interface DrugData {
		rxcui: string;
		friendlyName: string;
		form: string; // detailed dosage form
		formCategory: string; // broad category bucket
		prices: Record<string, Record<string, number>>;
	}
	
	let drugsData = $state<DrugData[]>([]);
	let selectedDrugIndices = $state<Set<number>>(new Set());
	let selectedFormCategories = $state<Set<string>>(new Set());
	let availableFormCategories = $state<string[]>([]);

	let tooltipData = $state<{ date: Date; prices: Map<string, number> } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let chartContainerRef = $state<HTMLDivElement>();

	// layout constants
	const drugColors = d3.schemeCategory10 as string[];
	let containerWidth = $state(0);
	const width = $derived(containerWidth * 0.75 || 900);
	const height = $derived(width * 0.6);
	const margin = { top: 40, right: 40, bottom: 60, left: 80 };

	// pagination calculations
	const totalPages = $derived(Math.ceil(allBrandDrugs.length / DRUGS_PER_PAGE));
	const startIndex = $derived(currentPage * DRUGS_PER_PAGE);
	const endIndex = $derived(Math.min(startIndex + DRUGS_PER_PAGE, allBrandDrugs.length));
	const currentPageDrugs = $derived(allBrandDrugs.slice(startIndex, endIndex));

	// data loading
	onMount(async () => {
		try {
			// load search index
			const searchIndexModule = await import('$lib/data/search_index_all.json');
			searchIndex = searchIndexModule.default;
			console.log('search index loaded:', Object.keys(searchIndex).length, 'entries');

			// extract all brand drugs
			const brands: { rxcui: string; name: string }[] = [];
			for (const [rxcui, data] of Object.entries(searchIndex)) {
				const drugData = data as any;
				if (drugData.is_brand === true && drugData.mate_rxcui) {
					// parse name to get dosage info
					const fullName = drugData.name || '';
					const manufacturerName = drugData.manufacturer_name || '';
					
					// extract dosage and form from full name
					const dosageMatch = fullName.replace(new RegExp(manufacturerName, 'i'), '').trim();
					
					const displayName = manufacturerName && dosageMatch 
						? `${manufacturerName} - ${dosageMatch}`
						: fullName || manufacturerName || 'Unknown';
					
					brands.push({
						rxcui,
						name: displayName
					});
				}
			}

			// sort alphabetically
			brands.sort((a, b) => a.name.localeCompare(b.name));
			allBrandDrugs = brands;
			console.log('total brand drugs found:', brands.length);

			// load first page
			await loadPageData();
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('error loading search index:', err);
		}
	});

	// convert prices object to chart points
	function getChartPoints(drug: DrugData): ChartPoint[] {
		const points: ChartPoint[] = [];
		
		// iterate through all NDCs and their dates
		for (const ndc in drug.prices) {
			for (const [dateStr, price] of Object.entries(drug.prices[ndc])) {
				const date = parseDate(dateStr);
				if (date) {
					// Adjust price based on form type
					let singleDosePrice = price;
					// if (drug.form !== "Oral Capsule" && 
					// 	drug.form !== "Oral Tablet" && 
					// 	drug.form !== "Delayed/Extended Release Oral Tablet" && 
					// 	drug.form !== "Delayed/Extended Release Oral Capsule") {
						singleDosePrice = price / 30;
					// }
				
					points.push({ date, price: singleDosePrice });
				}
			}
		}
		
		// sort by date
		points.sort((a, b) => a.date.getTime() - b.date.getTime());
		
		// remove duplicates (keep last price for each date)
		const dateMap = new Map<string, ChartPoint>();
		for (const point of points) {
			const dateKey = point.date.toISOString().split('T')[0];
			dateMap.set(dateKey, point);
		}
		
		return Array.from(dateMap.values()).sort((a, b) => a.date.getTime() - b.date.getTime());
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
			console.warn('failed to parse date:', dateStr);
		}
		return null;
	}

	// load data for current page of drugs
	async function loadPageData() {
		loadingPage = true;
		try {
			console.log('loading page', currentPage + 1, 'with', currentPageDrugs.length, 'drugs');

			// load drug data for current page
			const loadedDrugs: DrugData[] = [];
			const categoriesSet = new Set<string>();
			
			for (const drug of currentPageDrugs) {
				try {
					// load price data
					const priceModule = await import(`$lib/data/prices/${drug.rxcui}.json`);
					const priceData = priceModule.default;

					// make sure prices exist
					if (!priceData.prices || Object.keys(priceData.prices).length === 0) {
						continue;
					}

					// get form from JSON and categorize it
					const form = priceData.Form || 'Unknown';
					const formCategory = categorizeDosageForm(form);
					
					if (formCategory && formCategory !== 'Other') {
						categoriesSet.add(formCategory);
					}

					loadedDrugs.push({
						rxcui: drug.rxcui,
						friendlyName: drug.name,
						form: form,
						formCategory: formCategory,
						prices: priceData.prices
					});
					
					// log first few for debugging
					if (loadedDrugs.length <= 5) {
						console.log(`${drug.name}: "${form}" → "${formCategory}"`);
					}
				} catch (e) {
					// skip drugs without price data
				}
			}

			drugsData = loadedDrugs;
			
			// update available categories (sorted alphabetically)
			availableFormCategories = Array.from(categoriesSet).sort();
			console.log('loaded', loadedDrugs.length, 'drugs with', availableFormCategories.length, 'unique form categories');
			console.log('categories:', availableFormCategories);

			// select all drugs on current page by default
			const initialSelection = new Set<number>();
			for (let i = 0; i < drugsData.length; i++) {
				initialSelection.add(i);
			}
			selectedDrugIndices = initialSelection;
			selectedFormCategories = new Set<string>();
			
			loadingPage = false;
		} catch (err) {
			console.error('error loading page data:', err);
			loadingPage = false;
		}
	}

	// pagination controls
	async function goToNextPage() {
		if (currentPage < totalPages - 1) {
			currentPage++;
			await loadPageData();
		}
	}

	async function goToPreviousPage() {
		if (currentPage > 0) {
			currentPage--;
			await loadPageData();
		}
	}

	// helper to get most recent price for a drug
	function getMostRecentPrice(drug: DrugData): number {
		let mostRecentDate: Date | null = null;
		let mostRecentPrice: number = 0;

		for (const ndc in drug.prices) {
			for (const [dateStr, price] of Object.entries(drug.prices[ndc])) {
				const date = parseDate(dateStr);
				if (date && (mostRecentDate === null || date > mostRecentDate)) {
					mostRecentDate = date;
					// if (drug.form !== "Oral Capsule" && drug.form !== "Oral Tablet" && drug.form !== "Delayed/Extended Release Oral Tablet" && drug.form !== "Delayed/Extended Release Oral Capsule") {
					// 	mostRecentPrice = price/30;
					// } else {
					mostRecentPrice = price/30;		
					// }	
				}
			}
		}
		return mostRecentPrice;
	}

	// filter drugs by selected categories
	const filteredDrugs = $derived(
		drugsData.filter((drug, i) => {
			// if no categories selected, show all drugs
			if (selectedFormCategories.size === 0) return true;
			// otherwise, only show drugs matching selected categories
			return selectedFormCategories.has(drug.formCategory);
		})
	);

	// data processing - sort by price (highest to lowest) - ONLY FILTERED DRUGS
	const brandDrugs = $derived(
		filteredDrugs
			.map((drug, i) => {
				// need to find original index in drugsData for selection tracking
				const originalIndex = drugsData.indexOf(drug);
				return { 
					drug, 
					i: originalIndex,
					price: getMostRecentPrice(drug)
				};
			})
			.sort((a, b) => b.price - a.price)
	);

	interface LineData {
		data: ChartPoint[];
		color: string;
		label: string;
		drugIndex: number;
	}

	const selectedLines = $derived.by(() => {
		const lines: LineData[] = [];

		filteredDrugs.forEach((drug) => {
			const originalIndex = drugsData.indexOf(drug);
			
			// only show if drug is selected
			if (!selectedDrugIndices.has(originalIndex)) return;
			
			const brandDrugPosition = brandDrugs.findIndex(({ i }) => i === originalIndex);
			const color = drugColors[brandDrugPosition % drugColors.length];

			const chartData = getChartPoints(drug);
			if (chartData.length > 0) {
				lines.push({
					data: chartData,
					color,
					label: drug.friendlyName,
					drugIndex: originalIndex
				});
			}
		});

		return lines;
	});

	const allDataPoints = $derived(selectedLines.flatMap((line) => line.data));

	// chart scales & paths
	function createScales(
		data: ChartPoint[],
		widthVal: number,
		heightVal: number,
		marginVal: typeof margin
	) {
		const hasData = data.length > 0;

		const xScale = d3
			.scaleTime()
			.range([marginVal.left, widthVal - marginVal.right])
			.domain(
				hasData ? (d3.extent(data, (d) => d.date) as [Date, Date]) : [new Date(), new Date()]
			);

		const yScale = d3
			.scaleLinear()
			.range([heightVal - marginVal.bottom, marginVal.top])
			.domain([0, hasData ? (d3.max(data, (d) => d.price * 1.04) ?? 100) : 100])
			.nice();

		return { xScale, yScale };
	}

	const mainScales = $derived(createScales(allDataPoints, width, height, margin));
	const xScale = $derived(mainScales.xScale);
	const yScale = $derived(mainScales.yScale);

	function createLinePath(
		data: ChartPoint[],
		xScale: d3.ScaleTime<number, number>,
		yScale: d3.ScaleLinear<number, number>
	): string {
		if (data.length === 0) return '';
		const lineGen = d3
			.line<ChartPoint>()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.price))
			.curve(d3.curveLinear);
		return lineGen(data) || '';
	}

	const linePaths = $derived(
		selectedLines.map((line) => ({
			...line,
			path: createLinePath(line.data, xScale, yScale)
		}))
	);

	// svg refs
	let mainSvgRef = $state<SVGSVGElement>();
	let xAxisRef = $state<SVGGElement>();
	let yAxisRef = $state<SVGGElement>();

	// effects - axes rendering
	$effect(() => {
		renderXAxis(xAxisRef, xScale, allDataPoints.length);
		renderYAxis(yAxisRef, yScale, allDataPoints.length);
	});

	function renderXAxis(
		ref: SVGGElement | undefined,
		scale: d3.ScaleTime<number, number>,
		dataLength: number
	) {
		if (!ref || dataLength === 0) return;

		const multiFormat = (date: Date) =>
			(d3.timeSecond(date) < date
				? d3.timeFormat('.%L')
				: d3.timeMinute(date) < date
					? d3.timeFormat(':%S')
					: d3.timeHour(date) < date
						? d3.timeFormat('%I:%M')
						: d3.timeDay(date) < date
							? d3.timeFormat('%I %p')
							: d3.timeMonth(date) < date
								? d3.timeWeek(date) < date
									? d3.timeFormat('%a %d')
									: d3.timeFormat('%b %d')
								: d3.timeYear(date) < date
									? d3.timeFormat('%b')
									: d3.timeFormat('%Y'))(date);

		d3.select(ref).call(d3.axisBottom(scale).tickFormat(multiFormat as any));
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

	function toggleDrugSelection(index: number) {
		const newSet = new Set(selectedDrugIndices);
		if (newSet.has(index)) {
			newSet.delete(index);
		} else {
			newSet.add(index);
		}
		selectedDrugIndices = newSet;
	}

	function toggleFormCategorySelection(category: string) {
		const newSet = new Set(selectedFormCategories);
		if (newSet.has(category)) {
			newSet.delete(category);
		} else {
			newSet.add(category);
		}
		selectedFormCategories = newSet;
	}

	// count how many drugs match each category
	const categoryCounts = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const drug of drugsData) {
			counts.set(drug.formCategory, (counts.get(drug.formCategory) || 0) + 1);
		}
		return counts;
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
	<div class="width-tracker" bind:clientWidth={containerWidth}>
		<div class="content-wrapper">
			<!---main chart --->
			<div class="chart-wrapper" bind:this={chartContainerRef}>
				{#if loadingPage}
					<div class="loading-overlay">
						<p>Loading page data...</p>
					</div>
				{/if}
				
				<svg {width} {height} role="img" bind:this={mainSvgRef}>
					<defs>
						<clipPath id="animated-series-clip">
							<rect
								x={margin.left}
								y={margin.top}
								width={width - margin.left - margin.right}
								height={height - margin.top - margin.bottom}
							/>
						</clipPath>
					</defs>

					<g clip-path="url(#animated-series-clip)">
						<!-- draw all lines -->
						{#each linePaths as line}
							{#if line.path}
								<path d={line.path} fill="none" style="stroke: {line.color}" stroke-width="2" />
							{/if}
						{/each}

						<!-- draw all data points -->
						{#each linePaths as line}
							{#each line.data as point}
								<circle
									cx={xScale(point.date)}
									cy={yScale(point.price)}
									r="2"
									fill={line.color}
									stroke={$isDarkMode ? '#ddd' : '#222'}
									style="cursor: pointer; pointer-events: all;"
									onmouseenter={(e) => {
										const prices = new Map<string, number>();
										prices.set(line.label, point.price);
										tooltipData = { date: point.date, prices };
										cursorX = e.clientX;
										cursorY = e.clientY;
									}}
									onmouseleave={() => {
										tooltipData = null;
									}}
									onmousemove={(e) => {
										cursorX = e.clientX;
										cursorY = e.clientY;
									}}
								/>
							{/each}
						{/each}
					</g>

					<g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}
					></g>
					<g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>
				</svg>

				<!--- tooltip --->
				{#if tooltipData}
					{@const dateStr = tooltipData.date.toLocaleDateString('en-US', {
						month: 'long',
						year: 'numeric'
					})}
					{@const containerRect = chartContainerRef?.getBoundingClientRect()}
					{@const tooltipX = containerRect ? cursorX - containerRect.left + 15 : 0}
					{@const tooltipY = containerRect ? cursorY - containerRect.top : 0}

					<div class="tooltip" style="left: {tooltipX}px; top: {tooltipY}px;">
						<div class="tooltip-date"><strong>{dateStr}</strong></div>

						{#each Array.from(tooltipData.prices.entries()) as [label, price]}
							{@const lineData = linePaths.find((l) => l.label === label)}
							<div class="tooltip-row">
								<span class="label" style="color: {lineData?.color || '#000'}">
									{label}:
								</span>
								<span class="value">${price.toFixed(2)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!--- side bar --->
			<div class="side-bar">
				<div class="controls">
					<!-- pagination controls -->
					<div class="pagination-controls">
						<div class="pagination-info">
							<strong>Page {currentPage + 1} of {totalPages}</strong>
							<div class="text-sm">
								Showing {startIndex + 1}-{endIndex} of {allBrandDrugs.length} drugs
							</div>
						</div>
						<div class="pagination-buttons">
							<button
								class="pagination-btn"
								onclick={goToPreviousPage}
								disabled={currentPage === 0 || loadingPage}
							>
								← Previous
							</button>
							<button
								class="pagination-btn"
								onclick={goToNextPage}
								disabled={currentPage >= totalPages - 1 || loadingPage}
							>
								Next →
							</button>
						</div>
					</div>

					<!-- form filter section -->
					<div class="form-filter-section">
						<div class="mb-2">
							<label>Filter by Dosage Form Category:</label>
							<div class="text-sm text-gray-500">
								{selectedFormCategories.size > 0 
									? `${filteredDrugs.length} of ${drugsData.length} drugs` 
									: 'All forms'}
							</div>
						</div>
						<ul class="form-list">
							{#each availableFormCategories as category}
								{@const isSelected = selectedFormCategories.has(category)}
								{@const count = categoryCounts.get(category) || 0}
								<li
									class="form-list-item"
									class:selected={isSelected}
									class:unselected={!isSelected}
									onclick={() => toggleFormCategorySelection(category)}
									role="option"
									aria-selected={isSelected}
									tabindex="0"
								>
									<span class="checkmark">{isSelected ? '✓' : ''}</span>
									<span class="form-name">{category}</span>
									<span class="form-count">({count})</span>
								</li>
							{/each}
						</ul>
					</div>

					<!-- drug selection section -->
					<div class="drug-selection-section">
						<div class="mb-2 flex items-center justify-between">
							<label for="drug-list">Select Drugs:</label>
							<span class="text-sm text-gray-500">* For a single dose</span>
						</div>
						<ul class="drug-list" role="listbox">
							{#each brandDrugs as { drug, i, price }}
								{@const brandDrugPosition = brandDrugs.findIndex(({ i: idx }) => idx === i)}
								{@const color = drugColors[brandDrugPosition % drugColors.length]}
								{@const isSelected = selectedDrugIndices.has(i)}
								<li
									class="drug-list-item"
									class:selected={isSelected}
									onclick={() => toggleDrugSelection(i)}
									onkeydown={(e) => {
										if (e.key === 'Enter' || e.key === ' ') toggleDrugSelection(i);
									}}
									role="option"
									aria-selected={isSelected}
									tabindex="0"
									style="border-left: 4px solid {color}; {isSelected
										? `background-color: ${color}70; color: ${color};`
										: ''}"
								>
									<span class="checkmark">{isSelected ? '✓' : ''}</span>
									<span class="drug-name">{drug.friendlyName.toUpperCase()}</span>
									<span class="drug-price">${price.toFixed(2)}</span>
								</li>
							{/each}
						</ul>
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

	.loading-overlay {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		background: rgba(255, 255, 255, 0.9);
		padding: 2rem;
		border-radius: 8px;
		border: 2px solid #ccc;
		z-index: 100;
		font-family: fustat;
	}

	.pagination-controls {
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		border-bottom: 2px solid #ccc;
	}

	.pagination-info {
		text-align: center;
		margin-bottom: 0.75rem;
		font-family: fustat;
	}

	.pagination-info .text-sm {
		font-size: 0.85em;
		color: #666;
		margin-top: 0.25rem;
	}

	.pagination-buttons {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
	}

	.pagination-btn {
		font-family: fustat;
		padding: 0.5rem 1rem;
		border: 1px solid #ccc;
		background-color: rgba(75, 75, 75, 0.1);
		cursor: pointer;
		border-radius: 4px;
		font-size: 0.9em;
		transition: background-color 0.2s;
	}

	.pagination-btn:hover:not(:disabled) {
		background-color: rgba(75, 75, 75, 0.2);
	}

	.pagination-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.form-filter-section {
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		border-bottom: 2px solid #ccc;
	}

	.form-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		max-height: 200px;
		overflow-y: auto;
		border: 2px solid rgba(128, 128, 128, 0.5);
		border-radius: 4px;
	}

	.form-list-item {
		padding: 0.4rem 0.8rem;
		cursor: pointer;
		transition: background-color 0.2s;
		font-family: fustat;
		font-size: 13px;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background-color: rgba(75, 75, 75, 0.2);
		border-bottom: 1px solid rgba(128, 128, 128, 0.5);
	}

	.form-list-item:last-child {
		border-bottom: none;
	}

	.form-list-item .checkmark {
		width: 1rem;
		font-weight: bold;
	}

	.form-list-item .form-name {
		flex: 1;
	}

	.form-list-item .form-count {
		margin-left: auto;
		font-size: 0.85em;
		color: #666;
	}

	.form-list-item:hover {
		background-color: rgba(128, 128, 128, 0.15);
	}

	.form-list-item.selected {
		font-weight: 600;
		background-color: rgba(45, 106, 79, 0.15);
		border-left: 3px solid #2D6A4F;
	}

	.form-list-item.unselected {
		opacity: 0.7;
	}

	.drug-selection-section {
		flex: 1;
		display: flex;
		flex-direction: column;
	}

	.drug-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		max-height: 300px;
		overflow-y: auto;
		border: 2px solid rgba(128, 128, 128, 0.5);
		border-radius: 4px;
		flex: 1;
	}

	.drug-list-item {
		padding: 0.5rem 1rem;
		cursor: pointer;
		transition: background-color 0.2s;
		font-family: fustat;
		font-size: 14px;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background-color: rgba(75, 75, 75, 0.2);
		border-bottom: 1px solid rgba(128, 128, 128, 0.5);
	}

	.drug-list-item:last-child {
		border-bottom: none;
	}

	.drug-list-item .checkmark {
		width: 1rem;
		font-weight: bold;
	}

	.drug-list-item .drug-name {
		flex: 1;
	}

	.drug-list-item .drug-price {
		margin-left: auto;
		font-weight: 600;
		font-size: 0.9em;
	}

	.drug-list-item:hover {
		background-color: rgba(128, 128, 128, 0.15);
	}

	.drug-list-item.selected {
		font-weight: 600;
	}

	.drug-list-item:focus {
		outline: 2px solid #54707c;
		outline-offset: -2px;
	}

	.width-tracker {
		margin: 20px 40px;
	}

	.content-wrapper {
		display: flex;
		justify-content: left;
		align-items: top;
		border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
		box-sizing: border-box;
		user-select: none;
		-webkit-user-select: none;
	}

	.chart-wrapper {
		padding: 10px 0 0 0;
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
		position: relative;
	}

	.side-bar {
		padding: 10px 10px 0 20px;
		width: 25%;
		display: flex;
		flex-direction: column;
		border-left: 1px solid #ccc;
	}

	.controls {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	svg {
		display: block;
	}

	.tooltip {
		position: absolute;
		background: white;
		color: #000;
		border: 2px solid #333;
		border-radius: 8px;
		padding: 12px;
		pointer-events: none;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 1000;
		min-width: 200px;
		max-height: 400px;
		overflow-y: auto;
		transform: translateY(-50%);
	}

	.tooltip-date {
		margin-bottom: 8px;
		padding-bottom: 8px;
		border-bottom: 1px solid #ddd;
		font-size: 14px;
		color: #000;
		font-weight: bold;
	}

	.tooltip-row {
		display: flex;
		justify-content: space-between;
		margin: 6px 0;
		font-size: 13px;
		color: #000;
	}

	.tooltip-row .label {
		font-weight: 600;
	}

	.tooltip-row .value {
		font-weight: 600;
		color: #000;
	}

	.text-sm {
		font-size: 0.85em;
	}

	.text-gray-500 {
		color: #666;
	}

	.mb-2 {
		margin-bottom: 0.5rem;
	}

	.flex {
		display: flex;
	}

	.items-center {
		align-items: center;
	}

	.justify-between {
		justify-content: space-between;
	}
</style>