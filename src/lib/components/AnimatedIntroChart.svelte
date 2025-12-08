<script lang="ts">
    import * as d3 from 'd3';
    import { onMount } from 'svelte';

    interface DrugData {
        rxcui: string;
        name: string;
        color: string;
        prices: { date: Date; price: number }[];
    }

    let loading = $state(true);
    let error = $state<string | null>(null);
    let searchIndex = $state<any>({});
    let allDrugs = $state<DrugData[]>([]);
    let displayedDrugs = $state<DrugData[]>([]);
    let isAnimating = $state(false);
    let currentProgress = $state(0);
    let sampleSize = $state(300);

    // SVG dimensions
    const width = 1200;
    const height = 600;
    const margin = { top: 40, right: 40, bottom: 60, left: 80 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    let svgRef: SVGSVGElement;
    let animationFrame: number;
    let containerRef: HTMLDivElement;
    let hasAnimated = $state(false);

    onMount(async () => {
        try {
            const searchIndexModule = await import('$lib/data/search_index_all.json');
            searchIndex = searchIndexModule.default;
            console.log('loading data for', Object.keys(searchIndex).length, 'drugs...');

            await loadAllDrugData();
            
            // Set up Intersection Observer to trigger animation when visible
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting && !hasAnimated && !isAnimating) {
                            console.log('Chart is visible, starting animation...');
                            hasAnimated = true;
                            startAnimation();
                        }
                    });
                },
                { threshold: 0.3 }
            );

            if (containerRef) {
                observer.observe(containerRef);
            }
            
            loading = false;
            
            return () => {
                observer.disconnect();
                if (animationFrame) cancelAnimationFrame(animationFrame);
            };
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

                drugs.push({
                    rxcui,
                    name: drugData.name,
                    color,
                    prices: pricePoints
                });
            } catch (e) {
                // skip
            }
        }

        console.log(`loaded ${drugs.length} drugs with price data`);
        allDrugs = drugs;
        sampleDrugs();
    }

    function sampleDrugs() {
        if (allDrugs.length <= sampleSize) {
            displayedDrugs = allDrugs;
            return;
        }

        const sorted = [...allDrugs].sort((a, b) => {
            const aLast = a.prices[a.prices.length - 1].price;
            const bLast = b.prices[b.prices.length - 1].price;
            return aLast - bLast;
        });

        const step = Math.floor(sorted.length / sampleSize);
        const sampled: DrugData[] = [];
        for (let i = 0; i < sorted.length && sampled.length < sampleSize; i += step) {
            sampled.push(sorted[i]);
        }

        displayedDrugs = sampled;
        console.log(`displaying ${displayedDrugs.length} of ${allDrugs.length} drugs`);
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
        const multipliers = [1, 2, 5];
        
        let magnitude = Math.floor(Math.log10(min));
        const maxMagnitude = Math.ceil(Math.log10(max)) + 1;
        
        while (magnitude <= maxMagnitude) {
            for (const mult of multipliers) {
                const value = mult * Math.pow(10, magnitude);
                if (value >= min * 0.5 && value <= max * 2) {
                    ticks.push(value);
                }
            }
            magnitude++;
        }
        
        return ticks;
    }

    function startAnimation() {
        if (isAnimating || displayedDrugs.length === 0) return;

        isAnimating = true;
        currentProgress = 0;

        const svg = d3.select(svgRef);
        const g = svg.select('.chart-group');

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

        const allDates = displayedDrugs.flatMap(d => d.prices.map(p => p.date));
        const minDate = d3.min(allDates) || new Date(2017, 0, 1);
        const maxDate = d3.max(allDates) || new Date(2025, 11, 31);

        const xScale = d3.scaleTime()
            .domain([minDate, maxDate])
            .range([0, chartWidth]);

        const startMinY = Math.max(0.01, minPrice * 0.5);
        const startMaxY = Math.min(1, minPrice * 10);
        let currentMinY = startMinY;
        let currentMaxY = startMaxY;

        const yScale = d3.scaleLog()
            .domain([currentMinY, currentMaxY])
            .range([chartHeight, 0])
            .clamp(true);

        const xAxis = d3.axisBottom(xScale).ticks(8);
        const yAxis = d3.axisLeft(yScale)
            .ticks(10, (d) => {
                if (d >= 1) return `${d.toFixed(0)}`;
                return `${d.toFixed(2)}`;
            });

        const xAxisG = g.append('g').attr('class', 'x-axis').attr('transform', `translate(0,${chartHeight})`).call(xAxis);
        const yAxisG = g.append('g').attr('class', 'y-axis').call(yAxis);

        xAxisG
            .append('text')
            .attr('x', chartWidth / 2)
            .attr('y', 45)
            .attr('fill', 'black')
            .attr('font-size', '14px')
            .attr('font-family', 'Antonio')
            .attr('text-anchor', 'middle')
            .text('Year');

        yAxisG
            .append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -chartHeight / 2)
            .attr('y', -55)
            .attr('fill', 'black')
            .attr('font-size', '14px')
            .attr('font-family', 'Antonio')
            .attr('text-anchor', 'middle')
            .text('Price per Unit ($)');

        const lineGenerator = d3
            .line<{ date: Date; price: number }>()
            .defined((d) => d.price > 0 && d.price >= currentMinY && d.price <= currentMaxY * 1.1)
            .x((d) => xScale(d.date))
            .y((d) => yScale(Math.max(currentMinY, Math.min(currentMaxY, d.price))));

        const lines = g
            .selectAll('.drug-line')
            .data(displayedDrugs)
            .enter()
            .append('path')
            .attr('class', 'drug-line')
            .attr('fill', 'none')
            .attr('stroke', (d) => d.color)
            .attr('stroke-width', 1.5)
            .attr('opacity', 0.4)
            .attr('d', (d) => lineGenerator(d.prices));

        const duration = 10000;
        const startTime = Date.now();
        const updateInterval = 100;
        let lastUpdate = 0;
        
        const allTickValues = generateLogTicks(startMinY, maxPrice);

        function animate() {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            currentProgress = progress;

            if (elapsed - lastUpdate >= updateInterval || progress === 1) {
                lastUpdate = elapsed;

                const easedProgress = 1 - Math.pow(1 - progress, 3);

                currentMaxY = startMaxY * Math.pow(maxPrice / startMaxY, easedProgress);
                yScale.domain([startMinY, currentMaxY]);

                const currentTicks = allTickValues.filter(t => t >= startMinY && t <= currentMaxY * 1.2);
                yAxis.tickValues(currentTicks);

                yAxisG.call(yAxis);
                lines.attr('d', (d) => lineGenerator(d.prices));
            }

            if (progress < 1) {
                animationFrame = requestAnimationFrame(animate);
            } else {
                isAnimating = false;
            }
        }

        animate();
    }

    function resetAnimation() {
        if (animationFrame) cancelAnimationFrame(animationFrame);
        isAnimating = false;
        currentProgress = 0;
        hasAnimated = false;

        const svg = d3.select(svgRef);
        svg.selectAll('.chart-group').remove();
        svg.append('g').attr('class', 'chart-group').attr('transform', `translate(${margin.left},${margin.top})`);
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
    <div class="container" bind:this={containerRef}>
        <h3>Drug Price Changes Over Time (2017-2025)</h3>
        <p class="subtitle">
            {displayedDrugs.length.toLocaleString()} drugs 
            {#if displayedDrugs.length < allDrugs.length}
                (sampled from {allDrugs.length.toLocaleString()} total)
            {/if}
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
            <svg bind:this={svgRef} {width} {height}>
                <g class="chart-group" transform="translate({margin.left},{margin.top})"></g>
            </svg>
        </div>

        <div class="controls">
            <button onclick={startAnimation} disabled={isAnimating}>
                {isAnimating ? 'Animating...' : 'Start Animation'}
            </button>
            <button onclick={resetAnimation} disabled={isAnimating}>Reset</button>
            {#if isAnimating}
                <div class="progress">
                    <div class="progress-bar" style="width: {currentProgress * 100}%"></div>
                </div>
            {/if}
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

    .progress {
        width: 200px;
        height: 8px;
        background-color: #e0e0e0;
        border-radius: 4px;
        overflow: hidden;
    }

    .progress-bar {
        height: 100%;
        background-color: #2D6A4F;
        transition: width 0.1s linear;
    }

    :global(.x-axis text, .y-axis text) {
        font-family: fustat;
        font-size: 12px;
    }

    :global(.x-axis path, .y-axis path, .x-axis line, .y-axis line) {
        stroke: #666;
    }
</style>