from random import shuffle, uniform
from chromosome import Chromosome

class GeneticAlgorithm:


    def __init__(self, rides, date, start_secs, end_secs, predictors, predicted_waits_interps, initial_population_size, num_generations):
        self.__population = []
        self.__initial_population_size = initial_population_size
        self.__rides = rides
        self.__date = date
        self.__start_secs = start_secs
        self.__end_secs = end_secs
        self.__predictors = predictors
        self.__predicted_waits_interps = predicted_waits_interps
        self.__num_generations = num_generations
        self.__cached_total_fitness = -1
        self.__best_fitness = -1
        self.__best_chromosome = None

    def __generate_initial_population(self, size):
        population = []
        for route in [self.__rides.copy() for i in range(size)]:
            shuffle(route)
            population.append(Chromosome(route, self.__date, self.__start_secs, self.__end_secs, self.__predictors, self.__predicted_waits_interps))

        return population

    def __sort_population(self):
        self.__population.sort(key=lambda chromo:chromo.get_fitness())

    def __calculate_total_fitness(self):
        if self.__cached_total_fitness != -1:
            return self.__cached_total_fitness

        total = 0
        for c in self.__population:
            fitness = c.get_fitness()

            if fitness > self.__best_fitness:
                self.__best_fitness = fitness
                self.__best_chromosome = c
            total += fitness

        self.__cached_total_fitness = total
        return total

    def __select(self, exception=-1):
        total_fitness = self.__calculate_total_fitness()
        threshold = uniform(0,1)
        threshold_fitness = threshold * total_fitness
        cumulative_fitness = 0
        for i in range(len(self.__population)):
            c = self.__population[i]
            cumulative_fitness += c.get_fitness()
            if cumulative_fitness >= threshold_fitness:
                if i != exception:
                    return c, i
                elif i == 0:
                    return self.__population[1], 1
                else:
                    return self.__population[i-1], i-1
        return self.__population[-1], -1

    def __run(self):
        self.__population = self.__generate_initial_population(self.__initial_population_size)

        generation = 0
        while generation <= self.__num_generations:
            c1, i1 = self.__select()
            c2, i2 = self.__select(i1)
            print("Best fitness: ", self.__best_fitness)
            c3, c4 = Chromosome.crossover(c1, c2)
            c5, c6 = c1.mutate(), c2.mutate()

            cands = [c3,c4,c5,c6]
            if c1.get_fitness() > c2.get_fitness():
                max_fitness, second_fitness = c1.get_fitness(), c2.get_fitness()
                best_cand, second_cand = c1, c2
            else:
                max_fitness, second_fitness = c2.get_fitness(), c1.get_fitness()
                best_cand, second_cand = c2, c1

            for cand in cands:
                fitness = cand.get_fitness()
                if fitness > max_fitness:
                    second_fitness = max_fitness
                    max_fitness = fitness
                    second_cand = best_cand
                    best_cand = cand
                elif fitness > second_fitness:
                    second_fitness = fitness
                    second_cand = cand
            self.__population[i1] = best_cand
            self.__population[i2] = second_cand
            if not (best_cand == c1 and second_cand == c2 or best_cand == c2 and second_cand == c1):
                self.__cached_total_fitness = -1

            generation += 1

    def get_optimal_route(self):
        self.__run()
        self.__calculate_total_fitness()
        return self.__best_chromosome.route
