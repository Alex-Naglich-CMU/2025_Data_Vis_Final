/**
 * categorize dosage forms into broader buckets for visualization
 * keeps original detailed forms in JSON, but groups them for display
 * 
 * based on team's bucket definitions:
 * 1. Delayed/Extended Release Oral Capsules - must have "Capsule" AND ("Delayed" OR "Extended")
 * 2. Delayed/Extended Release Oral Tablets - must have "Tablet" AND ("Delayed" OR "Extended")
 * 3. Oral Capsule - exact match only
 * 4. Oral Tablet - exact match only
 * 5. Injection - contains "Inject" OR "Syringe"
 * 6. Inhalation - contains "Inhal"
 * 7. Topical - contains ["Topical", "Cream", "Paste", "Gel"] but NOT ["Oral", "Nasal", "Rectal", "Vaginal"]
 * 8. Other - everything else
 */

/**
 * object that kim made!
 * 	const drugForms = {
		//must have first word and then either second or third
		"Delayed/ Extended Release Oral Capsules": [ "Capsules", "Delayed", "Extended"],
		"Delayed/Extended Release Oral Tablets" : ["Tablets", "Delayed", "Extended"],
		//just true value
		"Oral Capsule" : ["Oral Capsule"],
		"Oral Tablet": ["Oral Tablet"],
		"Injection": ["Inject", "Syringe"],
		"Inhalation" : ["Inhal"],
		//doesn't include the first four, any of the rest
		"Topical" : ["Oral", "Nasal", "Rectal", "Vaginal", "Topical", "Cream", "Paste", "Gel"],
		"Other" : []
	};
 */

export function categorizeDosageForm(form: string): string {
	if (!form || form === '' || form === 'Unknown') {
		return 'Other';
	}

	const formLower = form.toLowerCase();

	// 1. delayed/extended release oral capsules
	// must have "capsule" AND ("delayed" OR "extended")
	if (
		formLower.includes('capsule') &&
		(formLower.includes('delayed') || formLower.includes('extended'))
	) {
		return 'Delayed/Extended Release Oral Capsules';
	}

	// 2. delayed/extended release oral tablets
	// must have "tablet" AND ("delayed" OR "extended")
	if (
		formLower.includes('tablet') &&
		(formLower.includes('delayed') || formLower.includes('extended'))
	) {
		return 'Delayed/Extended Release Oral Tablets';
	}

	// 3. oral capsule (exact match)
	if (form === 'Oral Capsule') {
		return 'Oral Capsule';
	}

	// 4. oral tablet (exact match)
	if (form === 'Oral Tablet') {
		return 'Oral Tablet';
	}

	// 5. injection
	// contains "inject" OR "syringe" OR "cartridge"
	if (
		formLower.includes('inject') || 
		formLower.includes('syringe') ||
		formLower.includes('cartridge')
	) {
		return 'Injection';
	}

	// 6. inhalation
	// contains "inhal" OR "inhaler"
	if (formLower.includes('inhal')) {
		return 'Inhalation';
	}

	// 7. topical
	// contains ["topical", "cream", "paste", "gel"]
	// but NOT if it contains ["oral", "nasal", "rectal", "vaginal"]
	const excludeTopical = ['oral', 'nasal', 'rectal', 'vaginal'];
	const includeTopical = ['topical', 'cream', 'paste', 'gel'];

	const hasExcluded = excludeTopical.some((term) => formLower.includes(term));
	const hasIncluded = includeTopical.some((term) => formLower.includes(term));

	if (hasIncluded && !hasExcluded) {
		return 'Topical';
	}

	// 8. everything else
	return 'Other';
}

/**
 * get all unique form categories from a list of drugs
 */
export function getFormCategories(drugs: Array<{ form: string }>): string[] {
	const categories = new Set<string>();
	for (const drug of drugs) {
		categories.add(categorizeDosageForm(drug.form));
	}
	return Array.from(categories).sort();
}

/**
 * count drugs by form category
 */
export function countByFormCategory(
	drugs: Array<{ form: string }>
): Map<string, number> {
	const counts = new Map<string, number>();
	for (const drug of drugs) {
		const category = categorizeDosageForm(drug.form);
		counts.set(category, (counts.get(category) || 0) + 1);
	}
	return counts;
}

// example usage:
// import { categorizeDosageForm } from '$lib/utils/formCategorizer';
// const category = categorizeDosageForm(priceData.Form);