
// Type definitions
import type { DrugPricesOnly, DrugAllData } from './drug-types';

interface SearchIndexEntry {
	rxcui: string;
	name: string;
	is_brand: boolean;
}

interface SearchIndex {
	[key: string]: SearchIndexEntry;
}

// List of drugs we want to visualize (partial names)
const drugSearchTerms: string[] = [
	'lipitor',
	'insulin',
	'synthroid',
	'metformin',
	'lisdexamfetamine',
	'fluoxetine',
	'isotretinoin',
	'amlodipine'
];

	let drugsData = $state<DrugAllData[]>([]);
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);

	try {
		// Load the search index
		const searchIndexResponse = await fetch('/data/search_index.json');
	const searchIndex: SearchIndex = await searchIndexResponse.json();

	console.log('Search index loaded:', Object.keys(searchIndex).slice(0, 10)); // Debug: show first 10 keys

	// For each drug search term, find matching drugs
	const loadPromises = drugSearchTerms.map(async (searchTerm): Promise<DrugAllData | null> => {
		const searchTermLower = searchTerm.toLowerCase();

		// Find drug by partial match in the search index
		let drugInfo: SearchIndexEntry | null = null;
		let matchedKey: string | null = null;

		for (const [key, value] of Object.entries(searchIndex)) {
			if (key.includes(searchTermLower)) {
				drugInfo = value;
				matchedKey = key;
				break; // Take first match
			}
		}

		if (!drugInfo) {
			console.warn(`Drug matching "${searchTerm}" not found in search index`);
			return null;
		}

		console.log(`Found match: "${searchTerm}" → "${matchedKey}"`);

		// Load the price JSON file
		const rxcui = drugInfo.rxcui;
		const priceResponse = await fetch(`/data/prices/${rxcui}.json`);
		const priceData = await priceResponse.json();

		return {
			searchName: searchTerm,
			...priceData
		} as DrugAllData;
	});

	// Wait for all drugs to load
	const results = await Promise.all(loadPromises);
	drugsData = results.filter((drug): drug is DrugAllData => drug !== null);
	loading = false;

	console.log('Loaded drugs:', $state.snapshot(drugsData)); // Use $state.snapshot for logging
} catch (err) {
	error = err instanceof Error ? err.message : 'Unknown error';
	loading = false;
	console.error('Error loading drug data:', err);
}
	
export {};