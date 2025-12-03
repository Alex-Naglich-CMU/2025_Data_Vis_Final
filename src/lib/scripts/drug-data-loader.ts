import type { DrugAllData, SinglePriceDataPoint } from './types';

// Vite glob import - this gets all JSON files ready for dynamic loading
const priceFiles = import.meta.glob('$lib/data/prices/*.json');

/**
 * Load drug price data for the given RxCUI codes
 * @param drugSearchTerms - Record mapping RxCUI codes to friendly names
 * @returns Promise of DrugAllData array
 */
export async function loadDrugData(
	drugSearchTerms: Record<string, string>
): Promise<DrugAllData[]> {
	const rxcuis = Object.keys(drugSearchTerms);

	const loadPromises = rxcuis.map(async (rxcui): Promise<DrugAllData | null> => {
		try {
			const filePath = `/src/lib/data/prices/${rxcui}.json`;
			const loader = priceFiles[filePath];

			if (!loader) {
				console.warn(`Price file not found for ${rxcui} (${drugSearchTerms[rxcui]})`);
				return null;
			}

			const priceModule = (await loader()) as any;
			const data = priceModule.default;

			const pricesArray: SinglePriceDataPoint[] = [];

			for (const [ndc, dates] of Object.entries(data.prices)) {
				for (const [date, price] of Object.entries(dates as Record<string, number>)) {
					pricesArray.push({
						ndc,
						date,
						price: price * 30,
						drugName: data.Name,
						rxcui: data.RxCUI,
						isBrand: data.IsBrand
					});
				}
			}

			pricesArray.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

			return {
				rxcui: data.RxCUI,
				friendlyName: drugSearchTerms[rxcui],
				fullName: data.Name,
				isBrand: data.IsBrand,
				brandRxcui: data.Brand_RxCUI,
				genericRxcui: data.Generic_RxCUI,
				prices: pricesArray
			};
		} catch (err) {
			console.warn(`Failed to load drug ${rxcui} (${drugSearchTerms[rxcui]}):`, err);
			return null;
		}
	});

	const results = await Promise.all(loadPromises);
	return results.filter((drug): drug is DrugAllData => drug !== null);
}
