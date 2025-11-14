<script lang="ts">
    import type { PageProps } from './$types';
    import { asset } from '$app/paths';
    import { onMount } from 'svelte';
    import TimeSeriesComparison from '$lib/Time-Series-Comparison.svelte';

    // Type definitions
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

    const drugSearchTerms: Record<string, string> = {
        // LIPITOR (brand) / ATORVASTATIN (generic) - 40mg
        '617320': 'lipitor',           // Brand - LIPITOR 40 MG TABLET
        '617311': 'atorvastatin',      // Generic - ATORVASTATIN 40 MG TABLET
        
        // GLUCOPHAGE (brand) / METFORMIN (generic) - 500mg
        '861008': 'glucophage',        // Brand - GLUCOPHAGE 500 MG TABLET
        '861007': 'metformin',         // Generic - METFORMIN HCL 500 MG TABLET
        
        // VYVANSE (brand) / LISDEXAMFETAMINE (generic) - 20mg
        '854832': 'vyvanse',           // Brand - VYVANSE 20 MG CAPSULE
        '854830': 'lisdexamfetamine',  // Generic - LISDEXAMFETAMINE 20 MG CAPSULE
        
        // PROZAC (brand) / FLUOXETINE (generic) - 20mg
        '104849': 'prozac',            // Brand - PROZAC 20 MG PULVULE
        '310385': 'fluoxetine',        // Generic - FLUOXETINE HCL 20 MG CAPSULE
        
        // NORVASC (brand) / AMLODIPINE (generic) - 5mg
        '212549': 'norvasc',           // Brand - NORVASC 5 MG TABLET
        '197361': 'amlodipine',         // Generic - AMLODIPINE BESYLATE 5 MG TAB

        // ZOLOFT (brand) / SERTRALINE (generic) - 50mg
        '208161': 'zoloft',            // Brand - ZOLOFT 50 MG TABLET
        '312941': 'sertraline',         // Generic - SERTRALINE HCL 50 MG TABLET

         // LEXAPRO (brand) / ESCITALOPRAM (generic) - 10mg
        '352272': 'lexapro',           // Brand - LEXAPRO 10 MG TABLET
        '349332': 'escitalopram',       // Generic - ESCITALOPRAM 10 MG TABLET

        // LYRICA (brand) / PREGABALIN (generic) - 150mg
        '607020': 'lyrica',            // Brand - LYRICA 150 MG CAPSULE
        '483440': 'pregabalin'         // Generic - PREGABALIN 150 MG CAPSULE
    };

    let drugsData = $state<DrugData[]>([]);
    let loading = $state<boolean>(true);
    let error = $state<string | null>(null);

    onMount(async () => {
        try {
            // Load each drug file directly by RxCUI
            const rxcuis = Object.keys(drugSearchTerms);
            
            const loadPromises = rxcuis.map(async (rxcui): Promise<DrugData | null> => {
                try {
                    const response = await fetch(`/data/prices/${rxcui}.json`);
                    const data = await response.json();

                    // Transform nested prices into flat array
                    const pricesArray: PriceDataPoint[] = [];
                    
                    for (const [ndc, dates] of Object.entries(data.prices)) {
                        for (const [date, price] of Object.entries(dates as Record<string, number>)) {
                            pricesArray.push({
                                ndc,
                                date,
                                price: price * 30, //montly supply instead of per pill to align with how user purchases
                                drugName: data.Name,
                                rxcui: data.RxCUI,
                                isBrand: data.IsBrand
                            });
                        }
                    }

                    // Sort by date
                    pricesArray.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

                    return {
                        rxcui: data.RxCUI,
                        friendlyName: drugSearchTerms[rxcui],  // Use friendly name!
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
            drugsData = results.filter((drug): drug is DrugData => drug !== null);
            loading = false;
            
            console.log('Loaded drugs:', $state.snapshot(drugsData));
            
        } catch (err) {
            error = err instanceof Error ? err.message : 'Unknown error';
            loading = false;
            console.error('Error loading drug data:', err);
        }
    });

    let { data }: PageProps = $props();

    /* 
        DATA STRUCTURE
        
        drugsData = [
          {
            rxcui: "617319",
            friendlyName: "lipitor",           // Easy to read!
            fullName: "LIPITOR 10MG TABLET",   // Technical name
            isBrand: true,
            brandRxcui: "617319",
            genericRxcui: "83367",
            prices: [
              { ndc: "...", date: "2024-01-15", price: 125.50, ... },
              ...
            ]
          }
        ]
        
        USAGE:
        - Use drug.friendlyName for display ("lipitor")
        - Use drug.fullName for detailed info ("LIPITOR 10MG TABLET")
        - drug.prices is already a flat, sorted array
    */
</script>

<div class="title-holder">
    <div class="title">
        <h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
        <h2>What price can you expect on your next refill?</h2>

        <br>
        <br>
        <p>In the United States, brand-name drug prices have continued to rise, while generic drug prices have steadily declined. This interactive dashboard visualizes these trends over time. According to RAND, an independent public policy research organization, generics are the only category where U.S. prices are consistently lower than those in other countries, costing about 84% of the international average. Understanding this contrast makes it easier to see how pricing patterns affect affordability and policy decisions. Use the dashboard to select different drugs and compare how their prices change across brands, generics, and time.

        </p>
    </div>
    <div class="pillsImages"> 
        <img class="pillpics" src={asset('/images/pill01.png')} alt="red pill illustration"/>
        <img class="pillpics" src={asset('/images/pill02.png')} alt="blue pill illustration"/>
        <img class="pillpics" src={asset('/images/pill03.png')} alt="tan pill illustration"/>
    </div>
</div>

{#if loading}
    <div class="loading">
        <p>Loading drug data...</p>
    </div>
{:else if error}
    <div class="error">
        <p>Error loading data: {error}</p>
    </div>
{:else}
    <!-- <div class="drug-section">        
        {#if drugsData.length === 0}
            <p class="no-data">No drugs found. Check console for details.</p>
        {:else}
            <div class="drug-grid">
                {#each drugsData as drug}
                    <div class="drug-card">
                        <h4>{drug.friendlyName}</h4>
                        <p class="full-name">{drug.fullName}</p>
                        <p><strong>Type:</strong> {drug.isBrand ? 'Brand' : 'Generic'}</p>
                        <p><strong>Data Points:</strong> {drug.prices.length}</p>
                        
                        {#if drug.prices.length > 0}
                            <p class="price-info">
                                <span>First: ${drug.prices[0].price.toFixed(2)}</span>
                                <span>Latest: ${drug.prices[drug.prices.length - 1].price.toFixed(2)}</span>
                            </p>
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}
    </div> -->
{/if}

{#if !loading && !error && drugsData.length > 0}
    <TimeSeriesComparison {drugsData} />
{/if}

<style>
    * {
        font-family: Antonio;
    }

    h1 {
        font-size: 96px;
        font-weight: bold;
    }

    h2 {
        font-size: 40px;
        font-weight: bold;
    }

    h3 {
        font-family: fustat;
        font-size: 32px;
        font-weight: 700;
        text-transform: uppercase;
    }

    h4 {
        font-family: fustat;
        font-size: 20px;
        font-weight: 700;
        text-transform: uppercase;
    }

    h5 {
        font-family: fustat;
        font-size: 20px;
        font-weight: normal;
        text-transform: uppercase;
    }

    p {
        font-family: fustat;
        font-size: 16px;
        font-weight: normal;
    }

    .title-holder {
        padding: 40px 40px 40px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .title {
        max-width: 70%;
    }

    .headerTitle {
        margin-bottom: 60px;
    }

    .pillsImages {
        position: relative;
        width: 30%;
        display: flex;
        align-items: center;
    }

    .pillpics {
        position: absolute;
    }

    .loading, .error {
        padding: 2rem;
        text-align: center;
        font-family: fustat;
    }

    .error {
        color: red;
    }

    .drug-section {
        padding: 40px;
    }

    .no-data {
        text-align: center;
        padding: 2rem;
        color: #666;
    }

    .drug-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }

    .drug-card {
        border: 2px solid #333;
        padding: 1.5rem;
        border-radius: 12px;
        background: #f9f9f9;
        transition: transform 0.2s;
    }

    .drug-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .drug-card h4 {
        margin-top: 0;
        color: #333;
        margin-bottom: 0.5rem;
        text-transform: capitalize;
    }

    .full-name {
        font-size: 12px !important;
        color: #666;
        margin-bottom: 1rem !important;
    }

    .drug-card p {
        margin: 0.5rem 0;
        font-size: 14px;
    }

    .price-info {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #ddd;
        font-weight: 600;
    }
</style>

