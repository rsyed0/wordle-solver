from random import random, randint
from copy import deepcopy

import sys

# use genetic algorithms
# modify number/position of letters 
# initial guess, etc

p_mutation = 0.05
size_mutation = 0.35
pop_size = 50
n_generations = 15
survivor_ratio = 0.1
repeat_prob_adj = 0.25

n_feature_models = 25
n_feature_words = 25

words_per_gen = 10

letters_per_word = 5

# TODO decide whether to keep or not
words = [str(x)[:-1] for x in open("wordle_words.txt","r").readlines()]
rep_char = []
wd = dict()
for w in words:
	w_srt = "".join(sorted([c for c in w]))
	for i in range(32):
		bi = str(bin(i))[2:]
		bi = ("0"*(letters_per_word-len(bi))) + bi
		#print(w)
		key = "".join([w_srt[i] if bi[i] == '1' else '' for i in range(letters_per_word)])
		if key in wd:
			wd[key].append(w)
		else:
			wd[key] = [w]

wp = dict()
for w in words:
	for i in range(32):
		bi = str(bin(i))[2:]
		bi = ("0"*(letters_per_word-len(bi))) + bi
		#print(w)
		key = "".join([w[i] if bi[i] == '1' else '*' for i in range(letters_per_word)])
		if key in wp:
			wp[key].append(w)
		else:
			wp[key] = [w]

def pick_i(model):
	r = random()
	for i in range(26):
		if r <= model[i]:
			return i
		else:
			r -= model[i]
	return -1

def evaluate(guess, answer):
	#print(guess,answer)
	#g_l, a_l = [c for c in guess], [c for c in answer]
	a_l = [c for c in answer]

	# first check for direct matches (2)
	out = [0] * letters_per_word
	for i in range(letters_per_word):
		if guess[i] == answer[i]:
			out[i] = 2
			#g_l.remove(guess[i])
			a_l.remove(answer[i])

	# then for indirect matches (1)
	for i in range(letters_per_word):
		if out[i] == 2:
			continue
		elif guess[i] in a_l:
			out[i] = 1
			a_l.remove(guess[i])

	return out

def guess(model, past_guesses, answer, verbose=False):
	eval_res = []
	#print(past_guesses)
	if len(past_guesses) > 0:
		#print(past_guesses[-1])
		eval_res = evaluate(past_guesses[-1], answer)
	else:
		eval_res = [0,0,0,0,0]

	#print("generating a guess...")

	if verbose:
		print(eval_res)

	gd = "".join([answer[i] if eval_res[i] > 0 else "" for i in range(letters_per_word)])
	gp = "".join([answer[i] if eval_res[i] == 2 else "*" for i in range(letters_per_word)])

	#wgd, wgp = wd[gd], wp[gp]
	wgd = wp[gp]
	if len(wgd) == 1:
		return wgd[0]

	# get past guessed letters that aren't in answer
	not_in = set()
	for pg in past_guesses:
		#er = evaluate(pg, answer)
		for i in range(letters_per_word):
			c = pg[i]
			if c not in answer:
				not_in.add(c)

	yellow = []
	for i in range(letters_per_word):
		if eval_res[i] == 1:
			yellow.append(past_guesses[-1][i])

	y_set = set(yellow)
	y_inds = {ys:set() for ys in y_set}
	for c in y_set:
		for pg in past_guesses:
			for i in range(letters_per_word):
				if pg[i] == c and not pg[i] == answer[i]:
					y_inds[c].add(i)

	#print(past_guesses, not_in, yellow, eval_res, answer)

	if verbose:
		print("yellow: "+str(yellow))

	pg_set = set(past_guesses)
	#try:
	max_w, max_score = "", -1.0
	for w in wgd:
		score = 0.0
		valid = True
		extras = []
		for i in range(letters_per_word):
			c = w[i]
			if (gp[i] == "*" and c in not_in) or w in pg_set or (c in y_inds and i in y_inds[c]):
				#print("a")
				valid = False
				break
			if not eval_res[i] == 2:
				extras.append(w[i])
			score += model[ord(c)-ord('a')]
			model[ord(c)-ord('a')] *= repeat_prob_adj

		if not valid:
			continue

		#print(w,end=" ")
		for c in yellow:
			if c not in extras:
				#print("b")
				valid = False
				break
			else:
				extras.remove(c)

		if valid and score > max_score:
			max_score = score
			max_w = w
	"""except KeyboardInterrupt:
		print(model)
		print(sum(model))
		sys.exit()"""

	if max_score >= 0:
		return max_w
	else:
		print("max score fail")
		sys.exit()
		return ""

def cross(model_a, model_b, n_children=2):
	# equal weighted sum of both probs
	model_c = [(a+b)/2 for a,b in zip(model_a, model_b)]

	# plus random mutation(s)
	out = []
	for nc in range(n_children):
		mc = deepcopy(model_c)
		for i in range(26):
			if random() < p_mutation:

				# TODO experiment with different mutation systems
				"""i,j = -1,-1
				while i == j:
					i,j = randint(0,25), randint(0,25)

				delta = random()*mc[j]
				mc[j] -= delta
				mc[i] += delta"""

				mc[i] += random()*size_mutation

		out.append(mc)
	return out

def main():
	population = []
	for i in range(pop_size):
		probs = [0.0 for j in range(26)]
		n, pl = 26, 1.0
		while n > 0 and pl > 0.0:
			ri = randint(0,25)
			if probs[ri] == 0.0:
				probs[ri] = random()*pl
				pl -= probs[ri]
				n -= 1
		population.append(probs)

	n_survivors = int(survivor_ratio*pop_size)
	ordered_models = None

	# implement generations
	for g in range(n_generations):
		print("Generation "+str(g+1)+" of "+str(n_generations))

		n_guesses = [0] * pop_size
		for w in range(words_per_gen):
			answer = words[randint(0,len(words)-1)]
			past_guesses = [[] for i in range(pop_size)]
			n = pop_size

			while n > 0:
				for i in range(pop_size):
					if not past_guesses[-1] == answer:
						next_guess = guess(population[i][:], past_guesses[i], answer)
						past_guesses[i].append(next_guess)

						if next_guess == answer:
							n -= 1

						if len(next_guess) == 0:
							# failed to get a valid guess
							pass

			for i in range(pop_size):
				n_guesses[i] += len(past_guesses[i])

		# order models in reverse order of len(past_guesses[i])
		ordered_models = [population[j] for j in sorted([i for i in range(pop_size)], key=lambda x: n_guesses[x])]

		next_pop = ordered_models[:3]
		for i in range(n_survivors):
			for j in range(i+1, n_survivors):
				next_pop.extend(cross(ordered_models[i], ordered_models[j], 1))
			if len(next_pop) >= pop_size:
				population = next_pop[:pop_size]
				break

	# score best few models against a sample of words
	n_guesses = [0] * n_feature_models
	wins = [0] * n_feature_models
	for j in range(n_feature_words):
		answer = words[randint(0,len(words)-1)]

		for i in range(n_feature_models):
			pg = []

			while len(pg) == 0 or not pg[-1] == answer:
				next_guess = guess(ordered_models[i][:], pg, answer)
				pg.append(next_guess)

			n_guesses[i] += len(pg)
			wins[i] += 1 if len(pg) <= 6 else 0

	m_guesses, m_i = 2**31 - 1, -1
	for i in range(n_feature_models):
		if m_guesses > n_guesses[i]:
			m_i = i
		print("Avg guesses: " + str(n_guesses[i]/n_feature_words) + ", wins: " + str(wins[i]) + " / " + str(n_feature_words))

	best_model = ordered_models[i]
	print(best_model)
	for i in range(len(words)):
		w = words[randint(0,len(words)-1)]
		print("Goal word: "+w)

		pg = []
		while len(pg) == 0 or not pg[-1] == w:
			g = guess(best_model[:], pg, w, False)
			pg.append(g)
			print("Guess: "+g)

		input("")

if __name__ == "__main__":
	main()