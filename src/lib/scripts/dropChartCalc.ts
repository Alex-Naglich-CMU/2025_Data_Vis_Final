import type { DrugData } from './types';

// Highlighted drug keywords
export const highlightedKeywords = [
	'Asmanex',
	'Advair',
	'Symbicort',
	'Humalog',
	'Humalin',
	'Novalog',
	'Cialis',
	'Victoza',
	'Diclegis',
	'Focalin',
	'Latisse',
	'Kloxxado',
	'Maxidex',
	'Lamictal',
	'Levemir',
	'Lantus',
	'Lastacaft',
	'Klor',
	'Procrit',
	'Nascobal',
	'Pred',
	'Narcan',
	'Novolog',
	'Novolin',
	'Olopatadine',
	'Pradaxa',
	'Pataday',
	'Prozac',
	'Protonix',
	'Pylera',
	'Vigamox',
	'Valtrex'
];

export const sampleSize = 300;

// Parse date from MM/DD/YYYY
export function parseDate(dateStr: string): Date | null {
	try {
		const parts = dateStr.split('/');
		if (parts.length === 3) {
			const month = parseInt(parts[0]) - 1;
			const day = parseInt(parts[1]);
			const year = parseInt(parts[2]);
			return new Date(year, month, day);
		}
	} catch (e) {
		return null;
	}
	return null;
}

// Sample drugs for display
export function sampleDrugs(allDrugs: DrugData[], sampleSize: number): DrugData[] {
	// first, get all highlighted drugs
	const highlighted = allDrugs.filter((d) => d.isHighlighted);

	if (allDrugs.length <= sampleSize) {
		return allDrugs;
	}

	// start with ALL highlighted drugs
	const sampled: DrugData[] = [...highlighted];

	// fill the rest with stratified sampling from non-highlighted drugs
	const nonHighlighted = allDrugs.filter((d) => !d.isHighlighted);
	const sorted = nonHighlighted.sort((a, b) => {
		const aLast = a.prices[a.prices.length - 1].price;
		const bLast = b.prices[b.prices.length - 1].price;
		return aLast - bLast;
	});

	const remaining = sampleSize - sampled.length;
	const step = Math.floor(sorted.length / remaining);

	for (let i = 0; i < sorted.length && sampled.length < sampleSize; i += step) {
		sampled.push(sorted[i]);
	}

	return sampled;
}

// Load all drug data (async, expects searchIndex and import function)
export async function loadAllDrugData(
	searchIndex: any,
	importPrice: (rxcui: string) => Promise<any>
): Promise<DrugData[]> {
	const drugs: DrugData[] = [];
	let processed = 0;
	const totalEntries = Object.keys(searchIndex).length;

	for (const [rxcui, data] of Object.entries(searchIndex)) {
		processed++;
		if (processed % 500 === 0) {
			console.log(`loading ${processed}/${totalEntries} drugs...`);
		}

		const drugData = data as any;

		try {
			const priceModule = await importPrice(rxcui);
			const priceData = priceModule.default;

			if (!priceData.prices || Object.keys(priceData.prices).length === 0) {
				continue;
			}

			const pricePoints: { date: Date; price: number }[] = [];

			for (const ndc in priceData.prices) {
				for (const [dateStr, price] of Object.entries(priceData.prices[ndc])) {
					const date = parseDate(dateStr);
					if (!date || date.getFullYear() < 2017) continue;

					const priceNum = price as number;
					if (!priceNum || priceNum <= 0) continue;

					pricePoints.push({ date, price: priceNum });
				}
			}

			if (pricePoints.length === 0) continue;

			pricePoints.sort((a, b) => a.date.getTime() - b.date.getTime());

			const firstPrice = pricePoints[0].price;
			const lastPrice = pricePoints[pricePoints.length - 1].price;
			const percentChange = ((lastPrice - firstPrice) / firstPrice) * 100;

			let color: string;
			if (percentChange > 1) {
				color = '#355b75';
			} else if (percentChange < -1) {
				color = '#E74C3C';
			} else {
				color = '#9a2f1f';
			}

			// check if this drug is in the highlighted list AND has a drop in 2023-2024
			const drugName = drugData.name.toLowerCase();
			const matchesKeyword = highlightedKeywords.some(
				(keyword) =>
					drugName.startsWith(keyword.toLowerCase()) || drugName.includes(keyword.toLowerCase())
			);

			let isHighlighted = false;
			if (matchesKeyword) {
				// check for price drop between 2023-2024
				const prices2023 = pricePoints.filter((p) => p.date.getFullYear() === 2023);
				const prices2024 = pricePoints.filter((p) => p.date.getFullYear() === 2024);

				if (prices2023.length > 0 && prices2024.length > 0) {
					const avg2023 = prices2023.reduce((sum, p) => sum + p.price, 0) / prices2023.length;
					const avg2024 = prices2024.reduce((sum, p) => sum + p.price, 0) / prices2024.length;
					const dropPercent = ((avg2024 - avg2023) / avg2023) * 100;

					// only highlight if there's a significant drop (> 50%)
					if (dropPercent < -50) {
						isHighlighted = true;
					}
				}
			}

			drugs.push({
				rxcui,
				name: drugData.name,
				color,
				prices: pricePoints,
				isHighlighted
			});
		} catch (e) {
			// skip
		}
	}

	console.log(`loaded ${drugs.length} drugs with price data`);
	return drugs;
}
