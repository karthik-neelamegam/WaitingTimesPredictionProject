import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, median_absolute_error
from math import sqrt
import os.path
from os import path
from dbi import DBI
from joblib import dump, load as ld
import re


class RideWaitPredictor:


    def __init__(self, ride, dbi, load_model=False, load_fls=False):
        self.__dbi = dbi
        self.__ride = ride
        self.__ride_file_stem = re.sub(r'[\\/*?:"<>|]',"", self.__ride)
        self.__load_fls = load_fls
        if load_model:
            if path.exists("model " + self.__ride_file_stem + ".joblib") and path.exists("vectorizer " + self.__ride_file_stem + ".joblib"):
                self.__regressor = ld("model " + self.__ride_file_stem + ".joblib")
                self.__vectorizer = ld("vectorizer " + self.__ride_file_stem + ".joblib")
            else:
                print("Model or vectorizer not found for " + ride)
                self.__regressor = RandomForestRegressor(n_estimators=100)
                self.__vectorizer = DictVectorizer(sparse=False)
                self.fit()
        else:
            self.__regressor = RandomForestRegressor(n_estimators=100)
            self.__vectorizer = DictVectorizer(sparse=False)

    @staticmethod
    def get_predicted_waits_interps(dbi=None, ride=None, pred_waits=None):

        if pred_waits is None:
            pred_waits = dbi.get_waits("predicted", ride=ride)

        pred_interps = {}
        curr_date = None
        curr_date_times = []
        curr_date_waits = []

        for row in pred_waits:

            date, hour, min, sec, wait = row

            if date != curr_date or pred_waits[-1] == row:

                if curr_date:

                    curr_date_waits[0] = curr_date_waits[1]
                    curr_date_times.append(110000)
                    curr_date_waits.append(curr_date_waits[-1])
                    pred_interps[curr_date] = interp1d(np.array(curr_date_times), np.array(curr_date_waits))

                curr_date_times = [0]
                curr_date_waits = [-1]
                curr_date = date

            curr_date_times.append(3600*hour+60*min+sec)
            curr_date_waits.append(wait)

        return pred_interps

    def __extract_features_labels(self):

        if self.__load_fls:
            if path.exists("features " + self.__ride_file_stem + ".npy") and path.exists("labels " + self.__ride_file_stem + ".npy") and path.exists("vectorizer " + self.__ride_file_stem + ".joblib"):
                print("Returned load")
                self.__vectorizer = ld("vectorizer " + self.__ride_file_stem + ".joblib")
                return np.load("features " + self.__ride_file_stem + ".npy"), np.load("labels " + self.__ride_file_stem + ".npy")
            else:
                print("Could not find features, labels or vectorizer")

        pred_interps = RideWaitPredictor.get_predicted_waits_interps(dbi=self.__dbi, ride=self.__ride)

        features = []
        labels = []

        posted_waits = self.__dbi.get_waits("posted", ride=self.__ride)
        if len(posted_waits) == 0:
            return None, None

        for row in posted_waits:

            date, hour, min, sec, wait = row

            if date not in pred_interps:
                continue

            secs = 3600*hour+60*min+sec
            features.append({
                "day": str(date.weekday()),
                "month": str(date.month),
                "pred": pred_interps[date]([secs])[0],
                "secs": secs
            })
            labels.append(wait)

        features = self.__vectorizer.fit_transform(features)
        labels = np.array(labels)

        if path.exists("features " + self.__ride_file_stem + ".npy") and path.exists("labels " + self.__ride_file_stem + ".npy") and path.exists("vectorizer " + self.__ride_file_stem + ".joblib"):
            os.remove("features " + self.__ride_file_stem + ".npy")
            os.remove("labels " + self.__ride_file_stem + ".npy")
            os.remove("vectorizer " + self.__ride_file_stem + ".joblib")
        np.save("features " + self.__ride_file_stem, features)
        np.save("labels " + self.__ride_file_stem, labels)
        dump(self.__vectorizer, "vectorizer " + self.__ride_file_stem + ".joblib")

        return features, labels

    def fit(self):
        features, labels = self.__extract_features_labels()

        if features is None:
            print("NO FEATURES")
            return

        self.__regressor.fit(features, labels)
        if path.exists("model " + self.__ride_file_stem + ".joblib"):
            os.remove("model " + self.__ride_file_stem + ".joblib")
        dump(self.__regressor, "model " + self.__ride_file_stem + ".joblib")

    def predict(self, date, secs, pred):
        feature = self.__vectorizer.transform([{
            "day": str(date.weekday()),
            "month": str(date.month),
            "pred": pred,
            "secs": secs
        }])
        return self.__regressor.predict(feature)[0]

    def test(self):
        features, labels = self.__extract_features_labels()

        if features is None:
            print("NO FEATURES")
            return

        features_train, features_test, labels_train, labels_test = train_test_split(features, labels, test_size=0.33)

        self.__regressor.fit(features_train, labels_train)

        labels_our_preds = self.__regressor.predict(features_test)
        print("Mean Wait: ", np.mean(labels_test))
        our_mae = mean_absolute_error(labels_our_preds, labels_test)
        our_mdae = median_absolute_error(labels_our_preds, labels_test)
        our_rmse = sqrt(mean_squared_error(labels_our_preds, labels_test))
        our_r2 = r2_score(labels_our_preds, labels_test)
        print("Out preds")
        print("MAE: ", our_mae)
        print("MdAE: ", our_mdae)
        print("RMSE: ", our_rmse)
        print("r2: ", our_r2)
        #inds = labels_test.argsort()
        #plt.scatter(labels_our_preds[inds], labels_test[inds])
        #plt.show()

        labels_their_preds = features_test[:,-2]
        their_mae = mean_absolute_error(labels_their_preds, labels_test)
        their_mdae = median_absolute_error(labels_their_preds, labels_test)
        their_rmse = sqrt(mean_squared_error(labels_their_preds, labels_test))
        their_r2 = r2_score(labels_their_preds, labels_test)
        print("\nTheir preds")
        print("MAE: ", their_mae)
        print("MdAE: ", their_mdae)
        print("RMSE: ", their_rmse)
        print("r2: ", their_r2)
        #plt.scatter(labels_their_preds, labels_test)
        #plt.show()

        if their_mae != 0:
            print("\nMAE Improvement: ", 100 * (their_mae - our_mae) / their_mae)
        if their_mdae != 0:
            print("\nMdAE Improvement: ", 100 * (their_mdae - our_mdae) / their_mdae)
        if their_rmse != 0:
            print("\nRMSE Improvement: ", 100 * (their_rmse - our_rmse) / their_rmse)
"""
dbi = DBI()
i = 0
for r in dbi.get_ride_ids():
    print("\n" + r)
    i+=1
    if i <= 15:
        continue
    model = WaitPredictor(r, dbi, load_fls=True)
    model.fit()
"""
