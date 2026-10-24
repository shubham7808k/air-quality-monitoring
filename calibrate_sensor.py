
import pandas as pd
import joblib

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Use real paired measurements from calibration.csv
df = pd.read_csv("calibration.csv")

required = ["dust_voltage_v", "reference_pm25_ugm3"]
df = df[required].dropna()

if len(df) < 30:
    raise ValueError(
        "Collect more paired measurements before fitting a model."
    )

X = df[["dust_voltage_v"]]
y = df["reference_pm25_ugm3"]

# For time-series data, a chronological split is often better
# than a random split. This basic example uses a random split.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

print("Slope:", model.coef_[0])
print("Intercept:", model.intercept_)
print("Validation MAE (ug/m3):", round(mae, 2))
print("Validation RMSE (ug/m3):", round(rmse, 2))
print("Validation R²:", round(r2, 3))

joblib.dump(model, "gp2y1010_pm25_model.joblib")
print("Saved model: gp2y1010_pm25_model.joblib")
