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

    interface ChartPoint {
        date: Date;
        price: number;
    }

    // PROPS
    const { drugsData = [] }: { drugsData: DrugData[] } = $props();

    // STATE
    let selectedDrugIndex = $state<number>(0);

    // CONSTANTS
    const width = 900;
    const height = 400;
    const margin = { top: 40, right: 40, bottom: 80, left: 80 };

    // DERIVED DATA
    let selectedDrug = $derived(drugsData[selectedDrugIndex]);
    
    // Dynamic color based on brand/generic
    let lineColor = $derived(selectedDrug?.isBrand ? '#E53935' : '#2563eb');
    
    // Calculate average price per date
    let chartData = $derived.by(() => {
        if (!selectedDrug || !selectedDrug.prices) return [];
        
        // Group by date and average
        const dateMap: { [date: string]: number[] } = {};
        
        for (const point of selectedDrug.prices) {
            if (!dateMap[point.date]) {
                dateMap[point.date] = [];
            }
            dateMap[point.date].push(point.price);
        }
        
        // Calculate averages
        const result: ChartPoint[] = Object.entries(dateMap).map(([dateStr, prices]) => ({
            date: new Date(dateStr),
            price: prices.reduce((sum, p) => sum + p, 0) / prices.length
        }));
        
        // Sort by date
        result.sort((a, b) => a.date.getTime() - b.date.getTime());
        return result;
    });

    // Log what we have
    $effect(() => {
        console.log('Selected drug:', selectedDrug?.friendlyName);
        console.log('Chart data points:', chartData.length);
    });

    // SCALES
    let xScale = $derived.by(() => {
        if (chartData.length === 0) {
            return d3.scaleTime().range([margin.left, width - margin.right]);
        }
        
        return d3
            .scaleTime()
            .range([margin.left, width - margin.right])
            .domain(d3.extent(chartData, d => d.date) as [Date, Date]);
    });

    let yScale = $derived.by(() => {
        if (chartData.length === 0) {
            return d3.scaleLinear().range([height - margin.bottom, margin.top]).domain([0, 100]);
        }
        
        return d3
            .scaleLinear()
            .range([height - margin.bottom, margin.top])
            .domain([0, d3.max(chartData, d => d.price) ?? 100])
            .nice();
    });

    // LINE PATH
    let linePath = $derived.by(() => {
        if (chartData.length === 0) return '';
        
        const lineGen = d3
            .line<ChartPoint>()
            .x(d => xScale(d.date))
            .y(d => yScale(d.price))
            .curve(d3.curveMonotoneX);
        
        return lineGen(chartData) || '';
    });

    // AXES
    let xAxisRef: SVGGElement;
    let yAxisRef: SVGGElement;

    $effect(() => {
        if (xAxisRef && chartData.length > 0) {
            const xAxis = d3.axisBottom(xScale).tickFormat(d3.timeFormat('%b %Y') as any);
            d3.select(xAxisRef)
                .call(xAxis)
                .selectAll('text')
                .attr('transform', 'rotate(-45)')
                .style('text-anchor', 'end')
                .attr('dx', '-.8em')
                .attr('dy', '.15em');
        }
    });

    $effect(() => {
        if (yAxisRef && chartData.length > 0) {
            const yAxis = d3.axisLeft(yScale).tickFormat((d) => `$${d}`);
            d3.select(yAxisRef).call(yAxis);
        }
    });
</script>

<div class="controls">
    <h3>Drug Price Chart</h3>
    <label for="drug-select">Select Drug:</label>
    <select id="drug-select" bind:value={selectedDrugIndex}>
        {#each drugsData as drug, i}
            <option value={i}>
                {drug.friendlyName} - {drug.isBrand ? 'Brand' : 'Generic'}
            </option>
        {/each}
    </select>
    <p>Data points: {chartData.length}</p>
</div>

<div class="chart-wrapper">
    <svg {width} {height}>
        <!-- Line -->
        {#if linePath}
            <path d={linePath} fill="none" stroke={lineColor} stroke-width="3" />
        {/if}

        <!-- Data points -->
        {#each chartData as point}
            <circle 
                cx={xScale(point.date)} 
                cy={yScale(point.price)} 
                r="4" 
                fill={lineColor}
                stroke="white"
                stroke-width="2"
            />
        {/each}

        <!-- Axes -->
        <g class="x-axis" transform="translate(0,{height - margin.bottom})" bind:this={xAxisRef}></g>
        <g class="y-axis" transform="translate({margin.left},0)" bind:this={yAxisRef}></g>

        <!-- Axis labels -->
        <text
            text-anchor="middle"
            x={width / 2}
            y={height - 10}
            font-size="14px"
        >
            Time
        </text>

        <text
            text-anchor="middle"
            transform="rotate(-90)"
            x={-height / 2}
            y={20}
            font-size="14px"
        >
            Price ($ per unit)
        </text>
    </svg>

    <!-- LEGEND -->
    <div class="legend">
        <h4>Legend</h4>
        <div class="legend-item">
            <div class="legend-line" style="background-color: {lineColor};"></div>
            <span>{selectedDrug?.friendlyName} ({selectedDrug?.isBrand ? 'Brand' : 'Generic'})</span>
        </div>
    </div>
</div>

<style>
    .controls {
        padding: 1.5rem;
        margin: 2rem;
    }

    .controls h3 {
        margin-top: 0;
    }

    .controls select {
        width: 100%;
        max-width: 400px;
        padding: 0.5rem;
        font-size: 16px;
        margin: 10px 0;
    }

    .chart-wrapper {
        padding: 2rem;
        display: flex;
        gap: 30px;
        align-items: flex-start;
    }

    svg {
        border: 1px solid #ccc;
    }

    .legend {
        min-width: 200px;
        padding: 1rem;
        border-radius: 8px;
    }

    .legend h4 {
        margin: 0 0 10px 0;
        font-size: 14px;
        text-transform: uppercase;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
    }

    .legend-line {
        width: 30px;
        height: 3px;
        border-radius: 2px;
    }
</style>