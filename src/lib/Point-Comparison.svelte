<script lang="ts">
	import * as d3 from 'd3';

    // TYPE DEFINITIONS
	interface PriceDataPoint {
		ndc: string;
		date: string;
		price: number;
		drugName: string;
		rxcui: string;
		isBrand: boolean;
	}

	interface DrugData {
		rxcui: string;
		friendlyName: string;
		fullName: string;
		isBrand: boolean;
		brandRxcui: string | null;
		genericRxcui: string | null;
		prices: PriceDataPoint[];
	}

    interface YearlyAverage {
		year: number;
		averagePrice: number;
		dataPoints: number;
	}

    interface DataPoint {
		rxcui: string;
		drugName: string;
		yearlyAverages: YearlyAverage[];
		firstDate: Date;
		timeSinceFirstDate: number;
	}

    // PROPS
	const { drugsData = [] }: { drugsData: DrugData[] } = $props();

    // CONSTANTS
	const width = 900;
	const height = 500;
	const margin = { top: 40, right: 40, bottom: 80, left: 80 };

	const colors = {
		red: '#9A2F1F',
		blue: '#54707C',
		green: '#3F5339',
		orange: '#DF7C39',
		tan: '#BFA97F',
		cream: '#F6F5EC'
	};

    //find average price per year & time it's been on market
   	const findYearAverage: DataPoint[] = $derived(
		drugsData.map((drug) => {
			// Calculate yearly averages
			const yearlyMap = d3.rollup(
				drug.prices,
				(prices) => d3.mean(prices, (d) => d.price) || 0,
				(d) => new Date(d.date).getFullYear()
			);

			const yearlyAverages: YearlyAverage[] = Array.from(yearlyMap, ([year, averagePrice]) => ({
				year,
				averagePrice,
				dataPoints: drug.prices.filter((p) => new Date(p.date).getFullYear() === year).length
			})).sort((a, b) => a.year - b.year);

			// Time on market calculations
			const firstDate = d3.min(drug.prices, (d) => new Date(d.date)) || new Date();
			const timeSinceFirstDate = (new Date().getTime() - firstDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25);

			return {
				rxcui: drug.rxcui,
				drugName: drug.friendlyName,
				yearlyAverages,
				firstDate,
				timeSinceFirstDate: Math.round(timeSinceFirstDate * 10) / 10
			};
		})
	);

	// Extract all unique years
	let years: Array<number> = $derived(
		Array.from(
			new Set(findYearAverage.flatMap((a) => a.yearlyAverages.map((ya) => ya.year)))
		).sort()
	);

</script>