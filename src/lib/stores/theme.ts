import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function createDarkModeStore() {
	const { subscribe, set } = writable(false);

	return {
		subscribe,
		init: () => {
			if (browser) {
				const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
				set(isDark);

				// Listen for changes
				window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
					set(e.matches);
				});
			}
		}
	};
}

export const isDarkMode = createDarkModeStore();
