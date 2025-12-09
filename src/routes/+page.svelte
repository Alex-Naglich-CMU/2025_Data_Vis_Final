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
	import AnimatedIntroChart from '$lib/components/AnimatedIntroChart.svelte';
	import DropChart from '$lib/components/DropChart.svelte';
	import IntroChart from '$lib/components/IntroChart.svelte';
	import IntroChart2 from '$lib/components/IntroChart2.svelte';
	import PeopleImpact from '$lib/components/PeopleImpact.svelte';
	import DrugSelector from '$lib/components/DrugSelector.svelte';



	let selectedDrugIndex = $state(8);
	
    const brandDrugs = [
        // { name: 'GLUCOPHAGE', image: '/images/pills/pill01.png' },
        { name: 'LAMICTAL' },
        { name: 'LANTUS' },
        { name: 'LEXAPRO' },
        { name: 'LIPITOR' },
        { name: 'LYRICA' },
        { name: 'NEURONTIN' },
        { name: 'NORVASC' },
        { name: 'PROVIGIL' },
        { name: 'PROZAC' },
        { name: 'SYNTHROID' },
        { name: 'VYVANSE' },
        { name: 'ZOLOFT' }
    ];


	//default values for scrolling effect
	let currentSection = $state(0);
	let isTransitioning = $state(false);
	let totalSections = $state(0);

	onMount(() => {
		isDarkMode.init();

		// Set initial theme on body
		if (typeof window !== 'undefined') {
			const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
			document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
		}

		//find & count each 'anchor' section 
		const sections = document.querySelectorAll('.slide-section');
		totalSections = sections.length;

		let scrollMovementSum = 0;
		const threshold = 15;
		
		const handleWheel = (e: WheelEvent) => {
			//prevent users from srolling during transition
			if (isTransitioning) {
				e.preventDefault();
				return;
			}

			//don't zoom in on charts
			const target = e.target as HTMLElement;
			if (target.closest('.inflation-section') || target.closest('svg') || target.closest('.chart-area')) {
				return; 
			}
			
			// add user scroll to total scroll movemetn
			scrollMovementSum += e.deltaY;
			
			// Scrolling down to next section
			if (scrollMovementSum > threshold && currentSection < totalSections - 1) {
				const currentSectionElement = sections[currentSection];
				const currentRect = currentSectionElement.getBoundingClientRect();
				
				if (currentRect.top >= -20 && currentRect.top <= 15) {
					isTransitioning = true;
					currentSection += 1;
					scrollMovementSum = 0;
					
					document.body.style.overflow = 'hidden';
					
					const nextSection = sections[currentSection];
					nextSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
					setTimeout(() => { 
						isTransitioning = false;
						// reset overflow to allow scrolling again
						document.body.style.overflow = '';
					}, 1200);
				} else {
					//reset to prevent false triggers
					scrollMovementSum = 0;
				}
			} 
			// Scrolling up to previous section
			else if (scrollMovementSum < -threshold && currentSection > 0) {
				const currentRect = sections[currentSection].getBoundingClientRect();
				
				if (currentRect.top >= -30) {
					isTransitioning = true;
					currentSection -= 1;
					scrollMovementSum = 0;
					
					document.body.style.overflow = 'hidden';

					const prevSection = sections[currentSection];
					prevSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
					setTimeout(() => { 
						isTransitioning = false;
						// reset overflow to allow scrolling again
						document.body.style.overflow = '';

					}, 1200);
				}
			}
			
			if (Math.abs(scrollMovementSum) > threshold * 20) {
				scrollMovementSum = 0;
			}
		};

		//listen for mouse wheel movement
		window.addEventListener('wheel', handleWheel, { passive: false });
		
		return () => {
			window.removeEventListener('wheel', handleWheel);
		};
	});

</script>

<div class='slideshow-wrapper'>
	<div class='page-container'> 
		<div class='intro-container'> 
			<!--Intro Screen -->
			<div class="title-holder slide-section">
				<div class="title">
					<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
				</div>
				<div class="pillsImages">
					<img class="pillpics" src={asset('/images/pills/pill01.png')} alt="red pill illustration" />
					<img class="pillpics" src={asset('/images/pills/pill02.png')} alt="blue pill illustration" />
					<img class="pillpics" src={asset('/images/pills/pill03.png')} alt="tan pill illustration" />
				</div>
			</div>

			<!--drug selector -->
			<div class='drug-select-container slide-section'>
				<p>
					According
					to
					<a
						href="https://pmc.ncbi.nlm.nih.gov/articles/PMC10656114/"
						target="_blank"
						rel="noopener noreferrer">a 2023 study</a
					>, a person born today could expect to take prescription medications for roughly half of their
					life. These are some of the most common prescriptions in the US. 
				</p>
				<br />
				<h4>Pick one to learn more about its price. </h4>
				<br />
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

			<!--Current State-->
			<div class="slide-section">
				<div class="intro-holder">
					<h2>The state of drug pricing in America</h2>
					<br />
					<h3>Prescription drug use is increasing</h3>
					<br>
					<p>
						Prescription drug use is at an all-time high in the United States, in part due to increases in
						medicalization, population aging, and growing rates of diagnoses of chronic diseases. At
						the same time, everyone in the US seems to agree that 
						<b>the current cost of prescription medications is too high.</b>
						Just look at the sample of news articles from this year alone ↓
					</p>
					<br />
					<p>
						
					</p>
					<br />
					<h4 class="section-title">Explore recent headlines:</h4>
					<div class="news-holder">
						<Headlines />
					</div>
				</div>
			</div>

			<div class='slide-section'>
				<div class="price-increase-section">
					<h3>Are prices actually increasing?</h3>
					<br />
					<p>
						It turns out that between 2017 and 2025, <b>more drug prices decreased</b> instead of increased. But are these figures telling us the whole story? 
					</p>
					<IntroChart />
				</div>
			</div>
			
			<div class='slide-section'>
				<div class="price-increase-section">
					<p>
						For now, lets ignore the drugs whose prices stay the same. If we look at the actual price amount each drug increased or decreased by, the data looks very different. Although slightly 
						more drugs decreased in price than increased, the total dollar increase is much larger than the total dollar decrease.
						<IntroChart2 />
					<p>
						When we only look at the number of drugs whose prices have increased or decreased, we're missing critical context.
						Let's be clear, 
						<b>drug prices are getting worse.</b>
					</p>
				</div>
			</div>



			<div class='slide-section'>
				<div class="inflation-section">
					<h3>Is the drug you selected outpacing inflation?</h3>
					<br />
					<InflationComparison {selectedDrugIndex}/>
				</div>
			</div>
			
			<div class='slide-section'>
				<div class='impact'>
					<h3>What impact does this have?</h3>
					<br />
					<p>People end up splitting pills or skipping doses to try and make a drug last longer, threatening their health. Out of pocket costs are greater for those with less coverage, so some of the people likely to receive the highest drug costs are those with the fewest resources to pay for them.</p>
					<br />
					<div class="graphic">
						<PeopleImpact />
					</div>
					<br />
				</div>
			</div>
			


			<div class="slide-section">
				<div class='causes-intro'>
					<h2>What is driving drug prices?</h2>
					<br />
					<p>
						Looking for trends in what contributes to higher drug prices is complicated. Prescription drugs cover a wide spectrum so they are not always easy to compare. Some medications only require a short course and some require lifelong use. Some need to be taken every day and others monthly or only as-needed. Prescriptions also span types ranging anywhere from oral tablets to topical foams. 
					</p>
					<br />
					<p>
						These are some of the most common drugs used by patients in the US. 
					</p>
				</div>
			</div>
			
			
			<div class="cause-section-container">
				<h3>Does dosage affect cost?</h3>
				<br /> 
				<p>
					Even though the amount patients pay per MG may decrease as dosage increases, the price of each pill emains relatively constant independent of dosage. When a certain dosage is unusually high, it is usually due to market exclusivity rather than the drug's formulation. 
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

			<h4 class="section-title">Look at Insulin Lantus ↓</h4>
			<InsulinComparison />

			
			
		</div>
	</div>
		

		<!-- I know this syntax is a bit wonky -->
		 <DrugSelector bind:selectedDrugIndex label="Select drug:" />
        <TimeSeriesComparison {selectedDrugIndex} /> 
        <br />
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
		
	<br />
	<AnimatedIntroChart />
	<br />
	<DropChart />
</div> 

<style>
	* {
		font-family: Antonio;
	}

	h1 {
		font-size: 5em;
		font-weight: bold;
	}

	h2 {
		font-size: 2.75em;
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
		font-size: inherit;
		font-weight: normal;
		color: inherit;
		text-decoration: underline;
	}

	p b {
		font-family: fustat;
		font-size: inherit;
		font-weight: bold;
	}

	li {
		padding-bottom: 2em;
	}

	.slideshow-wrapper {
		scroll-behavior: smooth;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.slide-section {
		min-height: 100vh;
		display: flex;
		justify-content: center;
		scroll-snap-align: start;
	}

	.page-container {
		width: 100%;
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
		justify-content: center;
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
	}

	.intro-holder {
		max-width: 850px;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.news-holder {
		margin-bottom: 40px;
		max-width: 850px;
		display: flex;
		justify-content: center;
		align-items: center;
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
		padding: 0.2em 1em;
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
		margin-bottom: 2em;
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
		padding: 0.1em .1em;
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
		margin-right: 0.6em;
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

	.price-increase-section {
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.inflation-section {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.impact {
		min-height: 100vh;
		max-width: 850px;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.source {
		font-family: fustat;
		font-size: .5em;
		color: #818181;
	}

	.graphic {
		margin: 3em auto;
	}

</style>