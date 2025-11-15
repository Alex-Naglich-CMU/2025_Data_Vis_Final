<script lang="ts">

    const sources = [
        {
            link: "https://priceschool.usc.edu/news/drug-prices-trump-executive-order-cost/",
            headline: "Why do Americans pay more for prescription drugs?"
        },
        {
            link: "https://www.healthday.com/healthpro-news/general-health/price-of-prescription-drugs-almost-threefold-higher-in-the-united-states?utm_ ",
            headline: "Price of Prescription Drugs Almost Threefold Higher in the United States"
        },
        {
            link: "https://www.healthday.com/healthpro-news/general-health/price-of-prescription-drugs-almost-threefold-higher-in-the-united-states?utm_ ",
            headline: "Price of Prescription Drugs Almost Threefold Higher in the United States"
        },
        {
            link: "https://www.healthday.com/healthpro-news/general-health/price-of-prescription-drugs-almost-threefold-higher-in-the-united-states?utm_ ",
            headline: "Price of Prescription Drugs Almost Threefold Higher in the United States"
        }
    ];

    const colors = {
		red: '#9A2F1F',
		blue: '#54707C',
		green: '#3F5339',
		orange: '#DF7C39',
		tan: '#BFA97F',
		cream: '#F6F5EC'
	};

</script>
 

<div class="background-scroll">
  {#each sources as source}
    <a href={source.link} target="_blank" rel="noopener noreferrer">
        <div class="background-source" style="background-color: {colors.cream}">
            {source.headline}
        </div>
     </a>
  {/each}
</div>

<style>
  .background-scroll {
    margin-left: 40px;
    width: 900px;
    height: 200px;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 10px;
    box-shadow: 0 0 3px #ccc inset;    
  }

  .background-source {
    padding: 10px;
    margin-bottom: 10px;
    box-shadow: 0 0 5px #ccc;
  }

</style>