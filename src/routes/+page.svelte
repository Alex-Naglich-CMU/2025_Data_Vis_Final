<script lang="ts">
	import type { PageProps } from './$types';
	import { asset } from '$app/paths';
	import { onMount } from 'svelte';
	import { isDarkMode } from '$lib/stores/theme';
	import TimeSeriesComparison from '$lib/components/TimeSeriesComparison.svelte';
	import Headlines from '$lib/components/Headlines.svelte';
	import InsulinComparison from '$lib/components/InsulinComparison.svelte';
	import AnimatedSeries from '$lib/components/AnimatedSeries.svelte';

	onMount(() => {
		isDarkMode.init();

		// Set initial theme on body
		if (typeof window !== 'undefined') {
			const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
			document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
		}
	});

	let { data }: PageProps = $props();
</script>

<div class="title-holder">
	<div class="title">
		<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
		<h2>The state of drug pricing in America</h2>
	</div>
	<div class="pillsImages">
		<img class="pillpics" src={asset('/images/pills/pill01.png')} alt="red pill illustration" />
		<img class="pillpics" src={asset('/images/pills/pill02.png')} alt="blue pill illustration" />
		<img class="pillpics" src={asset('/images/pills/pill03.png')} alt="tan pill illustration" />
	</div>
</div>

<div class="intro-holder">
	<p>
		Prescription drug use is at an all-time high in the United States, due to increases in
		medicalization, population aging, and growing rates of diagnoses of chronic diseases. According
		to
		<a
			href="https://pmc.ncbi.nlm.nih.gov/articles/PMC10656114/"
			target="_blank"
			rel="noopener noreferrer">a 2023 study</a
		>, a person born today could expect to take prescription medications for roughly half of their
		life.
	</p>
	<br />
	<p>
		At the same time, everyone in the US seems to agree that <b
			>the current cost of prescription medications is too high.</b
		>
		Just look at the sample of news articles from this year alone ↓
	</p>
</div>

<h4 class="section-title">Explore recent headlines:</h4>
<div class="news-holder">
	<Headlines />
</div>

<div class="insulin-graphic-intro">
	<h3>How high are they really?</h3>
	<br />
	<p>
		What's causing drug prices to be so high? Does this public perception reflect the actual price
		trends?
	</p>
	<br />
	<p>
		Part of the problem is that information about how drugs are priced or even what they cost is
		largely hidden to the public. Also, since the US allows pharmaceutical companies to patent
		medications when they first go to market, patients have no choice but to pay their high fees.
	</p>
	<br />
	<p>
		Then the administrators of prescription drugs have little role in determining the costs their
		patients pay. The <a
			href="https://www.ama-assn.org/about/leadership/unchecked-power-pbm-industry-puts-patients-risk-harm"
			target="_blank"
			rel="noopener noreferrer">American Medical Association</a
		> noted that many patients complain about how they can’t afford their medications. When the patents
		expire and generic drugs join the market, those options are usually much more affordable, and are
		often even cheaper than they are in other countries.
	</p>
	<br />
	<p>
		For example, look at insulin: when the brand Lantus had no generic drug competitor in 2018 when
		there was no generic drug available, and 2025 after it took the place of the generic option. Of
		course, the cost of insulin is still very high, but it decreased significantly.
	</p>
</div>

<h4 class="section-title">Look at Insulin Lantus ↓</h4>
<InsulinComparison />

<div class="chart-intro">
	<p>
		In the United States, brand-name drug prices have continued to rise, while generic drug prices
		have steadily declined. This interactive dashboard visualizes these trends over time. According
		to <a
			href="https://www.rand.org/news/press/2021/01/28.html"
			target="_blank"
			rel="noopener noreferrer">RAND</a
		>, an independent public policy research organization, generics are the only category where U.S.
		prices are consistently lower than those in other countries, costing about 84% of the
		international average. Understanding this contrast makes it easier to see how pricing patterns
		affect affordability and policy decisions. Use the dashboard to select different drugs and
		compare how their prices change across brands, generics, and time.
	</p>
</div>

<TimeSeriesComparison />

<AnimatedSeries />

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
	/* 
	h5 {
		font-family: fustat;
		font-size: 20px;
		font-weight: normal;
		text-transform: uppercase;
	} */

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

	.section-title {
		margin-bottom: 20px;
		margin-left: 40px;
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
