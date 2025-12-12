// This function replicates the final data calculation from IntroChart.svelte
import searchIndexAll from '$lib/data/search_index_all.json';

export function calculateIntroChartSummary() {
	let increased = 0;
	let decreased = 0;
	let stayedSame = 0;
	let total = 0;
	let increasedDollars = 0;
	let decreasedDollars = 0;
	let stayedSameDollars = 0;
	let totalDollars = 0;

	for (const [rxcui, data] of Object.entries(searchIndexAll)) {
		if (!('prices' in data)) continue;
		const pricesObj = (data as any).prices;
		let earliestDate: Date | null = null;
		let latestDate: Date | null = null;
		let firstPrice: number | null = null;
		let lastPrice: number | null = null;
		for (const ndc in pricesObj) {
			for (const [dateStr, price] of Object.entries(pricesObj[ndc])) {
				const parts = dateStr.split('/');
				if (parts.length === 3) {
					const month = parseInt(parts[0]) - 1;
					const day = parseInt(parts[1]);
					const year = parseInt(parts[2]);
					const date = new Date(year, month, day);
					if (!earliestDate || date < earliestDate) {
						earliestDate = date;
						firstPrice = typeof price === 'number' ? price : Number(price);
					}
					if (!latestDate || date > latestDate) {
						latestDate = date;
						lastPrice = typeof price === 'number' ? price : Number(price);
					}
				}
			}
		}
		if (firstPrice == null || lastPrice == null || isNaN(firstPrice) || isNaN(lastPrice)) continue;
		total++;
		const dollarChange = Math.abs(lastPrice - firstPrice);
		totalDollars += dollarChange;
		const percentChange = ((lastPrice - firstPrice) / firstPrice) * 100;
		if (percentChange > 1) {
			increased++;
			increasedDollars += dollarChange;
		} else if (percentChange < -1) {
			decreased++;
			decreasedDollars += dollarChange;
		} else {
			stayedSame++;
			stayedSameDollars += dollarChange;
		}
	}
	return {
		increased,
		decreased,
		stayedSame,
		total,
		increasedPct: total ? ((increased / total) * 100).toFixed(2) : '0.00',
		decreasedPct: total ? ((decreased / total) * 100).toFixed(2) : '0.00',
		stayedSamePct: total ? ((stayedSame / total) * 100).toFixed(2) : '0.00',
		increasedDollars,
		decreasedDollars,
		stayedSameDollars,
		totalDollars,
		increasedDollarsPct: totalDollars
			? ((increasedDollars / totalDollars) * 100).toFixed(2)
			: '0.00',
		decreasedDollarsPct: totalDollars
			? ((decreasedDollars / totalDollars) * 100).toFixed(2)
			: '0.00',
		stayedSameDollarsPct: totalDollars
			? ((stayedSameDollars / totalDollars) * 100).toFixed(2)
			: '0.00'
	};
}
