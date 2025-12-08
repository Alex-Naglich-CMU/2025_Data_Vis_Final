<script lang="ts">
    import * as d3 from 'd3';
    import { onMount } from 'svelte';

    interface DrugData {
        rxcui: string;
        name: string;
        color: string;
        prices: { date: Date; price: number }[];
        isHighlighted: boolean;
    }

    let loading = $state(true);
    let error = $state<string | null>(null);
    let searchIndex = $state<any>({});
    let allDrugs = $state<DrugData[]>([]);
    let displayedDrugs = $state<DrugData[]>([]);
    let currentStage = $state(3); // Start at step 3

    const sampleSize = 300;

    // Highlighted drug keywords
    const highlightedKeywords = [
        'Asmanex', 'Advair', 'Symbicort', 'Humalog', 'Humalin', 'Novalog', 'Cialis',
        'Victoza', 'Diclegis', 'Focalin', 'Latisse', 'Kloxxado', 'Maxidex', 'Lamictal',
        'Levemir', 'Lantus', 'Lastacaft', 'Klor', 'Procrit', 'Nascobal', 'Pred',
        'Narcan', 'Novolog', 'Novolin', 'Olopatadine', 'Pradaxa', 'Pataday', 'Prozac',
        'Protonix', 'Pylera', 'Vigamox', 'Valtrex'
    ];

    // SVG dimensions
    const width = 1200;
    const height = 600;
    const margin = { top: 40, right: 40, bottom: 60, left: 80 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    let svgRef: SVGSVGElement;

    onMount(async () => {
        try {
            const searchIndexModule = await import('$lib/data/search_index_all.json');
            searchIndex = searchIndexModule.default;
            console.log('loading data for', Object.keys(searchIndex).length, 'drugs...');

            await loadAllDrugData();
            
            // Auto-initialize to step 3
            setTimeout(() => {
                initializeChart();
                setTimeout(() => {
                    showHighlightedOnly();
                    setTimeout(() => {
                        addAnnotation();
                    }, 100);
                }, 100);
            }, 100);
            
            loading = false;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Unknown error';
            loading = false;
            console.error('error loading data:', err);
        }
    });

    async function loadAllDrugData() {
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
                const priceModule = await import(`$lib/data/prices/${rxcui}.json`);
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
                    color = '#4A90E2';
                } else if (percentChange < -1) {
                    color = '#E74C3C';
                } else {
                    color = '#95A5A6';
                }

                // Check if this drug is in the highlighted list AND has a drop in 2023-2024
                const drugName = drugData.name.toLowerCase();
                const matchesKeyword = highlightedKeywords.some(keyword => 
                    drugName.startsWith(keyword.toLowerCase()) || 
                    drugName.includes(keyword.toLowerCase())
                );

                let isHighlighted = false;
                if (matchesKeyword) {
                    // Check for price drop between 2023-2024
                    const prices2023 = pricePoints.filter(p => p.date.getFullYear() === 2023);
                    const prices2024 = pricePoints.filter(p => p.date.getFullYear() === 2024);
                    
                    if (prices2023.length > 0 && prices2024.length > 0) {
                        const avg2023 = prices2023.reduce((sum, p) => sum + p.price, 0) / prices2023.length;
                        const avg2024 = prices2024.reduce((sum, p) => sum + p.price, 0) / prices2024.length;
                        const dropPercent = ((avg2024 - avg2023) / avg2023) * 100;
                        
                        // only highlight if there's a significant drop (> 10%)
                        if (dropPercent < -50) {
                            isHighlighted = true;
                            console.log(`Found highlighted drug with drop: ${drugData.name} (${dropPercent.toFixed(1)}% drop)`);
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
        allDrugs = drugs;
        
        // sample drugs for display
        sampleDrugs();
    }

    function sampleDrugs() {
        // first, get all highlighted drugs
        const highlighted = allDrugs.filter(d => d.isHighlighted);
        console.log(`Found ${highlighted.length} highlighted drugs in total dataset`);
        
        if (allDrugs.length <= sampleSize) {
            displayedDrugs = allDrugs;
            return;
        }

        // start with ALL highlighted drugs
        const sampled: DrugData[] = [...highlighted];
        
        // fill the rest with stratified sampling from non-highlighted drugs
        const nonHighlighted = allDrugs.filter(d => !d.isHighlighted);
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

        displayedDrugs = sampled;
        console.log(`displaying ${displayedDrugs.length} drugs (${highlighted.length} highlighted + ${displayedDrugs.length - highlighted.length} others)`);
    }

    function parseDate(dateStr: string): Date | null {
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

    function generateLogTicks(min: number, max: number): number[] {
        const ticks: number[] = [];
        
        // only use powers of 10 - NO intermediate values
        let magnitude = Math.floor(Math.log10(min));
        const maxMagnitude = Math.ceil(Math.log10(max)) + 1;
        
        while (magnitude <= maxMagnitude) {
            const tick = Math.pow(10, magnitude);
            if (tick >= min * 0.5 && tick <= max * 2) {
                ticks.push(tick);
            }
            magnitude++;
        }
        
        // remove the first tick if there are multiple ticks to prevent overlap at bottom
        if (ticks.length > 1) {
            ticks.shift();
        }
        
        return ticks;
    }

    function initializeChart() {
        if (displayedDrugs.length === 0) return;

        currentStage = 0;

        const svg = d3.select(svgRef);
        svg.selectAll('*').remove();

        const g = svg.append('g')
            .attr('class', 'chart-group')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // find price range
        let minPrice = Infinity;
        let maxPrice = -Infinity;
        
        displayedDrugs.forEach(drug => {
            drug.prices.forEach(p => {
                if (p.price > 0) {
                    minPrice = Math.min(minPrice, p.price);
                    maxPrice = Math.max(maxPrice, p.price);
                }
            });
        });

        console.log('price range:', minPrice, 'to', maxPrice);

        // time extent
        const allDates = displayedDrugs.flatMap(d => d.prices.map(p => p.date));
        const minDate = d3.min(allDates) || new Date(2017, 0, 1);
        const maxDate = d3.max(allDates) || new Date(2025, 11, 31);

        // scales
        const xScale = d3.scaleTime()
            .domain([minDate, maxDate])
            .range([0, chartWidth]);

        const yScale = d3.scaleLog()
            .domain([Math.max(0.01, minPrice * 0.5), maxPrice * 1.2])
            .range([chartHeight, 0])
            .clamp(true);

        // axes
        const xAxis = d3.axisBottom(xScale).ticks(8);
        const tickValues = generateLogTicks(minPrice, maxPrice);
        
        const yAxis = d3.axisLeft(yScale)
            .tickValues(tickValues)
            .tickFormat((d) => {
                const num = d as number;
                if (num >= 1) return `$${num}`;
                return `$${num.toFixed(2)}`;
            });

        const xAxisG = g.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${chartHeight})`)
            .call(xAxis);

        const yAxisG = g.append('g')
            .attr('class', 'y-axis')
            .call(yAxis);

        // axis labels
        xAxisG.append('text')
            .attr('x', chartWidth / 2)
            .attr('y', 45)
            .attr('fill', 'black')
            .attr('font-size', '14px')
            .attr('font-family', 'Antonio')
            .attr('text-anchor', 'middle')
            .text('Year');

        yAxisG.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -chartHeight / 2)
            .attr('y', -55)
            .attr('fill', 'black')
            .attr('font-size', '14px')
            .attr('font-family', 'Antonio')
            .attr('text-anchor', 'middle')
            .text('Price per Unit ($)');

        // line generator
        const lineGenerator = d3.line<{ date: Date; price: number }>()
            .defined((d) => d.price > 0)
            .x((d) => xScale(d.date))
            .y((d) => yScale(d.price));

        // draw lines - VERY LOW OPACITY FOR 300 DRUGS
        g.selectAll('.drug-line')
            .data(displayedDrugs)
            .enter()
            .append('path')
            .attr('class', 'drug-line')
            .attr('fill', 'none')
            .attr('stroke', (d) => d.color)
            .attr('stroke-width', 0.3)
            .attr('opacity', 0.95)
            .attr('d', (d) => lineGenerator(d.prices));

        console.log(`Drew ${displayedDrugs.length} lines`);

        currentStage = 1;
    }

    function showHighlightedOnly() {
        if (currentStage < 1) return;

        const svg = d3.select(svgRef);
        const lines = svg.selectAll('.drug-line');

        const highlightedCount = displayedDrugs.filter(d => d.isHighlighted).length;
        console.log(`Highlighting ${highlightedCount} drugs out of ${displayedDrugs.length}`);

        lines.transition()
            .duration(1000)
            .attr('opacity', (d: any) => d.isHighlighted ? 0.75 : 0)
            .attr('stroke-width', (d: any) => d.isHighlighted ? 1 : 0.3);

        currentStage = 2;
    }

    function addAnnotation() {
        if (currentStage < 2) return;

        const svg = d3.select(svgRef);
        const g = svg.select('.chart-group');

        // calculate actual position of highlighted drugs in 2024
        const highlightedDrugs = displayedDrugs.filter(d => d.isHighlighted);
        
        // get prices in 2024 for highlighted drugs
        let totalPrice = 0;
        let count = 0;
        const targetDate = new Date(2024, 0, 1); // early 2024
        
        highlightedDrugs.forEach(drug => {
            const prices2024 = drug.prices.filter(p => p.date.getFullYear() === 2024);
            if (prices2024.length > 0) {
                const avgPrice = prices2024.reduce((sum, p) => sum + p.price, 0) / prices2024.length;
                totalPrice += avgPrice;
                count++;
            }
        });

        const avgPrice = count > 0 ? totalPrice / count : 5; // fallback to $5
        
        // get scales from the chart
        const allDates = displayedDrugs.flatMap(d => d.prices.map(p => p.date));
        const minDate = d3.min(allDates) || new Date(2017, 0, 1);
        const maxDate = d3.max(allDates) || new Date(2025, 11, 31);
        
        let minPrice = Infinity;
        let maxPrice = -Infinity;
        displayedDrugs.forEach(drug => {
            drug.prices.forEach(p => {
                if (p.price > 0) {
                    minPrice = Math.min(minPrice, p.price);
                    maxPrice = Math.max(maxPrice, p.price);
                }
            });
        });

        const xScale = d3.scaleTime()
            .domain([minDate, maxDate])
            .range([0, chartWidth]);

        const yScale = d3.scaleLog()
            .domain([Math.max(0.01, minPrice * 0.5), maxPrice * 1.2])
            .range([chartHeight, 0])
            .clamp(true);

        // calculate actual x,y position
        const dataX = xScale(targetDate);
        const dataY = yScale(avgPrice);
        
        console.log('Annotation pointing to:', { date: targetDate, price: avgPrice, x: dataX, y: dataY });
        
        // annotation box position (below and to the left of data point)
        const annotationX = dataX - 150;
        const annotationY = dataY + 60; // moved down

        const annotation = g.append('g')
            .attr('class', 'annotation')
            .attr('opacity', 0);

        // arrow pointing to actual data
        annotation.append('line')
            .attr('x1', annotationX + 140) // from top center of text box
            .attr('y1', annotationY)
            .attr('x2', dataX)
            .attr('y2', dataY)
            .attr('stroke', '#2D6A4F')
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrowhead)');

        // define arrowhead marker
        svg.append('defs')
            .append('marker')
            .attr('id', 'arrowhead')
            .attr('markerWidth', 10)
            .attr('markerHeight', 10)
            .attr('refX', 5)
            .attr('refY', 3)
            .attr('orient', 'auto')
            .append('polygon')
            .attr('points', '0 0, 10 3, 0 6')
            .attr('fill', '#2D6A4F');

        // text box
        const textBox = annotation.append('g')
            .attr('transform', `translate(${annotationX + 140}, ${annotationY})`);

        textBox.append('rect')
            .attr('x', -140)
            .attr('y', 0)
            .attr('width', 280)
            .attr('height', 60)
            .attr('fill', 'white')
            .attr('stroke', '#2D6A4F')
            .attr('stroke-width', 2)
            .attr('rx', 5);

        textBox.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('y', 21)
            .attr('font-family', 'Antonio')
            .attr('font-size', '14px')
            .attr('font-weight', 'bold')
            .attr('fill', '#2D6A4F')
            .text('Driven by American Rescue Plan Act');

        textBox.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('y', 39)
            .attr('font-family', 'Antonio')
            .attr('font-size', '14px')
            .attr('font-weight', 'bold')
            .attr('fill', '#2D6A4F')
            .text('and Medicaid Drug Rebate Program');

        // fade in annotation
        annotation.transition()
            .duration(1000)
            .attr('opacity', 1);

        currentStage = 3;
    }

    function reset() {
        currentStage = 0;
        initializeChart();
    }
</script>

{#if loading}
    <div class="loading">
        <p>Loading drug price data...</p>
    </div>
{:else if error}
    <div class="error">
        <p>Error loading data: {error}</p>
    </div>
{:else}
    <div class="container">
        <p class="subtitle">
            {displayedDrugs.length.toLocaleString()} drugs (sampled from 5,895 total)
        </p>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #4A90E2"></div>
                <span>Increased (>1%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #95A5A6"></div>
                <span>Stayed Same (±1%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #E74C3C"></div>
                <span>Decreased (&lt;-1%)</span>
            </div>
        </div>

        <div class="chart-container">
            <svg bind:this={svgRef} {width} {height}></svg>
        </div>

        <div class="controls">
            <button onclick={initializeChart} disabled={currentStage >= 1}>
                Step 1: Show All Drugs
            </button>
            <button onclick={showHighlightedOnly} disabled={currentStage < 1 || currentStage >= 2}>
                Step 2: Focus on Key Drugs
            </button>
            <button onclick={addAnnotation} disabled={currentStage < 2 || currentStage >= 3}>
                Step 3: Add Context
            </button>
            <button onclick={reset}>Reset</button>
        </div>
    </div>
{/if}

<style>
    * {
        font-family: Antonio;
    }

    .loading,
    .error {
        padding: 2rem;
        text-align: center;
        font-family: fustat;
    }

    .error {
        color: #9a2f1f;
    }

    .container {
        margin: 20px 40px;
    }

    h3 {
        font-size: 1.75em;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .subtitle {
        font-family: fustat;
        text-align: center;
        color: #666;
        margin-bottom: 1rem;
    }

    .legend {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 1.5rem;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-family: fustat;
    }

    .legend-color {
        width: 30px;
        height: 4px;
        border-radius: 2px;
    }

    .chart-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
    }

    .controls {
        display: flex;
        justify-content: center;
        gap: 1rem;
        align-items: center;
        flex-wrap: wrap;
    }

    button {
        padding: 0.75rem 1.5rem;
        font-size: 1em;
        font-family: Antonio;
        background-color: #2D6A4F;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.2s;
    }

    button:hover:not(:disabled) {
        background-color: #1e4d37;
    }

    button:disabled {
        background-color: #ccc;
        cursor: not-allowed;
    }

    :global(.x-axis text, .y-axis text) {
        font-family: fustat;
        font-size: 12px;
    }

    :global(.x-axis path, .y-axis path, .x-axis line, .y-axis line) {
        stroke: #666;
    }
</style>