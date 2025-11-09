<script lang="ts">
	import type { PageProps } from './$types';
	import {asset } from '$app/paths';


	let { data }: PageProps = $props();
</script>

<div class="title-holder">
	<div class="title">
		<h1 class="headerTitle">Do You Know the <u>Actual Cost</u> of Your Medications?</h1>
		<h2>a subtitle will go here</h2>
	</div>
	<div class="pillsImages"> 
		<img class="pillpics" src={asset('/images/pill01.png')} alt="red pill illustration"/>
		<img class="pillpics" src={asset('/images/pill02.png')} alt="blue pill illustration"/>
		<img class="pillpics" src={asset('/images/pill03.png')} alt="tan pill illustration"/>
	</div>
</div>

<style>
	/* global(sheet) styling */

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
		font-family: fustat;
		font-size: 32px;
		font-weight: 700;
		text-transform: uppercase;
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
		display: flex;
		align-items: center;
	}

	.pillpics {
		position: absolute;
	}


</style>
