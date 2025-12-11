<!-- scrollable version of automated series chart
loads drug data on-demand when selected from search_index_all.json
MODIFIED: Shows average price per year instead of all data points
-->

<script lang="ts">
	import * as d3 from 'd3';
	import type { ChartPoint } from '$lib/scripts/types';
	import { isDarkMode } from '$lib/stores/theme';
	import { onMount } from 'svelte';
	import { categorizeDosageForm } from '$lib/scripts/formCategorizer';

	// state for all available drugs (just names, no price data loaded yet)
	let allBrandDrugs = $state<{ rxcui: string; name: string }[]>([]);
	let searchIndex = $state<any>({});
	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchQuery = $state('');

	// loaded drug data
	interface DrugData {
		rxcui: string;
		friendlyName: string;
		form: string; // detailed dosage form
		formCategory: string; // broad category bucket
		prices: Record<string, Record<string, number>>;
	}

	// Array of loaded drug data
	let loadedDrugs = $state<DrugData[]>([]);
	// Array of selected rxcuis
	let selectedRxcuis = $state<string[]>([]);
	// Array of currently loading rxcuis
	let loadingRxcuis = $state<string[]>([]);
	// Selected form categories for filtering
	let selectedFormCategories = $state<string[]>([]);
	// Available form categories (derived from loaded drugs)
	const availableFormCategories = $derived(
		[...new Set(loadedDrugs.map((d) => d.formCategory).filter((c) => c && c !== 'Other'))].sort()
	);

	let tooltipData = $state<{ date: Date; prices: { label: string; price: number }[] } | null>(null);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let chartContainerRef = $state<HTMLDivElement>();

	// layout constants
	const drugColors = d3.schemeCategory10 as string[];
	let containerWidth = $state(0);
	const width = $derived(containerWidth * 0.65 || 900);
	const height = $derived(width * 0.7);
	const margin = { top: 40, right: 40, bottom: 60, left: 80 };

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

					// Remove both manufacturerName and ' [manufacturerName]' from fullName
					let dosageMatch = fullName;
					if (manufacturerName) {
						// Remove ' [manufacturerName]' if present
						const bracketed = ` [${manufacturerName}]`;
						if (dosageMatch.endsWith(bracketed)) {
							dosageMatch = dosageMatch.slice(0, -bracketed.length).trim();
						}
						// Remove manufacturerName if present at the end
						if (dosageMatch.endsWith(manufacturerName)) {
							dosageMatch = dosageMatch.slice(0, -manufacturerName.length).trim();
						}
					}

					const displayName =
						manufacturerName && dosageMatch
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

			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			loading = false;
			console.error('error loading search index:', err);
		}
	});

	// convert prices object to chart points - averaged by year
	function getChartPoints(drug: DrugData): ChartPoint[] {
		const yearPrices: Record<number, number[]> = {};

		// iterate through all NDCs and their dates, grouping by year
		for (const ndc in drug.prices) {
			for (const [dateStr, price] of Object.entries(drug.prices[ndc])) {
				const date = parseDate(dateStr);
				if (date) {
					const year = date.getFullYear();
					const singleDosePrice = price / 30;

					if (!yearPrices[year]) {
						yearPrices[year] = [];
					}
					yearPrices[year].push(singleDosePrice);
				}
			}
		}

		// calculate average price for each year
		const points: ChartPoint[] = [];
		for (const [yearStr, prices] of Object.entries(yearPrices)) {
			const year = parseInt(yearStr);
			const avgPrice = prices.reduce((sum, p) => sum + p, 0) / prices.length;
			// use January 1st of each year as the date
			points.push({
				date: new Date(year, 0, 1),
				price: avgPrice
			});
		}

		// sort by date
		points.sort((a, b) => a.date.getTime() - b.date.getTime());

		return points;
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

	// load data for a single drug on-demand
	async function loadDrugData(rxcui: string, friendlyName: string): Promise<DrugData | null> {
		// already loaded?
		const existing = loadedDrugs.find((d) => d.rxcui === rxcui);
		if (existing) {
			return existing;
		}

		// mark as loading
		loadingRxcuis = [...loadingRxcuis, rxcui];

		try {
			const priceModule = await import(`$lib/data/prices/${rxcui}.json`);
			const priceData = priceModule.default;

			// make sure prices exist
			if (!priceData.prices || Object.keys(priceData.prices).length === 0) {
				loadingRxcuis = loadingRxcuis.filter((r) => r !== rxcui);
				return null;
			}

			// get form from JSON and categorize it
			const form = priceData.Form || 'Unknown';
			const formCategory = categorizeDosageForm(form);

			const drugData: DrugData = {
				rxcui,
				friendlyName,
				form,
				formCategory,
				prices: priceData.prices
			};

			// store in array
			loadedDrugs = [...loadedDrugs, drugData];
			console.log(`Loaded: ${friendlyName}`);

			// remove from loading
			loadingRxcuis = loadingRxcuis.filter((r) => r !== rxcui);
			return drugData;
		} catch (e) {
			console.warn(`Failed to load drug ${rxcui}:`, e);
			loadingRxcuis = loadingRxcuis.filter((r) => r !== rxcui);
			return null;
		}
	}

	// 7 main categories for sidebar filter chips
	const SIDEBAR_FORM_CATEGORIES = [
		'Delayed/Extended Release Oral Capsules',
		'Delayed/Extended Release Oral Tablets',
		'Oral Capsule',
		'Oral Tablet',
		'Injection',
		'Inhalation',
		'Topical'
	];
	let sidebarFormCategory = $state<string>('');

	// search and sidebar-chip filtered drugs from allBrandDrugs (not loaded data)
	const searchFilteredDrugs = $derived(
		allBrandDrugs.filter((drug) => {
			// Filter by search string
			const matchesSearch =
				!searchQuery.trim() || drug.name.toLowerCase().includes(searchQuery.toLowerCase());
			if (!matchesSearch) return false;

			// Filter by sidebar chip (if any)
			if (!sidebarFormCategory) return true;

			const formCategory = searchIndex[drug.rxcui]?.formCategory || '';
			return formCategory === sidebarFormCategory;
		})
	);

	// helper to get most recent price for a drug
	function getMostRecentPrice(drugData: DrugData): number {
		let mostRecentDate: Date | null = null;
		let mostRecentPrice: number = 0;

		for (const ndc in drugData.prices) {
			for (const [dateStr, price] of Object.entries(drugData.prices[ndc])) {
				const date = parseDate(dateStr);
				if (date && (mostRecentDate === null || date > mostRecentDate)) {
					mostRecentDate = date;
					mostRecentPrice = price / 30;
				}
			}
		}
		return mostRecentPrice;
	}

	// get selected drugs with their loaded data, filtered by form category
	const selectedDrugsWithData = $derived(
		selectedRxcuis
			.map((rxcui) => loadedDrugs.find((d) => d.rxcui === rxcui))
			.filter((d): d is DrugData => d !== undefined)
			.filter((d) => {
				// if no form categories selected, show all
				if (selectedFormCategories.length === 0) return true;
				// otherwise filter by selected categories
				return selectedFormCategories.includes(d.formCategory);
			})
	);

	const drugListItems = $derived(
		searchFilteredDrugs.map((drug) => {
			const price = searchIndex[drug.rxcui]?.most_recent_price ?? null;
			return {
				rxcui: drug.rxcui,
				name: drug.name,
				price,
				isSelected: selectedRxcuis.includes(drug.rxcui),
				isLoading: loadingRxcuis.includes(drug.rxcui)
			};
		})
	);

	interface LineData {
		data: ChartPoint[];
		color: string;
		label: string;
		rxcui: string;
	}

	const selectedLines = $derived.by(() => {
		const lines: LineData[] = [];

		selectedDrugsWithData.forEach((drug, index) => {
			const color = drugColors[index % drugColors.length];

			const chartData = getChartPoints(drug);
			if (chartData.length > 0) {
				lines.push({
					data: chartData,
					color,
					label: drug.friendlyName,
					rxcui: drug.rxcui
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

	async function toggleDrugSelection(rxcui: string, friendlyName: string) {
		if (selectedRxcuis.includes(rxcui)) {
			// deselect
			selectedRxcuis = selectedRxcuis.filter((r) => r !== rxcui);
		} else {
			// select and load data if needed
			selectedRxcuis = [...selectedRxcuis, rxcui];

			// load data if not already loaded
			if (!loadedDrugs.find((d) => d.rxcui === rxcui)) {
				await loadDrugData(rxcui, friendlyName);
			}
		}
	}

	function toggleFormCategorySelection(category: string) {
		if (selectedFormCategories.includes(category)) {
			selectedFormCategories = selectedFormCategories.filter((c) => c !== category);
		} else {
			selectedFormCategories = [...selectedFormCategories, category];
		}
	}
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
				<!-- form filter chips above chart -->
				{#if availableFormCategories.length > 0}
					<div class="form-filter-chips ml-1 mb-4 pb-4">
						{#each availableFormCategories as category}
							{@const isSelected = selectedFormCategories.includes(category)}
							<button
								class="form-chip"
								class:selected={isSelected}
								onclick={() => toggleFormCategorySelection(category)}
							>
								{category}
							</button>
						{/each}
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
									role="button"
									aria-label="{line.label} on {point.date.toDateString()}: ${point.price.toFixed(
										2
									)}"
									tabindex="0"
									r="4"
									fill={line.color}
									stroke={$isDarkMode ? '#ddd' : '#222'}
									style="cursor: pointer; pointer-events: all;"
									onmouseenter={(e) => {
										tooltipData = {
											date: point.date,
											prices: [{ label: line.label, price: point.price }]
										};
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
						year: 'numeric'
					})}
					{@const containerRect = chartContainerRef?.getBoundingClientRect()}
					{@const tooltipX = containerRect ? cursorX - containerRect.left + 15 : 0}
					{@const tooltipY = containerRect ? cursorY - containerRect.top : 0}

					<div class="tooltip" style="left: {tooltipX}px; top: {tooltipY}px;">
						<div class="tooltip-date"><strong>{dateStr} Average</strong></div>

						{#each tooltipData.prices as { label, price }}
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
					<!-- search bar -->

					<div class="w-full text-right">
						<span class="text-sm text-gray-500">* For a single dose</span>
					</div>

					<div class="search-bar">
						<input
							type="text"
							class="search-input"
							placeholder="Search drugs..."
							bind:value={searchQuery}
						/>
						{#if searchQuery}
							<button class="clear-search" onclick={() => (searchQuery = '')}> ✕ </button>
						{/if}
					</div>

					<div class="drug-count">
						Showing {searchFilteredDrugs.length} of {allBrandDrugs.length} drugs
						{#if selectedRxcuis.length > 0}
							<span class="selected-count">({selectedRxcuis.length} selected)</span>
						{/if}
					</div>

					<!-- drug selection section -->
					<div class="flex flex-row">
						<div class="drug-selection-section flex-col">
							<div class="flex flex-row">
								<ul class="drug-list w-2/3" role="listbox">
									{#each drugListItems as item, index}
										{@const color = item.isSelected
											? drugColors[selectedRxcuis.indexOf(item.rxcui) % drugColors.length]
											: '#888'}
										<li
											class="drug-list-item"
											class:selected={item.isSelected}
											class:loading={item.isLoading}
											onclick={() => toggleDrugSelection(item.rxcui, item.name)}
											onkeydown={(e) => {
												if (e.key === 'Enter' || e.key === ' ')
													toggleDrugSelection(item.rxcui, item.name);
											}}
											role="option"
											aria-selected={item.isSelected}
											tabindex="0"
											style="border-left: 4px solid {color}; {item.isSelected
												? `background-color: ${color}70;`
												: ''}"
										>
											<span class="checkmark">
												{#if item.isLoading}
													<span class="spinner">⏳</span>
												{:else if item.isSelected}
													✓
												{/if}
											</span>
											<span class="drug-name">{item.name.toUpperCase()}</span>
											{#if item.price !== null}
												<span class="drug-price">${item.price.toFixed(2)}</span>
											{/if}
										</li>
									{/each}
								</ul>
								<div class="filter-list w-1/3 pl-4">
									<div
										class="form-filter-chips flex w-full flex-col"
										style="margin-bottom: 0.5rem;"
									>
										{#each SIDEBAR_FORM_CATEGORIES as category}
											{@const isSelected = sidebarFormCategory === category}
											<button
												class="form-chip"
												style="white-space: normal; word-break: break-word;"
												class:selected={isSelected}
												onclick={() => (sidebarFormCategory = isSelected ? '' : category)}
											>
												{category}
											</button>
										{/each}
									</div>
								</div>
							</div>
							<hr />
							<div>
								<div class="border-top mt-2 mb-2 flex items-center justify-between">
									<label for="drug-list" class="text-lg">Selected:</label>
								</div>
								<ul class="selected-list" role="listbox">
									{#each selectedDrugsWithData as item, index}
										{@const color =
											drugColors[selectedRxcuis.indexOf(item.rxcui) % drugColors.length]}
										{@const price = getMostRecentPrice(item)}
										<li
											class="selected-list-item"
											onclick={() => toggleDrugSelection(item.rxcui, item.friendlyName)}
											onkeydown={(e) => {
												if (e.key === 'Enter' || e.key === ' ')
													toggleDrugSelection(item.rxcui, item.friendlyName);
											}}
											role="option"
											aria-selected={true}
											tabindex="0"
											style="border-left: 4px solid {color}; background-color: {color}70;"
										>
											<span class="checkmark">✕</span>
											<span class="drug-name">{item.friendlyName.toUpperCase()}</span>
											<span class="drug-price">${price.toFixed(2)}</span>
										</li>
									{/each}
								</ul>
							</div>
						</div>
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

	.form-filter-chips {
		display: flex;
		flex-wrap: nowrap;
		gap: 0.5rem;
		border-bottom: 1px solid #ccc;
		margin-bottom: 1rem;
		margin-top: 1rem;
		width: 100%;
		box-sizing: border-box;
		overflow-x: auto;
	}

	.form-chip {
		font-family: fustat;
		padding: 0.45rem 0.65rem;
		border: 1px solid #ccc;
		background-color: rgba(75, 75, 75, 0.1);
		cursor: pointer;
		border-radius: 20px;
		font-size: 0.8em;
		transition: all 0.2s;
		white-space: nowrap;
		text-align: center;
		flex-shrink: 0;
	}

	.form-chip:hover {
		background-color: rgba(75, 75, 75, 0.2);
		border-color: #999;
	}

	.form-chip.selected {
		background-color: #2d6a4f;
		color: white;
		border-color: #2d6a4f;
		font-weight: 600;
	}

	.selected-count {
		color: #2d6a4f;
		font-weight: 600;
	}

	.drug-list-item.loading {
		opacity: 0.7;
	}

	.spinner {
		display: inline-block;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	.search-bar {
		position: relative;
		margin-bottom: 0.5rem;
	}

	.search-input {
		width: 100%;
		padding: 0.6rem 2rem 0.6rem 0.75rem;
		border: 1px solid #ccc;
		border-radius: 6px;
		font-family: fustat;
		font-size: 0.95em;
		background-color: rgba(75, 75, 75, 0.05);
		box-sizing: border-box;
	}

	.search-input:focus {
		outline: none;
		border-color: #2d6a4f;
		box-shadow: 0 0 0 2px rgba(45, 106, 79, 0.2);
	}

	.search-input::placeholder {
		color: #999;
	}

	.clear-search {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		background: none;
		border: none;
		cursor: pointer;
		font-size: 1rem;
		color: #666;
		padding: 0.25rem;
		line-height: 1;
	}

	.clear-search:hover {
		color: #333;
	}

	.drug-count {
		font-family: fustat;
		font-size: 0.85em;
		color: #666;
		text-align: center;
	}

	.drug-selection-section {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0px;
		max-height: 800px;
		overflow: hidden;
	}

	.drug-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		border: 1px solid rgba(128, 128, 128, 0.5);
		border-radius: 4px;
		flex: 1;
		overflow-y: auto;
		min-height: 0px;
		max-height: 400px;
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
		outline: 1px solid #54707c;
		outline-offset: -2px;
	}

	.selected-list {
		list-style: none;
		padding: 0;
		margin: 10px 0;
		border: 1px solid rgba(128, 128, 128, 0.5);
		border-radius: 4px;
		flex: 1;
		overflow-y: auto;
		min-height: 0px;
		max-height: 150px;
	}

	.selected-list-item {
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

	.selected-list-item .drug-name {
		flex: 1;
	}

	.selected-list-item .drug-price {
		margin-left: auto;
		font-weight: 600;
		font-size: 0.9em;
	}

	.selected-list-item:hover {
		background-color: rgba(128, 128, 128, 0.15);
	}

	.selected-list-item:focus {
		outline: 1px solid #54707c;
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
		padding: 0;
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
		position: relative;
	}

	.side-bar {
		padding: 10px 10px 10px 20px;
		width: 35%;
		display: flex;
		flex-direction: column;
		border-left: 1px solid #ccc;
		min-height: 0;
		max-height: 100%;
		overflow: hidden;
	}

	.controls {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
		overflow: hidden;
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
		font-size: 14px;
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
