// Type definitions

// Price data organized by NDC and date
export interface DrugPricesOnly {
	[ndc: string]: {
		[date: string]: number;
	};
}

export interface DrugAllData {
	rxcui: string;
	friendlyName: string;
	fullName: string;
	isBrand: boolean;
	brandRxcui: string | null;
	genericRxcui: string | null;
	prices: SinglePriceDataPoint[];
}

// TYPE DEFINITIONS
export interface SinglePriceDataPoint {
	ndc: string;
	date: string;
	price: number;
	drugName: string;
	rxcui: string;
	isBrand: boolean;
}

// Chart point with Date object (used in visualizations)
export interface ChartPoint {
	date: Date;
	price: number;
}

// Tooltip data for price comparisons
export interface TooltipData {
	date: Date;
	brandPrice?: number;
	genericPrice?: number;
	savings?: number;
	savingsPercent?: number;
}

export interface AverageGenericPrice {
	date: string;
	averagePrice: number;
	count: number;
}

// export interface PlottablePricePoint {
// 	ndc: string;
// 	date: Date;
// 	price: number;
// 	drugName: string;
// 	rxcui: string;
// 	isBrand: boolean;
// }

// export interface PlottableAveragePrice {
// 	date: Date;
// 	averagePrice: number;
// 	count: number;
// }
