import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function createDarkModeStore() {
	const { subscribe, set, update } = writable(false);

	// Sync store value to body attribute
	function syncTheme(isDark: boolean) {
		if (browser) {
			document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
		}
	}

	return {
		subscribe,
		init: () => {
            // Check OS preference on init
			if (browser) {
				const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
				set(isDark);
				syncTheme(isDark);

				// Listen for OS preference changes
				window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
					set(e.matches);
					syncTheme(e.matches);
				});
			}
		},
        // Manually set mode 
		toggle: () => {
			update((value) => {
				const newValue = !value;
				syncTheme(newValue);
				return newValue;
			});
		}
	};
}

export const isDarkMode = createDarkModeStore();
