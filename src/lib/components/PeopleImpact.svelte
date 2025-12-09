<script lang="ts">
	import { asset } from '$app/paths';

    const brandDrugs = [
        { name: 'LANTUS', image: '/images/drug-selections/Lantus.png'},
		{ name: 'LANTUS', image: '/images/drug-selections/Lantus.png' },
		{ name: 'LEXAPRO', image: '/images/drug-selections/Lexapro.png' },
		{ name: 'LIPITOR', image: '/images/drug-selections/Lipitor.png'},
		{ name: 'LYRICA', image: '/images/drug-selections/Lyrica.png' },
        { name: 'NEUROTIN', image: '/images/drug-selections/Neurotin.png' },
		{ name: 'NORVASC', image: '/images/drug-selections/Norvasc.png' },
		{ name: 'PROVIGIL', image: '/images/drug-selections/Provigil.png' },
		{ name: 'PROZAC', image: '/images/drug-selections/Prozac.png' },
        { name: 'SYNTHROID', image: '/images/drug-selections/Synthroid.png' },
		{ name: 'VYVANSE', image: '/images/drug-selections/Vyvance.png' },
		{ name: 'ZOLOFT', image: '/images/drug-selections/Zoloft.png' }
	];


</script>

<div class="graphic-container">
    <div class="people-graphic">
        <div class='impact-item'>
            <h4>3 in 10 adults report not taking their medication as prescribed</h4>
        </div>
        <div class='images'>
            <img class="statTrue" src={asset('/images/Person-Icon.svg')} alt="dark blue person icon" />
            <img class="statTrue" src={asset('/images/Person-Icon.svg')} alt="dark blue person icon" />
            <img class="statTrue" src={asset('/images/Person-Icon.svg')} alt="dark blue person iconn" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
            <img class="statFalse" src={asset('/images/Person-Icon.svg')} alt="ligh blue person icon" />
        </div>
        <a 
            class='source'
            href='https://www.ama-assn.org/public-health/behavioral-health/how-are-prescription-drug-prices-determined#:~:text=Prescription%20drug%20price%20increases%20can,to%20demand%20drug%20price%20transparency.' 
            target="_blank" 
            rel="noopener noreferrer"
        > ama-assn.org/public-health
        </a>
    </div>
    
</div>

<style>

    h4 {
		font-family: fustat;
		font-size: 1.3em;
		font-weight: 700;
	}

    .graphic-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }

    .people-graphic {
        width: 600px;
        display: flex;
        flex-direction: column;
        justify-content: start;
    }


	.impact-item {
		margin-bottom: 3em;
	}

    .images {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: .5em;
    }

    .statFalse {
        opacity: 60%;
        width: 40px;
        height: auto;
    }

    .statTrue {
        width: 40px;
        height: auto;
    }

    .source {
        font-family: fustat;
        font-size: .5em;
        color: #818181;
    }

</style>