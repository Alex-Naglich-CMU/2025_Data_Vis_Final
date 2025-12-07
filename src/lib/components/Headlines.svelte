<script lang="ts">
	import { asset } from '$app/paths';

	const colors = {
		red: '#9A2F1F',
		blue: '#54707C',
		green: '#3F5339',
		orange: '#DF7C39',
		tan: '#BFA97F',
		cream: '#F6F5EC'
	};

	// scrollable section with headlines and URLs
	const sources = [
		{
			icon: '/images/mediaCompanies/hd.png',
			link: 'https://www.healthday.com/healthpro-news/general-health/price-of-prescription-drugs-almost-threefold-higher-in-the-united-states?utm_ ',
			headline: 'Price of Prescription Drugs Almost Threefold Higher in the United States'
		},
		{
			icon: '/images/mediaCompanies/healthleaders.png',
			link: 'https://www.healthleadersmedia.com/strategy/us-prescription-drugs-cost-highest-world-far?',
			headline: 'U.S. Prescription Drugs Cost Highest in the World, By Far'
		},
		{
			icon: '/images/mediaCompanies/wsj.png',
			link: 'https://www.wsj.com/health/pharma/trump-tax-spending-bill-drug-prices-medicare-5465f4e2?gaa_at=eafs&gaa_n=AWEtsqf94pD78yDPPo85pAeFyqZxHVM9DIDbZ6wtl5v9VrPIq8C1-0Va5HtY37Cla9Y%3D&gaa_ts=69189055&gaa_sig=1aIcHrJOuEt0o2Le7mpkAOJmIcXTHM8kb9cHt7KT6LT3io4198Dncos1iQg3f_ocFIBeZX_aPcsdPGPpFjZTng%3D%3D',
			headline: 'Why Drug Prices for Some Big Medicines Will Remain High for a Longer Time'
		},
		{
			icon: '/images/mediaCompanies/bloomberg.png',
			link: 'https://www.bloomberg.com/news/articles/2025-11-07/why-us-drug-prices-are-so-high-can-trump-really-cut-them',
			headline: 'Why Are US Drug Prices So High? Can Trump Really Make Them Cheaper?'
		},
		{
			icon: '/images/mediaCompanies/gao.png',
			link: 'https://www.gao.gov/products/gao-21-282?utm',
			headline:
				'U.S. Prices for Selected Brand Drugs Were Higher on Average than Prices in Australia, Canada, and France'
		},
		{
			icon: '/images/mediaCompanies/nbc.png',
			link: 'https://www.nbcnews.com/health/health-news/taking-fewer-medications-key-lowering-drug-costs-us-rcna203539',
			headline: 'Is taking fewer medications the key to lowering drug costs in the U.S.?'
		},
		{
			icon: '/images/mediaCompanies/stateline.png',
			link: 'https://stateline.org/2025/10/30/dozens-of-states-tackle-high-prescription-drug-costs/',
			headline: 'Dozens of states tackle high prescription drug costs'
		}
	];
</script>

<div class="background-scroll">
	{#each sources as source}
		<a href={source.link} target="_blank" rel="noopener noreferrer">
			<div
				class="background-source"
				style="background-color: {colors.cream}; color: black"
			>
				<img class="icon" width="40px" height="40px" src={asset(source.icon)} alt="brand icon" />
				{source.headline}
			</div>
		</a>
	{/each}
</div>

<style>
	* {
		font-family: Antonio;
	}

	/* h1 {
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

	h4,
	.dropdown-label {
		font-family: fustat;
		font-size: 20px;
		font-weight: 700;
		text-transform: uppercase;
		margin-bottom: 20px;
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
	*/

	.background-scroll {
		width: 840px;
		height: 250px;
		overflow-y: auto;
		border: 1px solid #ccc;
		padding: 20px 40px 5px 20px;
		box-shadow: 0 0 3px #ccc inset;
	}

	.background-source {
		padding: 10px;
		min-height: 60px;
		margin-bottom: 15px;
		box-shadow: 0 0 5px #ccc;
		display: flex;
		align-items: center;
	}

	.icon {
		margin-right: 20px;
	}
</style>
