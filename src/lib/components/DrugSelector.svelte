<script lang="ts">
	// Define the drug list matching the order in your brandDrugs array
	// These indices match your radio button order
	const brandDrugs = [
		{ name: 'LAMICTAL', displayName: 'LAMICTAL', index: 0 },
		{ name: 'LANTUS', displayName: 'LANTUS', index: 1 },
		{ name: 'LEXAPRO', displayName: 'LEXAPRO', index: 2 },
		{ name: 'LIPITOR', displayName: 'LIPITOR', index: 3 },
		{ name: 'LYRICA', displayName: 'LYRICA', index: 4 },
		{ name: 'NEURONTIN', displayName: 'NEURONTIN', index: 5 },
		{ name: 'NORVASC', displayName: 'NORVASC', index: 6 },
		{ name: 'PROVIGIL', displayName: 'PROVIGIL', index: 7 },
		{ name: 'PROZAC', displayName: 'PROZAC', index: 8 },
		{ name: 'SYNTHROID', displayName: 'SYNTHROID', index: 9 },
		{ name: 'VYVANSE', displayName: 'VYVANSE', index: 10 },
		{ name: 'ZOLOFT', displayName: 'ZOLOFT', index: 11 }
	];

	// Props
	interface Props {
		selectedDrugIndex?: number;
		onDrugChange?: (index: number) => void;
		label?: string;
		showLabel?: boolean;
		compact?: boolean;
	}

	let { 
		selectedDrugIndex = $bindable(8), 
		onDrugChange,
		label = "Select Drug:",
		showLabel = true,
		compact = false
	}: Props = $props();

	// Handle dropdown change
	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		const newIndex = parseInt(target.value);
		selectedDrugIndex = newIndex;
		
		// Call optional callback
		if (onDrugChange) {
			onDrugChange(newIndex);
		}
	}
</script>

<div class="drug-selector-wrapper" class:compact>
	<!-- {#if showLabel}
		<label for="drug-select" class="drug-label">{label}</label>
	{/if} -->
	<select 
		id="drug-select"
		class="drug-dropdown"
		bind:value={selectedDrugIndex}
		onchange={handleChange}
	>
		{#each brandDrugs as drug}
			<option value={drug.index}>
				{drug.displayName}
			</option>
		{/each}
	</select>
</div>

<style>
	.drug-selector-wrapper {
		display: flex;
		align-items: center;
	}

	.drug-label {
		font-family: Antonio;
		font-size: 1em;
		font-weight: 600;
		white-space: nowrap;
	}

	.drug-dropdown {
		font-family: fustat;
		font-size: 1em;
		border: 1px solid #ccc;
		border-radius: 4px;
		background-color: rgba(75, 75, 75, 0.1);
		cursor: pointer;
		min-width: 240px;
		padding: 4px 10px ;
	}

	.drug-dropdown:focus {
		outline: 2px solid #54707c;
	}

	.drug-dropdown:hover {
		background-color: rgba(75, 75, 75, 0.15);
	}
</style>