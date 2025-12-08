<!-- page.svelte file -->

<script lang="ts">
	import type { PageProps } from './$types';
	import { asset } from '$app/paths';
	import { onMount } from 'svelte';
	import { isDarkMode } from '$lib/stores/theme';
	import TimeSeriesComparison from '$lib/components/TimeSeriesComparison.svelte';
	import Headlines from '$lib/components/Headlines.svelte';
	import InsulinComparison from '$lib/components/Insulin.svelte';
	import AnimatedSeries from '$lib/components/AnimatedSeries.svelte';
	import PricePerMgForm from '$lib/components/PricePerMgForm.svelte';
	import PricePerMgStrength from '$lib/components/PricePerMgStrength.svelte';
	import PricePerCapsuleForm from '$lib/components/PricePerCapsuleForm.svelte';
	import PricePerCapsuleStrength from '$lib/components/PricePerCapsuleStrength.svelte';
	import AnimatedSeriesPaginated from '$lib/components/AnimatedSeriesPaginated.svelte';
 	import AnimatedSeriesPaginated2 from '$lib/components/AnimatedSeriesPaginated2.svelte';
	import InflationComparison from '$lib/components/InflationComparison.svelte';
	import AveragePriceFormCategories from '$lib/components/AveragePriceFormCategories.svelte';

	let selectedDrugIndex = $state(8);
	
	const brandDrugs = [
		{ name: 'GLUCOPHAGE' },
		{ name: 'LANTUS' },
		{ name: 'LEXAPRO' },
		{ name: 'LIPITOR' },
		{ name: 'LYRICA' },
		{ name: 'NORVASC' },
		{ name: 'PROVIGIL' },
		{ name: 'PROZAC' },
		{ name: 'VYVANSE' },
		{ name: 'ZOLOFT' }
	];

	onMount(() => {
		isDarkMode.init();

		// Set initial theme on body
		if (typeof window !== 'undefined') {
			const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
			document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
		}
	});

</script>
<div class='page-container'> 
	<div class='intro-container'> 
		<div class="title-holder">
			<div class="title">
				<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
			</div>
			<div class="pillsImages">
				<img class="pillpics" src={asset('/images/pills/pill01.png')} alt="red pill illustration" />
				<img class="pillpics" src={asset('/images/pills/pill02.png')} alt="blue pill illustration" />
				<img class="pillpics" src={asset('/images/pills/pill03.png')} alt="tan pill illustration" />
			</div>
		</div>

		<div class="intro-holder">
			<h2>The state of drug pricing in America</h2>
			<br />
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
				At the same time, everyone in the US seems to agree that 
				<b>the current cost of prescription medications is too high.</b>
				Just look at the sample of news articles from this year alone ↓
			</p>
		</div>

		<h4 class="section-title">Explore recent headlines:</h4>
		<div class="news-holder">
			<Headlines />
		</div>
		<br />
		<h2>What is driving drug prices?</h2>
		<br />
		<p>
			Looking for trends in what contributes to higher drug prices is complicated. Prescription drugs cover a wide spectrum so they are not always easy to compare. Some medications only require a short course and some require lifelong use. Some need to be taken every day and others monthly or only as-needed. Prescriptions also span types ranging anywhere from oral tablets to topical foams. 
		</p>
		<br />
		<p>
			These are some of the most common drugs used by patients in the US. 
		</p>
		<div class='drug-select-container'>
			<h4>Pick one to learn more about its price. </h4>
			<br />
		<!-- drug selector -->
			<div class="drug-selector">
				<div class="drug-radios">
					{#each brandDrugs as drug, i}
						<label class="radio-label">
							<input
								type="radio"
								name="drug-selection"
								value={i}
								bind:group={selectedDrugIndex}
								class="radio-input"
							/>
							<span class="radio-text">{drug.name}</span>
						</label>
					{/each}
				</div>
			</div>
		</div>
		<div class="cause-section-container">
			<h3>Does dosage affect cost?</h3>
			<br /> 
			<p>
				Even though the amount patients pay per MG may decrease as dosage increases, the price of each pill remains relatively constant independent of dosage. When a certain dosage is unusually high, it is usually due to market exclusivity rather than the drug's formulation. 
			</p>
			<div class="width-tracker mid-chart">
				<div class="charts-container">
					<PricePerMgStrength {selectedDrugIndex} />
					<PricePerCapsuleStrength {selectedDrugIndex}/>
				</div>
			</div>
		</div>
		

		<br />
		<div class="cause-section-container">
			<h3>What about the delivery form?</h3>
			<br /> 
			<p>
				For oral medications, the differences between price in delivery method are also relatively minor for different versions of the same drug. Forms that do affect cost generally have specialized or patented technologies.
			</p>
			<!-- add a couple sentences if the person's selected drug doesn't have a second form and have it default to a different drug -->
			<div class="width-tracker mid-chart">
				<div class="charts-container">
					<PricePerMgForm {selectedDrugIndex} />
					<PricePerCapsuleForm {selectedDrugIndex} />
				</div>
			</div>
			<br /> 
			<p>
				Forms between different medications play a much larger role in predicting the cost. By far the most expensive form of drug delivery is injections, such as for insulin or epinepherine. Injections are followed by inhalation, such as for asthma medication, and then delayed or extended release capsules. Again, exclusive or proprietary technology plays a role. 
			</p>
			<div class="mid-chart">
				<AveragePriceFormCategories />
			</div>
		</div>
		
		<div class="cause-section-container">
			<h3>Do these numbers </h3>
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
				> noted that many patients complain about how they can't afford their medications. When the patents
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
			<br />
			<h3>How much cheaper are generics?</h3>
		</div>
	</div>
	

	<!-- I know this syntax is a bit wonky -->
	<TimeSeriesComparison /> 
	<br />
	<div class="headers">
		<h3> How did drug prices change over time? </h3>
	</div>
	<AnimatedSeries />

	<br />

	<AnimatedSeriesPaginated />

	<br />

	<AnimatedSeriesPaginated2 />

	<br />

<div class="headers">
	<h3> What is the cheapest option for a specific drug? </h3>
</div>
	<InflationComparison />
</div>
<br />

<style>
	* {
		font-family: Antonio;
	}

	h1 {
		font-size: 5em;
		font-weight: bold;
	}

	h2 {
		font-size: 2.5em;
		font-weight: bold;
	}

	h3 {
		font-size: 1.75em;
		font-weight: bold;
	}

	h4 {
		font-family: fustat;
		font-size: 1.3em;
		font-weight: 700;
	}
	
	h5 {
		font-family: fustat;
		font-size: 1em;
		font-weight: normal;
		text-transform: uppercase;
	}

	p {
		font-family: fustat;
		font-size: 1.1em;
		font-weight: normal;
	}

	p a {
		font-family: fustat;
		font-weight: normal;
		color: inherit;
		text-decoration: underline;
	}

	p b {
		font-family: fustat;
		font-size: 1.1em;
		font-weight: bold;
	}

	.page-container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 0;
	}

	.intro-container{
		max-width: 850px;
		margin: 0 auto;

	}

	.title-holder {
		padding: 40px 0;
		display: flex;
		justify-content: space-between;
		align-items: center;
		min-height: 100vh 
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
	}

	.intro-holder {
		margin-bottom: 40px;
		max-width: 850px;
	}

	.news-holder {
		margin-bottom: 40px;
		max-width: 850px;
	}

	.insulin-graphic-intro {
		margin-bottom: 40px;
		max-width: 850px;
	}

	.chart-intro {
		max-width: 850px;
	}

	.drug-select-container {
		display: flex;
		flex-direction: column;
		margin: 5em 0;
	}

	.drug-selector {
		display: flex;
		align-items: center;
		margin: 0 0 2em 0;
	}

	.drug-selector label {
		font-family: Antonio;
		font-size: 1em;
		font-weight: 600;
	}

	.drug-dropdown {
		font-family: fustat;
		font-size: 1em;
		padding: 0.2rem 1rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		background-color: rgba(75, 75, 75, 0.1);
		cursor: pointer;
		min-width: 200px;
	}

	.drug-dropdown:focus {
		outline: 2px solid #54707c;
	}

	.charts-container {
		display: flex;
		justify-content: space-between;
		/* border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1); */
		user-select: none;
		-webkit-user-select: none;
	}

	.drug-selector {
		margin-bottom: 2rem;
		border: 1px solid #ccc;
	}

	.drug-radios {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1.8em 8em;
		max-width: 850px;
		margin: 0 auto;
		padding: 3.5em 0;
		
	}

	.radio-label {
		display: flex;
		align-items: center;
		padding: 0.1rem .1rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.radio-label:hover .radio-text {
		font-weight: 800;
	}

	.radio-label:has(.radio-input:checked) .radio-text {
		font-weight: 800;
	}

	.radio-input {
		margin-right: 0.6rem;
		appearance: none;
		-webkit-appearance: none;
		-moz-appearance: none;
		border: 2px solid #ccc;
		border-radius: 50%;
		position: relative;
		outline: none;
		background-color: white;
		box-shadow: none;
	}

	.radio-input:focus-visible {
		outline: none;
		box-shadow: none;
	}

	.radio-input:checked {
		border-color: #C9381A;
		outline: none;

	}
	.radio-input:checked::before {
		content: '';
		position: absolute;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background-color: #C9381A;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.radio-text {
		font-family: fustat;
		font-size: 1em;
	}

	.cause-section-container {
		margin-bottom: 10em;
	}

	.mid-chart {
		margin-bottom: 6em;
		margin-top: 6em;
	}

</style>