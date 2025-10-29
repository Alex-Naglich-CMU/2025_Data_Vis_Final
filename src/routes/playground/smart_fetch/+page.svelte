<script lang="ts">
	// The core identifier for the NADAC Comparisons dataset
	const datasetId = 'a217613c-12bc-5137-8b3a-ada0e4dad1ff';
	// API reference: https://data.medicaid.gov/dataset/a217613c-12bc-5137-8b3a-ada0e4dad1ff#api
	// NDC code to filter data points
	const ndcFilterValue = $state('65862069030');

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
	const fetchData = async (
		url: string,
		signal: AbortSignal,
		method: string = 'GET',
		body: any = null
	) => {
		const options: RequestInit = {
			signal,
			method: method
		};

		if (body) {
			options.headers = { 'Content-Type': 'application/json' };
			options.body = JSON.stringify(body);
		}

		try {
			const res = await fetch(url, options);
			if (!res.ok) {
				throw new Error(`HTTP error! status: ${res.status} from ${url}`);
			}
			return await res.json();
		} catch (error) {
			// ... (error handling remains the same) ...
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
		const dataController = new AbortController();
		const dataSignal = dataController.signal;

		// Use the confirmed URL structure: /datastore/query/{datasetId}/{index}
		const url = `https://data.medicaid.gov/api/1/datastore/query/${datasetId}/0`;

		// Use the JSON request body structure for filtering and limiting
		const requestBody = {
			conditions: [
				{
					property: 'ndc',
					value: ndcFilterValue,
					operator: '=' // Exact match
				}
			]
		};

		const responseData = await fetchData(
			url,
			dataSignal,
			'POST', // Specify POST method
			requestBody
		);

		// Extract the array from the confirmed "results" wrapper
		if (responseData && responseData.results && Array.isArray(responseData.results)) {
			data = responseData.results;
		} else {
			data = responseData || null;
		}
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

	let docTitles = {
		metaData: { name: 'Metadata', file: 'metadata' },
		metadataDoc: { name: 'Metadata Document', file: 'metadataDoc' },
		description: { name: 'Description', file: 'description' },
		data: { name: 'Data Points', file: 'data' }
	};
	let currentDoc = $state('data');

	function getCurrentDocData() {
		// Use the val stored in currentDoc to determine which variable to return
		switch (currentDoc) {
			case 'metaData':
				return metadata;
			case 'metadataDoc':
				return metadataDoc;
			case 'description':
				return description;
			case 'data':
				return data;
			default:
				return null;
		}
	}



</script>

<h1 class="mb-4 text-3xl font-bold">Fetch Data from Medicaid using API</h1>
<div class="mb-4 rounded bg-gray-100 p-3">
	<p><strong>Dataset ID:</strong> {datasetId}</p>
	<p><strong>Description URL:</strong> {descriptionUrl || 'Loading...'}</p>
	<p><strong>Distribution ID:</strong> {distributionID || 'Loading...'}</p>
</div>

<select name="documents" id="documents" bind:value={currentDoc} class="select-bordered select mb-4">
	{#each Object.entries(docTitles) as [key, store]}
		<option value={key}>{store.name}</option>
	{/each}
</select>

<div class="flex space-x-4">
	<pre class="max-h-[500px] w-full overflow-auto rounded border bg-white p-4">
		{JSON.stringify(getCurrentDocData(), null, 2)}
	</pre>
</div>
