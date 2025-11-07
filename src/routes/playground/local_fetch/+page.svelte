// Example SvelteKit function to fetch drug data
async function fetchDrugPrices(rxcui) {
    // Assuming your data files are hosted in a public 'data' folder
    const url = `/data/${rxcui}.json`; 
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch ${rxcui} data.`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching drug data:", error);
        return [];
    }
}