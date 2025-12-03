import type {
	DrugAllData,
	SinglePriceDataPoint as SinglePriceDataPoint,
	AverageGenericPrice
} from '$lib/scripts/drug-types';

export function getPricesArray(drug: DrugAllData): SinglePriceDataPoint[] {
	if (!drug || !drug.prices) return [];

	const pricesArray: SinglePriceDataPoint[] = [];

	for (const [ndc, dates] of Object.entries(drug.prices)) {
		for (const [date, price] of Object.entries(dates)) {
			pricesArray.push({
				ndc,
				date,
				price,
				drugName: drug.friendlyName,
				rxcui: drug.rxcui,
				isBrand: drug.isBrand
			});
		}
	}

	pricesArray.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	return pricesArray;
}

// Helper to get average price per date
export function getAveragePrices(pricePoints: SinglePriceDataPoint[]): AverageGenericPrice[] {
	if (!pricePoints || pricePoints.length === 0) return [];

	// Map to hold prices for each unique date string
	const dateMap: { [date: string]: number[] } = {};

	// 💡 Iterate directly over the flat PricePoint array
	for (const point of pricePoints) {
		if (!dateMap[point.date]) {
			dateMap[point.date] = [];
		}
		// Use point.price from the flat array
		dateMap[point.date].push(point.price);
	}

	// Calculate averages (rest of logic is fine)
	const averages: AverageGenericPrice[] = Object.entries(dateMap).map(([date, prices]) => ({
		date,
		averagePrice: prices.reduce((sum, p) => sum + p, 0) / prices.length,
		count: prices.length
	}));

	averages.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	return averages;
}
