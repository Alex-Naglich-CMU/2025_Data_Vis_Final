import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		watch: {
			// Ignore the large prices data folder to prevent unnecessary HMR triggers
			ignored: ['**/src/lib/data/prices/**']
		}
	}
});
