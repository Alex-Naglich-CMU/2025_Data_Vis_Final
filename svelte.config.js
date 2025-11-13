import adapter from '@sveltejs/adapter-static';

const isDev = process.argv.includes('dev');

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			fallback: '404.html'
		}),
		paths: {
			base: isDev ? '' : '/2025_Data_Vis_Final'
		}
	}
};

export default config;
