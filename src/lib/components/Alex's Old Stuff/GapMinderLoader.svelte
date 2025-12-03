<script lang="ts">
	import GapMinderChart from '$lib/GapMinderChart.svelte';
	import * as d3 from 'd3';
	import comparison_map.json from '$lib/data/comparison_map.csv?url';

	const dataPromise = Promise.all(
		Object.entries(datasets).map(([name, url]) =>
			d3
				.csv(url, (d: any) => ({
					city: d.City,
					country: d.Country,
					mainPollutant: d['Main pollutant'],
					pm25: +d['PM2.5'],
					state: d.State,
					stationName: d['Station name'],
					timestamp: new Date(d['Timestamp(UTC)']),
					usAqi: +d['US AQI']
				}))
				.then((records) => [name, records])
		)
	).then((entries) => Object.fromEntries(entries));
</script>

{#await dataPromise}
	<p>loading data...</p>
{:then allData}
	<A3P2 data={allData} />
{:catch error}
	<p>Something went wrong: {error.message}</p>
{/await}