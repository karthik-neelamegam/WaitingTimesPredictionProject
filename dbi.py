import mysql.connector as mysql
class DBI:
    def __init__(self):
        self.__db = mysql.connect(
            host="localhost",
            user="root",
            passwd="jibbletastic",
            database="waiting_times",
            use_pure = True
        )
        self.__db.autocommit = False
        self.__cursor = self.__db.cursor()
        self.__ride_ids = self.get_ride_ids()

    def get_ride_ids(self):
        ride_ids = {}
        self.__cursor.execute("SELECT id, ride FROM rides;")
        results = self.__cursor.fetchall()
        for result in results:
            ride_ids[result[1]] = result[0]
        return ride_ids

    def __get_ride_id(self, ride):
        if ride in self.__ride_ids:
            return self.__ride_ids[ride]
        self.__cursor.execute("SELECT id FROM rides WHERE ride = %s;", (ride,))
        results = self.__cursor.fetchall()
        if len(results) == 0:
            self.__cursor.execute("INSERT INTO rides (ride) VALUES (%s);", (ride,))
            ride_id = self.__cursor.lastrowid
        else:
            ride_id = results[0][0]
        self.__ride_ids[ride] = ride_id
        return ride_id


    def insert_wait(self, date, hour, minute, second, ride, wait_type, wait):
        if(wait > 1000 or wait < 0):
            # clearly error
            print("TIME_VAL OUT OF RANGE: " + date + " " + str(hour) + ":" + str(minute) + ":" + str(second) + " " + ride + " " + str(wait))
            return
        table = "%s_times" % wait_type
        sql = "INSERT INTO " + table + " (ride_id, date, hour, minute, second, value) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id;"
        self.__cursor.execute(sql, (self.__get_ride_id(ride), date, hour, minute, second, wait))

    def get_waits(self, wait_type, start_date=None, end_date=None, ride=None, ride_id=None, order_by_date=True, limit=0):
        table = "%s_times" % wait_type
        where = " WHERE 1 "
        order = ""
        limit_str = ""
        args = []
        if end_date:
            where += " AND date <= %s "
            args.append(end_date)
        if end_date:
            where += " AND date >= %s "
            args.append(start_date)
        if ride:
            where += " AND ride_id = %s "
            args.append(self.__get_ride_id(ride))
        if ride_id:
            where += " AND ride_id = %s "
            args.append(ride_id)
        if order_by_date:
            order = " ORDER BY date"
        if limit > 0:
            limit_str = " LIMIT %s "
            args.append(limit)
        sql = "SELECT date, hour, minute, second, value FROM " + table + where + order + limit_str
        self.__cursor.execute(sql, tuple(args))
        return self.__cursor.fetchall()

    def commit(self):
        self.__db.commit()

    def close(self):
        self.__db.commit()
        self.__cursor.close()
        self.__db.close()
        print("Connection is closed.")
