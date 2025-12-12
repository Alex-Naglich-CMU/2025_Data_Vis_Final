// DrugData, smaller interface
export interface DrugData {
	rxcui: string;
	name: string;
	color: string;
	prices: { date: Date; price: number }[];
	isHighlighted: boolean;
}

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
	ingredientName: string;
	manufacturerName: string | null;
	strength: string | null;
	form: string | null;
	prices: SinglePriceDataPoint[];
}

// Individual price point with metadata
export interface SinglePriceDataPoint {
	ndc: string;
	date: string;
	price: number;
	drugName: string;
	rxcui: string;
	isBrand: boolean;
}

// Chart point with Date object (used in D3 visualizations)
export interface ChartPoint {
	date: Date;
	price: number;
}
