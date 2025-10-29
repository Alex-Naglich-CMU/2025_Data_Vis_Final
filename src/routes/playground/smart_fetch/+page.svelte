<script lang="ts">
	// The core identifier for the NADAC Comparisons dataset
	const datasetId = 'a217613c-12bc-5137-8b3a-ada0e4dad1ff';
	// API reference: https://data.medicaid.gov/dataset/a217613c-12bc-5137-8b3a-ada0e4dad1ff#api

	///////////////// State and Utility Initialization //////////////////

	// State variables (using `any` for raw JSON)
	let metadata = $state<any | null>(null);
	let metadataDoc = $state<any | null>(null);
	let distributionExamples = $state<Record<string, unknown> | null>(null);
	let description = $state<any | null>(null);
	let data = $state<any | null>(null);

	// Derived/Extracted IDs and URLs
	let descriptionUrl = $state<string | null>(null);
	let distributionID = $state<string | null>(null);

	// AbortController to manage fetch requests and prevent race conditions
	let controller = new AbortController();
	const signal = controller.signal;

	///////////////// Utility Functions //////////////////

	// Helper function for fetching from APIs.
	const fetchData = async (url: string, signal: AbortSignal) => {
		try {
			const res = await fetch(url, { signal });
			if (!res.ok) {
				throw new Error(`HTTP error! status: ${res.status} from ${url}`);
			}
			return await res.json();
		} catch (error) {
			if (error instanceof Error && error.name === 'AbortError') {
				// Don't log aborts as errors
			} else {
				console.error('Error fetching data from:', url, error);
			}
			return null;
		}
	};

	///////////////// Data Loading Functions //////////////////

	/**
	 * Loads the main dataset metadata and description documents.
	 * Also extracts the required distribution ID (UUID).
	 */
	const loadDataSet = async (id: string) => {
		// Cancel previous requests before starting new ones
		controller.abort();
		controller = new AbortController(); // Create new controller for new requests
		const newSignal = controller.signal;

		try {
			// 1. Fetch main page metadata document (contains UUID examples)
			metadataDoc = await fetchData(
				`https://data.medicaid.gov/api/1/metastore/schemas/dataset/items/${id}/docs?`,
				newSignal
			);

			// 2. Fetch main metadata object (contains description URL)
			metadata = await fetchData(
				`https://data.medicaid.gov/api/1/metastore/schemas/dataset/items/${id}?`,
				newSignal
			);

			// Extract the description URL
			descriptionUrl = metadata?.distribution?.[0]?.describedBy || null;

			// Extract the UUIDs and take the first one (probably the only one)
			distributionExamples =
				metadataDoc?.components?.parameters?.datastoreDistributionUuid?.examples || null;
			distributionID = distributionExamples ? Object.keys(distributionExamples)[0] : null;

			// 3. Fetch the Description data using the extracted URL
			if (descriptionUrl) {
				description = await fetchData(descriptionUrl, newSignal);
			}
		} catch (error) {
			// Errors are handled and logged in fetchData
		}
	};

	
	//Fetches the actual data points for a given distribution ID 
	const loadDataPoints = async (distributionID: string) => {
		data = await fetchData(`https://data.medicaid.gov/api/1/datastore/query/${distributionID}`, signal);

		// // Calculate the size of the JSON response string
		// if (data) {
		// 	const jsonString = JSON.stringify(data, null, 2);

		// 	// Use TextEncoder for a proper byte count (handles multi-byte characters)
		// 	const estimatedSizeInBytes = new TextEncoder().encode(jsonString).length;

		// 	console.log(
		// 		`Fetched Data Size: ${estimatedSizeInBytes} bytes (${(
		// 			estimatedSizeInBytes / 1024
		// 		).toFixed(2)} KB)`
		// 	);
		// }
	};

	///////////////// Effects for Reactivity //////////////////

	// Effect to load dataset when the component initializes
	$effect(() => {
		// No need for 'if (datasetId)' since it's a constant
		loadDataSet(datasetId);
	});

	// Effect to load data points when distributionID is successfully extracted
	$effect(() => {
		if (distributionID) {
			loadDataPoints(distributionID);
		}
	});
</script>

<h1 class="mb-4 text-3xl font-bold">Fetch Data from Medicaid using API</h1>
<div class="mb-4 rounded bg-gray-100 p-3">
	<p><strong>Dataset ID:</strong> {datasetId}</p>
	<p><strong>Description URL:</strong> {descriptionUrl || 'Loading...'}</p>
	<p><strong>Distribution ID:</strong> {distributionID || 'Loading...'}</p>
</div>

<div class="flex space-x-4">
	{#each [metadataDoc, metadata, description, data] as doc}
		{#if doc === null}
			<p>Loading...</p>
		{/if}
		{#if doc !== null}
			<div class="flex-1 min-w-0">
				<h2 class="mb-2 text-xl font-semibold">
					{#if doc === metadataDoc}
						Metadata Document
					{:else if doc === metadata}
						Metadata
					{:else if doc === description}
						Description
					{:else if doc === data}
						Data Points
					{/if}
				</h2>
				<pre class="max-h-96 overflow-auto rounded border bg-white p-2">
					{JSON.stringify(doc, null, 2)}
				</pre>
			</div>
		{/if}		
	{/each}
</div>