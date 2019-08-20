from model import RideWaitPredictor
from scraper import Scraper
from genetic_algorithm import GeneticAlgorithm

class Planner:


    def __init__(self, start_datetime, end_datetime, rides, dbi, load_models=False, load_fls=False):
        self.__dbi = dbi
        self.__rides = rides
        self.__predictors = self.__set_up_predictors(load_models, load_fls)
        self.__predicted_waits_interps = self.__load_predicted_waits_interps(start_datetime.date())
        self.__date = start_datetime.date()
        self.__start_secs = start_datetime.hour*3600+start_datetime.minute*60+start_datetime.second
        self.__end_secs = (end_datetime-start_datetime).total_seconds() + self.__start_secs

    def __set_up_predictors(self, load_models, load_fls):
        predictors = {}
        for ride in self.__rides:
            predictors[ride] = RideWaitPredictor(ride, self.__dbi, load_models, load_fls)
        return predictors

    def __load_predicted_waits_interps(self, date):
        scraper = Scraper(self.__dbi)
        predicted_waits_interps = {}
        for ride in self.__rides:
            predicted_waits_interps[ride] = RideWaitPredictor.get_predicted_waits_interps(pred_waits=scraper.get_predicted_waits(date, ride=ride))
        print(predicted_waits_interps)
        return predicted_waits_interps

    def get_optimal_route(self):
        ga = GeneticAlgorithm(self.__rides, self.__date, self.__start_secs, self.__end_secs, self.__predictors, self.__predicted_waits_interps, 1000, 1000)
        return ga.get_optimal_route()

"""
from datetime import datetime
from dbi import DBI
d = DBI()
rs = d.get_ride_ids()
rlist = []
for r in rs:
    if r not in {"Astro Orbiter", "Walt Disney World Railroad - Fantasyland", "Walt Disney World Railroad - Frontierland", "Walt Disney World Railroad - Main Street, U.S.A."}:
        rlist.append(r)
    if len(rlist) == 13:
        break

print(rlist)
p = Planner(datetime(2019,8,18,10,0,0), datetime(2019,8,18,23,0,0), rlist, d, True, True)
print(p.get_optimal_route())
"""