<script lang="ts">
	const datasetId = 'a217613c-12bc-5137-8b3a-ada0e4dad1ff';
	let response = $state<any>(null);
	let caseVal = $state(1);

	$effect(() => {
		response = null; // Reset response on case change
		let url = ''; // Initialize URL variable

		// Create AbortController instance to manage fetch requests without race conditions
		let controller = new AbortController();
		let signal = controller.signal;

		// Determine URL based on selected case
		switch (caseVal) {
			case 1:
				url = `https://data.medicaid.gov/api/1/metastore/schemas/dataset/items/${datasetId}`;
				break;
			case 2:
				url = `https://data.medicaid.gov/api/1/datastore/query/f4276775-1cf0-5252-bde3-1d66fc0acf5c`;
				break;
		}

		
		fetch(url, { signal })
			.then(async (res) => {	
				response = await res.json();
			});
	});
</script>

<h1 class="mb-4 text-3xl font-bold">Fetch Data from Medicare using API</h1>

<select name="case" bind:value={caseVal}>
	<option value={1}>Fetch Metadata</option>
	<option value={2}>Fetch Data</option>
</select>

<pre>
	{JSON.stringify(response, null, 2)}
</pre>
