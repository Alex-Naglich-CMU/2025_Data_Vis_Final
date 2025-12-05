<script lang="ts">
	import { inflationCalc } from '$lib/scripts/inflation-calc';

	const brandInsulinPromise = inflationCalc('285018'); // brand - LANTUS 100 UNIT/ML VIAL
	const genericInsulinPromise = inflationCalc('311041'); // generic - INSULIN GLARGINE 100 UNIT/ML VIAL
</script>

{#await brandInsulinPromise}
	<p>Loading...</p>
{:then brandInsulin}
	<div class="comparison-container">
		<div class="price-boxes">
			<div class="price-box">
				<span class="year">{brandInsulin.oldYear}</span>
				<span class="price">${brandInsulin.oldPrice}</span>
				<span class="period">per month</span>
			</div>

			<span class="arrow">→</span>

			<div class="price-box">
				<span class="year">{brandInsulin.newYear}</span>
				<span class="price">${brandInsulin.newPrice}</span>
				<span class="period">per month</span>
			</div>
		</div>

		<p class="note">
			{Math.abs(brandInsulin.actualPercentChange)}% {brandInsulin.actualPercentChange < 0
				? 'decrease'
				: 'increase'} in price
		</p>
	</div>
{/await}

<style>
	.comparison-container {
		margin: 60px 40px;
		max-width: 750px;
	}

	/* h3 {
		font-family: Antonio;
		font-size: 32px;
		font-weight: bold;
		margin-bottom: 30px;
	} */

	.price-boxes {
		display: flex;
		align-items: center;
		gap: 40px;
	}

	.price-box {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.year {
		font-family: Fustat;
		font-size: 16px;
		text-transform: uppercase;
		font-weight: 700;
	}

	.price {
		font-family: Antonio;
		font-size: 64px;
		font-weight: bold;
	}

	.period {
		font-family: Fustat;
		font-size: 14px;
	}

	.arrow {
		font-size: 32px;
		color: #999;
	}

	.note {
		font-family: Fustat;
		font-size: 14px;
		margin-top: 20px;
		color: #666;
	}
</style>
