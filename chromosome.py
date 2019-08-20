from random import randint, sample

class Chromosome:


    def __init__(self, route, date, start_secs, end_secs, predictors, predicted_wait_interps):
        self.date = date
        self.start_secs = start_secs
        self.end_secs = end_secs
        self.__cached_fitness = -1
        self.route = route
        self.predictors = predictors
        self.predicted_waits_interps = predicted_wait_interps

    def get_fitness(self):
        if self.__cached_fitness != -1:
            return self.__cached_fitness

        time_secs = self.start_secs
        fitness = -1
        for ride in self.route:
            wait = 60*self.predictors[ride].predict(self.date, time_secs, self.predicted_waits_interps[ride][self.date]([time_secs])[0])
            time_secs += wait + 600
            if time_secs > self.end_secs:
                fitness = self.end_secs - self.start_secs
                break
        if fitness == -1:
            fitness = time_secs - self.start_secs
        self.__cached_fitness = 1e6/fitness
        return self.__cached_fitness

    def mutate(self):
        mutated_route = self.route.copy()
        index1 = randint(0,len(mutated_route)-1)
        index2 = index1
        while index1 == index2:
            index2 = randint(0,len(mutated_route)-1)

        mutated_route.insert(index2,mutated_route[index1])
        if index1 > index2:
            del mutated_route[index1+1]
        else:
            del mutated_route[index1]

        return Chromosome(mutated_route, self.date, self.start_secs, self.end_secs, self.predictors, self.predicted_waits_interps)

    @staticmethod
    def crossover(parent1, parent2):
        rides_index_list = [i for i in range(len(parent1.route))]
        parent1_indices = set(sample(rides_index_list, randint(0, len(rides_index_list))))
        from_parent1 = set([parent1.route[i] for i in parent1_indices])

        offspring1_route = parent1.route.copy()
        for_offspring2_route = []
        j = 0
        for i in range(0, len(offspring1_route)):
            if i not in parent1_indices:
                while parent2.route[j] in from_parent1:
                    j += 1
                offspring1_route[i] = parent2.route[j]
                j += 1
                for_offspring2_route.append(parent1.route[i])

        offspring2_route = parent2.route.copy()
        j = 0
        for i in range(0, len(offspring2_route)):
            if offspring2_route[i] not in from_parent1:
                offspring2_route[i] = for_offspring2_route[j]
                j += 1

        return Chromosome(offspring1_route, parent1.date, parent1.start_secs, parent1.end_secs, parent1.predictors, parent1.predicted_waits_interps), \
               Chromosome(offspring2_route, parent1.date, parent1.start_secs, parent1.end_secs, parent1.predictors, parent1.predicted_waits_interps)






