import type { DrugAllData, ChartPoint } from '$lib/scripts/types';

// Get chart-ready data points with averaged prices per date
// Takes a drug and returns D3-friendly data with Date objects
// Averages all NDC prices for each unique date in the dataset
export function getChartPoints(drug: DrugAllData | null): ChartPoint[] {
	if (!drug || !drug.prices) return [];

	// Group prices by date
	const dateMap: { [date: string]: number[] } = {};

	for (const point of drug.prices) {
		if (!dateMap[point.date]) {
			dateMap[point.date] = [];
		}
		dateMap[point.date].push(point.price);
	}

	// Calculate average for each date and convert to Date objects
	const chartPoints: ChartPoint[] = Object.entries(dateMap).map(([dateStr, prices]) => ({
		date: new Date(dateStr),
		price: prices.reduce((sum, p) => sum + p, 0) / prices.length
	}));

	// Sort chronologically
	chartPoints.sort((a, b) => a.date.getTime() - b.date.getTime());
	return chartPoints;
}
