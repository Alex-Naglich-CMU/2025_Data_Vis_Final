<script lang="ts">
	import { asset } from '$app/paths';

	interface TeamMember {
		name: string;
		image: string;
		bio: string;
		preferredColor: string;
	}

	let TeamMembers: TeamMember[] = [
		{
			name: 'Anissa Patel',
			image: '/images/team/Anissa.jpeg',
			bio: 'Anissa does javvvvascript',
			preferredColor: 'oklch(87.1% 0.15 154.449)'
		},
		{
			name: 'Alex Naglich',
			image: '/images/team/Alex.png',
			bio: 'Alex is pretty cool I guess',
			preferredColor: 'oklch(83.3% 0.145 321.434)'
		},
		{
			name: 'Kim Credit',
			image: '/images/team/Kim.png',
			bio: 'Kim interacts with computers',
			preferredColor: 'oklch(86.5% 0.127 207.078)'
		}
	];
</script>

<div>
	<h2 class="m-8 text-center text-2xl font-bold">Meet the Team!</h2>
	<div class="grid grid-cols-3 overflow-hidden rounded-3xl text-center shadow-lg/20">
		{#each TeamMembers as member}
			<div
				class="row-span-3 grid grid-rows-subgrid place-items-center p-4 text-black"
				style="background-color: {member.preferredColor};"
			>
				<p class="mt-2 text-xl font-semibold">{member.name}</p>
				<img
					src={asset(member.image)}
					alt={member.name}
					class="mt-2 h-40 w-40 rounded-full object-cover"
				/>
				<div class="mt-2 px-4 text-center">
					<p class="text-sm">{member.bio}</p>
				</div>
			</div>
		{/each}
	</div>
</div>
