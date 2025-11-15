<script lang="ts">
    let items : Array<string> = ['test', 'test', 'test', 'test', 'test'];

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
  {#each items as item}
    <div class="background-source" style="background-color: {colors.cream}">{item}</div>
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
  }

  .background-source {
    padding: 10px;
    margin-bottom: 10px;
  }

  </style>