<script lang="ts">
    import type { PageProps } from './$types';
    import { asset } from '$app/paths';
    import { onMount } from 'svelte';
    import TimeSeriesComparison from '$lib/Time-Series-Comparison.svelte';
	import BackgroundInfo from '$lib/Background-Info.svelte';

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
        '483440': 'pregabalin',         // Generic - PREGABALIN 150 MG CAPSULE

        // LANTUS (brand) / INSULIN GLARGINE (generic) - 100 unit/ml vial
        '285018': 'lantus',              // Brand - LANTUS 100 UNIT/ML VIAL
        '311041': 'insulin glargine',    // Generic - INSULIN GLARGINE 100 UNIT/ML VIAL

        // PROVIGIL (brand) / MODAFINIL (generic) - 200mg
        '213471': 'provigil',          // Brand - PROVIGIL 200 MG TABLET
        '205324': 'modafinil'          // Generic - MODAFINIL 200 MG TABLET
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
        <h2>The state of drug pricing in America</h2>
    </div>
    <div class="pillsImages"> 
        <img class="pillpics" src={asset('/images/pill01.png')} alt="red pill illustration"/>
        <img class="pillpics" src={asset('/images/pill02.png')} alt="blue pill illustration"/>
        <img class="pillpics" src={asset('/images/pill03.png')} alt="tan pill illustration"/>
    </div>
</div>

<div class='intro-holder'>
    <p>
        Prescription drug use is at an all-time high in the United States, due to increases 
        in medicalization, population aging, and growing rates of diagnoses of chronic diseases. According to 
        <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC10656114/" target="_blank" rel="noopener noreferrer">a 2023 study</a>, a 
        person born today could expect to take prescription medications for roughly half of their life.
    </p>
    <br>    
    <p>
        At the same time, everyone in the US seems to agree that <b>the current cost of prescription medications is too high.</b>
        Just look at the sample of news articles from this year alone ↓
    </p>
</div>



<div class='news-holder'>
    <h4 class='section-title'>Explore recent headlines:</h4>
    <BackgroundInfo />
</div>

<div class='insulin-graphic-intro'>
    <h3>How high are they really?</h3>
    <br>
    <p>
        What's causing drug prices to be so high? Does this public perception reflect the actual price trends? 
    </p>
</div>

<div class='chart-intro'>
    <p> 
        In the United States, brand-name drug prices have continued to rise, while generic drug prices have steadily declined. 
        This interactive dashboard visualizes these trends over time. According to <a href="https://www.rand.org/news/press/2021/01/28.html" target="_blank" rel="noopener noreferrer">RAND</a>, an independent public policy research organization, 
        generics are the only category where U.S. prices are consistently lower than those in other countries, costing about 84% of the international
        average. Understanding this contrast makes it easier to see how pricing patterns affect affordability and policy decisions. Use the dashboard 
        to select different drugs and compare how their prices change across brands, generics, and time.
    </p>
</div>



{#if loading}
    <div class="loading">
        <p>Loading drug data...</p>
    </div>
{:else if error}
    <div class="error">
        <p>Error loading data: {error}</p>
    </div>
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
        font-family: antonio;
        font-size: 32px;
        font-weight: bold;
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

    p a {
        font-family: fustat;
        font-size: 16px;
        font-weight: normal;    
        color: inherit; 
        text-decoration: underline;
    }

    p b {
        font-family: fustat;
        font-size: 16px;
        font-weight: bold;  
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
        height: 300px;
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

    .section-title {
        margin-bottom: 20px;
    }

    .intro-holder {
        margin-left: 40px;
        margin-bottom: 40px;
        max-width: 750px;
    }

    .news-holder {
        margin-left: 40px;
        margin-bottom: 100px;
        max-width: 750px;
    }

    .insulin-graphic-intro {
        margin-left: 40px;
        margin-bottom: 40px;
        max-width: 750px;
    }

    .chart-intro {
        margin-left: 40px;
        max-width: 750px;
    }

</style>

