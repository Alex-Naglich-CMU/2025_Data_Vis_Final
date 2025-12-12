<script lang="ts">
	import type { PageProps } from './$types';
	import { asset } from '$app/paths';
	import { onMount } from 'svelte';
	import { isDarkMode } from '$lib/stores/theme';
	import TimeSeriesComparison from '$lib/components/TimeSeriesComparison.svelte';
	import Headlines from '$lib/components/Headlines.svelte';
	import AnimatedSeries from '$lib/components/AnimatedSeries.svelte';
	import PricePerMgForm from '$lib/components/PricePerMgForm.svelte';
	import PricePerMgStrength from '$lib/components/PricePerMgStrength.svelte';
	import PricePerCapsuleForm from '$lib/components/PricePerCapsuleForm.svelte';
	import PricePerCapsuleStrength from '$lib/components/PricePerCapsuleStrength.svelte';
	import AnimatedSeriesPaginated from '$lib/components/AnimatedSeriesPaginated.svelte';
	import AnimatedSeriesPaginated2 from '$lib/components/AnimatedSeriesPaginated2.svelte';
	import InflationComparison from '$lib/components/InflationComparison.svelte';
	import AveragePriceFormCategories from '$lib/components/AveragePriceFormCategories.svelte';
	import DropChart from '$lib/components/DropChart.svelte';
	import IntroChart from '$lib/components/IntroChart.svelte';
	import IntroChart2 from '$lib/components/IntroChart2.svelte';
	import PeopleImpact from '$lib/components/PeopleImpact.svelte';
	import DrugSelector from '$lib/components/DrugSelector.svelte';

	let selectedDrugIndex = $state(8);

	const brandDrugs = [
		{ name: 'LAMICTAL', image: 'Lamictal.png', type: 'Anticonvulsant' },
		{ name: 'LANTUS', image: 'Lantus.png', type: 'Insulin' },
		{ name: 'LEXAPRO', image: 'Lexapro.png', type: 'SSRI' },
		{ name: 'LIPITOR', image: 'Lipitor.png', type: 'Statin' },
		{ name: 'LYRICA', image: 'Lyrica.png', type: 'Anticonvulsant' },
		{ name: 'NEURONTIN', image: 'Neurotin.png', type: 'Anticonvulsant' },
		{ name: 'NORVASC', image: 'Norvasc.png', type: 'Calcium Channel Blocker' },
		{ name: 'PROVIGIL', image: 'Provigil.png', type: 'CNS Stimulant' },
		{ name: 'PROZAC', image: 'Prozac.png', type: 'SSRI' },
		{ name: 'SYNTHROID', image: 'Synthroid.png', type: 'Thyroid Hormone' },
		{ name: 'VYVANSE', image: 'Vyvance.png', type: 'CNS Stimulant' },
		{ name: 'ZOLOFT', image: 'Zoloft.png', type: 'SSRI' }
	];

	//default values for scrolling effect
	let currentSection = $state(0);
	let isTransitioning = $state(false);
	let totalSections = $state(0);

	onMount(() => {
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
			// if (
			// 	target.closest('.inflation-section') ||
			// 	target.closest('svg') ||
			// 	target.closest('.chart-area')
			// ) {
			// 	return;
			// }

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

<div class="slideshow-wrapper">
	<div class="page-container">
		<div class="intro-container">
			<!--Intro Screen -->
			<div class="slide-section">
				<div class="title-holder">
					<div class="title">
						<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
					</div>
					<div class="pillsImages">
						<img
							class="pillpics"
							src={asset('/images/pills/pill01.png')}
							alt="red pill illustration"
						/>
						<img
							class="pillpics"
							src={asset('/images/pills/pill02.png')}
							alt="blue pill illustration"
						/>
						<img
							class="pillpics"
							src={asset('/images/pills/pill03.png')}
							alt="tan pill illustration"
						/>
					</div>
				</div>
			</div>

			<!--drug selector -->
			<div class="slide-section">
				<div class="slide-section-content">
					<h4>Pick a medication to learn more about its price.</h4>
					<br />
					<p>
						According to
						<a
							href="https://pmc.ncbi.nlm.nih.gov/articles/PMC10656114/"
							target="_blank"
							rel="noopener noreferrer">a 2023 study</a
						>, a person born today could expect to take prescription medications for roughly half of
						their life. These are some of the most common prescriptions in the US. Pick one to learn
						more about its price.
					</p>
					<br />
					<div class="drugs-grid">
						{#each brandDrugs as drug, index}
							<button class="drug-card" onclick={() => (selectedDrugIndex = index)}>
								<img
									src={asset(`/images/drug-selections/${drug.image}`)}
									alt={drug.name}
									class="drug-image"
								/>
								<div class="text-button" class:selected={selectedDrugIndex === index}>
									<h5 class="pill-button-font">{drug.name}</h5>
									<h6 class="pill-button-sub">{drug.type}</h6>
								</div>
							</button>
						{/each}
					</div>
					<div class="selection-indicator">
						<p>You selected <b>{brandDrugs[selectedDrugIndex].name}</b></p>
						<span class="arrow">↓</span>
					</div>
				</div>
			</div>

			<!--Current State-->
			<div class="slide-section">
				<div class="slide-section-content">
					<h2>The state of drug pricing in America</h2>
					<br />
					<h3>The use of prescription drugs is increasing</h3>
					<br />
					<p>
						Prescription drug use is at an all-time high in the United States, in part due to
						increases in medicalization, population aging, and growing rates of diagnoses of chronic
						diseases. At the same time, everyone in the US seems to agree that
						<b>the current cost of prescription medications is too high.</b>
						Just look at the sample of news articles from this year alone ↓
					</p>
					<br />
					<h4 class="section-title">Explore recent headlines:</h4>
					<div class="news-holder">
						<Headlines />
					</div>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h4>Are prices increasing too, or does it just feel that way?</h4>
					<br />
					<p>
						It turns out that between 2017 and 2025, <b>more drug prices decreased</b> instead of increased.
						But are these figures telling us the whole story?
					</p>
					<IntroChart />
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<p>
						For now, let's ignore the drugs whose prices stay the same. If we look at the actual
						price amount each drug increased or decreased by, the data looks very different.
						Although slightly more drugs decreased in price than increased, the total dollar
						increase is much larger than the total dollar decrease.
					</p>
					<IntroChart2 />
					<p>
						When we only look at the number of drugs whose prices have increased or decreased, we're
						missing critical context. Let's be clear,
						<b>drug prices are getting worse.</b>
					</p>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<div class="title-inflation">
						<h3>Is the drug you selected outpacing inflation?</h3>
						<DrugSelector bind:selectedDrugIndex />
					</div>
					<br />
					<InflationComparison {selectedDrugIndex} />
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h2>What are the causes?</h2>
					<br />
					<p>
						Looking for trends in what contributes to higher drug prices is complicated.
						Prescription drugs cover a wide spectrum so they are not always easy to compare. Some
						medications only require a short course and some require lifelong use. Some need to be
						taken every day and others monthly or only as-needed. Prescriptions also span types
						ranging anywhere from oral tablets to topical foams.
					</p>
					<br />
					<p>
						If we look at this in the simplest way, causes can be broken down into two categories:
						development costs, and systemic factors.
					</p>
					<br />
					<div class='bottle-illustration'>
						<img
							class="pillBottle"
							src={asset('/images/drug-selections/RX-Bottle.png')}
							alt="pill-bottle-illustration"
						/>
						<h1 class="question">??</h1>
					</div>
					
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h2>Development Costs</h2>
					<br />
					<h4>Price remains relatively stable across different dosages of the same drug</h4>
					<br />
					<p>
						Even though the amount patients pay per MG may decrease as dosage increases, the price
						of each pill remains relatively constant independent of dosage. When a certain dosage is
						unusually high, it is usually due to market exclusivity rather than the drug's
						formulation.
					</p>
					<div class="width-tracker mid-chart">
						<div class="charts-container">
							<PricePerMgForm {selectedDrugIndex} />
							<PricePerCapsuleForm {selectedDrugIndex} />
						</div>
					</div>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h4>
						The form, like capsule or tablet, has little effect across versions of the same
						medication
					</h4>
					<br />
					<p>
						For oral medications, the differences between price based on delivery methods are also
						relatively minor for different versions of the same drug. Forms that do affect cost
						generally have specialized or patented technologies.
					</p>
					<div class="width-tracker mid-chart">
						<div class="charts-container">
							<PricePerMgStrength {selectedDrugIndex} />
							<PricePerCapsuleStrength {selectedDrugIndex} />
						</div>
					</div>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h4>Across different drug classes, forms play a bigger role</h4>
					<br />
					<p>
						Forms between different medications play a much larger role in predicting the cost. By
						far the most expensive form of drug delivery is injection, such as for insulin or
						epinephrine. Injection is followed by inhalation, such as for asthma medication, and
						then delayed or extended release capsules. Again, exclusive or proprietary technology is
						the driving factor.
					</p>
					<div class="mid-chart">
						<AveragePriceFormCategories />
					</div>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h2>Systemic Factors</h2>
					<br />
					<h4>Drugs are developed, priced, and distributed by profit-driven companies.</h4>
					<br />
					<p>
						Three main groups control what Americans pay for prescription drugs: pharmaceutical
						companies set initial prices and use patents to block competition, pharmacy benefit
						managers (PBM) negotiate as middlemen while keeping deals secret, and health insurers
						decide coverage and copays. Together, these players create a complex system where each
						group profits while patients face rising costs with little transparency about how prices
						are actually determined.
					</p>
					<br />
					<div class='card-holder'>
						<div class='company-cards'>
							<h4 class="card-label">Pharmaceutical Companies</h4>
							<img class="card-image" src={asset('/images/drug-selections/Pill-white.png')} alt="pharma company icon" />
							<p class="card-label">Set the Prices & Leverage Patents</p>
						</div>
						<div class='company-cards'>
							<h4 class="card-label">Pharmacy Benefit Managers</h4>
            				<img class="card-image" src={asset('/images/drug-selections/Person-Icon-white.png')} alt="PBM icon" />
							<p class="card-label">Serve as Middlemen Between Parties</p>
						</div>
						<div class='company-cards'>
							<h4 class="card-label">Health Insurance Companies</h4>
							<img class="card-image" src={asset('/images/drug-selections/shield-white.png')} alt="health insurance icon" />
							<p class="card-label">Decide Coverage & Copay Rates</p>
						</div>
					</div>
						
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h3>What impact does this have?</h3>
					<br />
					<p>
						People end up splitting pills or skipping doses to try and make a drug last longer,
						threatening their health. Out of pocket costs are greater for those with less coverage,
						so some of the people likely to receive the highest drug costs are those with the fewest
						resources to pay for them.
					</p>
					<br />
					<div class="graphic">
						<PeopleImpact />
					</div>
					<br />
					<h4>So what can we do, and how do we fix this?</h4>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<br />
					<h4>For your own personal prescriptions, choose generic when it's available.</h4>
					<br />
					<p>
						Your physician and PBM are likely already encouraging generic use for your prescription
						medications over their brand-name counterparts. Generic prescriptions are actually
						cheaper in the US than in other countries. When generic drugs are available, they can
						ease the price of medications significantly.
					</p>
					<br />
					<div class="generic-v-brand">
						<DrugSelector bind:selectedDrugIndex />
						<TimeSeriesComparison {selectedDrugIndex} />
					</div>
					<br />
					<p>
						However, generic options aren't always available, especially for new drugs. So what can
						we do to reduce the cost of those medications for those who need them?
					</p>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h4>To make systemic changes, we need policy solutions</h4>
					<br />
					<p>
						Drug price decreases either caused by patents expiring, or policy intervention. The
						American Rescue Plan Act, passed in 2021 under President Biden, removed the caps on
						penalties to drugmakers when they raise prices faster than inflation. By increasing the
						financial consequences for large price hikes, the law creates a stronger incentive for
						manufacturers to keep prices in check. As a result, we see the prices of some drugs, <a
							href="https://www.kff.org/medicaid/what-are-the-implications-of-the-recent-elimination-of-the-medicaid-prescription-drug-rebate-cap/#:~:text=As%20of%20January%201%2C%202024,a%20frequently%20used%20asthma%20inhaler."
							target="_blank"
							rel="noopener noreferrer">especially Insulin products and Inhalers</a
						> drop between 2023 and 2025.
					</p>
					<br />
					<div class="chart-wrapper">
						<DropChart />
					</div>
				</div>
			</div>

			<div class="slide-section">
				<div class="slide-section-content">
					<h4>How You Can Get Involved</h4>
					<br />
					<p>
						There are ways to help make prescription drugs more affordable. You can support advocacy
						groups like the AMA's Truth in RX, which works to increase transparency in drug pricing.
						You can also participate in state and federal elections and support legislation aimed at
						lowering prescription drug costs. For example, the 2025 State Tracker from the National
						Academy for State Health Policy highlights current bills in each state focused on making
						medications more affordable. Every action helps move the system toward fairer pricing.
					</p>
					<br />
					<p>
						→ <a href="https://truthinrx.org/" target="_blank" rel="noopener noreferrer"
							>Truth in RX</a
						>
					</p>
					<br />
					<p>
						→ <a
							href="https://nashp.org/state-tracker/2025-state-legislation-to-lower-prescription-drug-costs/"
							target="_blank"
							rel="noopener noreferrer">2025 State Tracker</a
						>
					</p>
				</div>
			</div>
		</div>

		<div class="exploreOtherDrugs">
			<h3>Explore other drugs!</h3>
			<p>
				Try out one of the tools we used to do our data research to see what you can learn about
				drug prices on your own!
			</p>

			<h6>Click on any drug price in the right menu to add it to the graph</h6>
		</div>

		<AnimatedSeriesPaginated />

		<br />

		<br />
	</div>
	<!-- closes page-container -->
	 <!-- Footer -->
	<footer class="footer">
		<div class="footer-content">
			<div class="footer-left">
				<p class="team">Team: Anissa Patel, Kimberly Credit, Alex Naglich</p>
				<p class="acknowledgements">
					<a href={asset('/acknowledgements.pdf')} target="_blank">Acknowledgements</a> | 
					<a href="https://www.youtube.com/watch?v=YOUR_VIDEO_ID" target="_blank">Watch Video ↗</a>
				</p>
			</div>
			<div class="footer-right">
				<p class="course-info">Data Visualization • CMU • Fall 2025</p>
			</div>
		</div>
	</footer>
</div>

<!-- closes slideshow-wrapper -->

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

	.pill-button-font {
		font-family: fustat;
		font-size: 0.85em;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}

	.pill-button-sub {
		font-family: fustat;
		font-size: 0.7em;
		font-weight: 500;
		margin: 0;
		color: #666;
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

	.slide-section-content {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.page-container {
		width: 100%;
		margin: 0 auto;
		padding: 0;
	}

	.intro-container {
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

	.news-holder {
		margin-bottom: 40px;
		max-width: 850px;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.charts-container {
		display: flex;
		justify-content: space-between;
		/* border: 1px solid #ccc;
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.1); */
		user-select: none;
		-webkit-user-select: none;
	}

	.mid-chart {
		margin-top: 2em;
	}

	.graphic {
		margin: 3em auto;
	}

	.title-inflation {
		display: flex;
		justify-content: space-between;
		align-items: end;
		margin-bottom: 2em;
	}

	.generic-v-brand {
		margin-top: 2em;
	}

	.exploreOtherDrugs {
		padding-left: 2.8em;
	}

	.drugs-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.8em;
		max-width: 1200px;
		min-width: 850px;
		margin: 0 auto;
		padding: 2em 0;
	}

	.drug-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 0.5em;
		background: transparent;
		border: none;
		cursor: pointer;
		transition: transform 0.2s ease;
	}

	.drug-card:hover {
		transform: translateY(-2px);
	}

	.drug-image {
		width: 75px;
		height: 75px;
		object-fit: contain;
		margin-bottom: 0.5em;
	}

	.text-button {
		padding: 0.1em 0.8em;
		background: #edeae2;
		border-radius: 6px;
		transition: background-color 0.2s ease;
		width: 100%;
	}

	.drug-card:hover .text-button {
		background-color: #d1d4d9;
	}

	.text-button.selected {
		background-color: #d1d4d9;
	}

	.drug-card h5 {
		margin: 0.2em 0 0.1em 0;
		text-align: center;
	}

	.drug-card h6 {
		margin: 0;
		text-align: center;
	}

	.pillBottle {
		width: 150px;
		height: auto;
	}

	.question {
		font-size: 8em;
		color: #8d8d8d;
	}

	.bottle-illustration {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 4em;
		margin-top: 2em;
	}

	.card-holder {
		max-width: 850px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 2em;
	}

	.company-cards {
		width: 30%;
		height: 18em;
		background-color: #355b75;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		padding: 1em;
		border-radius: 6px;
		color: white;
	}

	.card-label {
		text-align: center;
	}

	.card-image {
		width: 100px;
		height: 100px;
	}

	/* Footer Styles */
	.footer {
		margin-top: 4em;
		padding: 2em 0 1.5em 0;
		border-top: 1px solid #ddd;
	}

	:global(.dark) .footer {
		border-top: 1px solid #333;
	}

	.footer-content {
		max-width: 850px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 2em;
	}

	.footer-left {
		flex: 1;
		text-align: left;
	}

	.footer-right {
		text-align: right;
		white-space: nowrap;
	}

	.footer p {
		font-family: fustat;
		font-size: 0.85em;
		color: #818181;
		margin: 0.3em 0;
	}

	.footer a {
		color: #818181;
		text-decoration: underline;
		transition: color 0.2s ease;
	}

	.footer a:hover {
		color: #c9381a;
	}

	.team {
		font-weight: 600;
	}

	.acknowledgements {
		font-size: 0.8em;
	}

	.course-info {
		font-size: 0.85em;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	@media (max-width: 768px) {
		.footer-content {
			flex-direction: column;
			align-items: center;
			text-align: center;
			gap: 1em;
		}

		.footer-left,
		.footer-right {
			text-align: center;
		}
	}


</style>
