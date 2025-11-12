// Type definitions
export interface DrugPrices {
	[ndc: string]: {
		[date: string]: number;
	};
}

export interface DrugData {
	RxCUI: string;
	Name: string;
	IsBrand: boolean;
	Brand_RxCUI: string | null;
	Generic_RxCUI: string | null;
	prices: DrugPrices;
}

export interface PricePoint {
	ndc: string;
	date: string;
	price: number;
	drugName: string;
	rxcui: string;
	isBrand: boolean;
}

export interface PlottablePricePoint {
	ndc: string;
	date: Date;
	price: number;
	drugName: string;
	rxcui: string;
	isBrand: boolean;
}

export interface AveragePrice {
	date: string;
	averagePrice: number;
	count: number;
}

export interface PlottableAveragePrice {
	date: Date;
	averagePrice: number;
	count: number;
}
