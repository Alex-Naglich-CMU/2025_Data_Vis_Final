import { loadDrugData } from '$lib/scripts/drug-data-loader';

export interface InflationCalcResult {
    oldPrice: number;
    newPrice: number;
    oldYear: number;
    newYear: number;
    actualDollarChange: number;
    actualPercentChange: number;
    inflationAdjustedPrice: number;
    inflationPercentChange: number;
    differenceVsInflationDollars: number;
    differenceVsInflationPercent: number;   
}

export const inflationCalc = async (rxcui: string) => {
	try {
		const drugDataArray = await loadDrugData({ [rxcui]: '' });
		const drugData = drugDataArray[0];

		if (!drugData || drugData.prices.length === 0) {
			return {
				oldPrice: 0,
				newPrice: 0,
				oldYear: 2018,
				newYear: 2025,
				// Actual change
				actualDollarChange: 0,
				actualPercentChange: 0,
				// Inflation-adjusted
				inflationAdjustedPrice: 0,
				inflationPercentChange: 0,
				// Difference: actual vs inflation
				differenceVsInflationDollars: 0,
				differenceVsInflationPercent: 0
			};
		}

        // Original price points and dates
		const oldPrice = drugData.prices[0].price;
		const newPrice = drugData.prices[drugData.prices.length - 1].price;
		const oldYear = new Date(drugData.prices[0].date).getFullYear();
		const newYear = new Date(drugData.prices[drugData.prices.length - 1].date).getFullYear();

		// How much time has passed
		const startDate = new Date(drugData.prices[0].date);
		const endDate = new Date(drugData.prices[drugData.prices.length - 1].date);
		const years = (endDate.getTime() - startDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);

		// What the price SHOULD be
		const inflationRate = 0.03;
		const inflationAdjustedPrice = oldPrice * Math.pow(1 + inflationRate, years);

		// Actual price change
		const actualDollarChange = newPrice - oldPrice;
		const actualPercentChange = oldPrice > 0 ? ((newPrice - oldPrice) / oldPrice) * 100 : 0;

		// Inflation predicted price change
		const inflationPercentChange =
			oldPrice > 0 ? ((inflationAdjustedPrice - oldPrice) / oldPrice) * 100 : 0;

		// Difference between actual final price inflation final price
		const differenceVsInflationDollars = newPrice - inflationAdjustedPrice;
		const differenceVsInflationPercent =
			inflationAdjustedPrice > 0
				? ((newPrice - inflationAdjustedPrice) / inflationAdjustedPrice) * 100
				: 0;

		return {
			oldPrice: Math.round(oldPrice * 100) / 100, // Round to 2 decimal places, cents
			newPrice: Math.round(newPrice * 100) / 100, // Round to 2 decimal places, cents
			oldYear,
			newYear,
			actualDollarChange: Math.round(actualDollarChange * 100) / 100, // Round to 2 decimal places, cents
			actualPercentChange: Math.round(actualPercentChange * 10) / 10, // Round to 1 decimal place, tenths of a percent
			inflationAdjustedPrice: Math.round(inflationAdjustedPrice * 100) / 100, // Round to 2 decimal places, cents
			inflationPercentChange: Math.round(inflationPercentChange * 10) / 10, // Round to 1 decimal place, tenths of a percent
			differenceVsInflationDollars: Math.round(differenceVsInflationDollars * 100) / 100, // Round to 2 decimal places, cents
			differenceVsInflationPercent: Math.round(differenceVsInflationPercent * 10) / 10 // Round to 1 decimal place, tenths of a percent
		};
	} catch (err) {
		console.error('Error loading data:', err);
		return {
			oldPrice: 0,
			newPrice: 0,
			oldYear: 2018,
			newYear: 2025,
			actualDollarChange: 0,
			actualPercentChange: 0,
			inflationAdjustedPrice: 0,
			inflationPercentChange: 0,
			differenceVsInflationDollars: 0,
			differenceVsInflationPercent: 0
		};
	}
};
