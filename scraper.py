import requests
import re
import datetime
from bs4 import BeautifulSoup
from dbi import DBI

class Scraper:

    def __init__(self, dbi):
        self.__dbi = dbi
        self.__TITLE_REGEX = re.compile("title: \"(.*) - [\d/]+?\"")
        self.__WAIT_ROWS_REGEX = re.compile("\[new Date.*?\]")
        self.__WAIT_VALS_OLD_REGEX = re.compile("new Date\( (.*?) \),.*?,.*?,.*?,(.*?),(.*?),(.*?),(.*?),(.*?)")
        self.__WAIT_VALS_RECENT_REGEX = re.compile("new Date\( (.*?) \),(.*?)")

    def __get_html(self, date):
        url = "http://touringplans.com/magic-kingdom/wait-times/date/"+date.strftime("%Y-%m-%d")
        response = requests.get(url=url)
        return response.text

    def __get_rides_scripts(self, date):
        html = self.__get_html(date)
        soup = BeautifulSoup(html, features = "lxml")
        overview = soup.find("ul", class_="overview")
        if not overview:
            print("No wait data found")
            return
        return overview.find_all("li")


    def __scrape_html(self, date):

        old = (datetime.date.today()-date).days > 1
        wait_vals_regex = self.__WAIT_VALS_OLD_REGEX if old else self.__WAIT_VALS_RECENT_REGEX

        rides_scripts = self.__get_rides_scripts(date)
        if not rides_scripts:
            return

        for ride_script in rides_scripts:
            script_str = str(ride_script)
            ride_name = re.findall(self.__TITLE_REGEX, script_str)[0]
            time_rows = re.findall(self.__WAIT_ROWS_REGEX, script_str)

            for row in time_rows:
                all_values = re.findall(wait_vals_regex, row)
                for values in all_values:
                    dt = values[0]
                    dt_values = dt.split(",")
                    hour = int(dt_values[3])
                    if hour >= 0 and hour < 4:
                        hour += 24
                    min = int(dt_values[4])
                    sec = int(dt_values[5])
                    datestr = date.strftime("%Y-%m-%d")

                    if len(values[1]) > 0:
                        pred = int(values[1])
                        self.__dbi.insert_wait(datestr, hour, min, sec, ride_name, "predicted", pred)

                    if not old:
                        continue

                    if len(values[2]) > 0:
                        adj = int(values[2])
                        self.__dbi.insert_wait(datestr, hour, min, sec, ride_name, "adjusted", adj)

                    if len(values[3]) > 0:
                        acc = int(values[3])
                        self.__dbi.insert_wait(datestr, hour, min, sec, ride_name, "actual", acc)

                    if len(values[4]) > 0:
                        post = int(values[4])
                        self.__dbi.insert_wait(datestr, hour, min, sec, ride_name, "posted", post)

                    if len(values[5]) > 0:
                        obs = int(values[5])
                        self.__dbi.insert_wait(datestr, hour, min, sec, ride_name, "observed", obs)

    def get_predicted_waits(self, date, ride=None):
        waits = self.__dbi.get_waits("predicted", start_date=date, end_date=date, ride=ride)
        if len(waits) > 0:
            return waits
        else:
            print("reached")
            self.run_scrape(date, date)
        return self.__dbi.get_waits("predicted", start_date=date, end_date=date, ride=ride)

    def run_scrape(self, start_date, end_date):
        #Last date completed: 2019.8.17
        date = start_date
        while date <= end_date:
            print(date.strftime("%Y-%m-%d"))
            self.__scrape_html(date)
            date = date + datetime.timedelta(days=1)
            self.__dbi.commit()