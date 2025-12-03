import type { DrugData, PricePoint, AveragePrice } from '$lib/scripts/drug-types';

export function getPricesArray(drug: DrugData): PricePoint[] {
	if (!drug || !drug.prices) return [];

	const pricesArray: PricePoint[] = [];

	for (const [ndc, dates] of Object.entries(drug.prices)) {
		for (const [date, price] of Object.entries(dates)) {
			pricesArray.push({
				ndc,
				date,
				price,
				drugName: drug.Name,
				rxcui: drug.RxCUI,
				isBrand: drug.IsBrand
			});
		}
	}

	pricesArray.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	return pricesArray;
}

// Helper to get average price per date
export function getAveragePrices(pricePoints: PricePoint[]): AveragePrice[] {
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
	const averages: AveragePrice[] = Object.entries(dateMap).map(([date, prices]) => ({
		date,
		averagePrice: prices.reduce((sum, p) => sum + p, 0) / prices.length,
		count: prices.length
	}));

	averages.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	return averages;
}
