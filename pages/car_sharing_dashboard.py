import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    trips = pd.read_csv("datasets/trips.csv")
    cars = pd.read_csv("datasets/cars.csv")
    cities = pd.read_csv("datasets/cities.csv")
    # jointures
    trips_merged = trips.merge(cars, how="left", left_on="car_id", right_on="id_car")
    trips_merged = trips_merged.merge(cities, how="left", left_on="city_id", right_on="city_id")

    # nettoyage colonnes inutiles
    cols_to_drop = ["id_car", "city_id", "id_customer", "id"]
    cols_existing = [c for c in cols_to_drop if c in trips_merged.columns]
    trips_merged = trips_merged.drop(columns=cols_existing)

    # horodatage
    if "pickup_time" in trips_merged.columns:
        trips_merged["pickup_time"] = pd.to_datetime(trips_merged["pickup_time"], errors="coerce")
        trips_merged["pickup_date"] = trips_merged["pickup_time"].dt.date

    return trips_merged


def main():
    st.set_page_config(page_title="Car Sharing Dashboard", layout="wide")
    st.title("Car Sharing Metrics Dashboard")

    trips_merged = load_data()

    # filtre par marque
    if "brand" in trips_merged.columns:
        brands = sorted(trips_merged["brand"].dropna().unique())
    elif "model" in trips_merged.columns:
        brands = sorted(trips_merged["model"].dropna().unique())
    else:
        brands = []

    selected_brands = st.sidebar.multiselect("Filter by car brand", brands, default=brands)

    if selected_brands:
        trips_merged = trips_merged[trips_merged["brand"].isin(selected_brands)] if "brand" in trips_merged.columns else trips_merged[trips_merged["model"].isin(selected_brands)]

    # métriques
    total_rides = len(trips_merged)

    revenue_col = "revenue" if "revenue" in trips_merged.columns else "price" if "price" in trips_merged.columns else None
    best_model = "n/a"
    total_revenue = 0

    if revenue_col:
        total_revenue = trips_merged[revenue_col].sum()
        if "model" in trips_merged.columns:
            best_model = trips_merged.groupby("model")[revenue_col].sum().idxmax()
        elif "brand" in trips_merged.columns:
            best_model = trips_merged.groupby("brand")[revenue_col].sum().idxmax()

    distance_col = "distance" if "distance" in trips_merged.columns else None
    total_distance = trips_merged[distance_col].sum() if distance_col else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Trips", total_rides)
    c2.metric("Top Revenue Model", best_model)
    c3.metric("Total Distance", f"{total_distance:.2f}" if distance_col else "n/a")

    st.subheader("Sample Trips")
    st.write(trips_merged.head(10))

    # visualisations
    st.subheader("Visualizations")

    if "pickup_date" in trips_merged.columns and revenue_col:
        revenue_over_time = trips_merged.groupby("pickup_date")[revenue_col].sum().reset_index()
        revenue_over_time = revenue_over_time.sort_values("pickup_date")
        st.line_chart(revenue_over_time.rename(columns={"pickup_date": "index"}).set_index("index")[revenue_col])

    if "model" in trips_merged.columns and revenue_col:
        revenue_by_model = trips_merged.groupby("model")[revenue_col].sum().sort_values(ascending=False)
        st.bar_chart(revenue_by_model)

    if "pickup_date" in trips_merged.columns and revenue_col:
        cumulative = revenue_over_time.copy()
        cumulative["cumulative_revenue"] = cumulative[revenue_col].cumsum()
        st.area_chart(cumulative.rename(columns={"pickup_date": "index"]).set_index("index")["cumulative_revenue"])

    if "model" in trips_merged.columns and distance_col:
        rides_by_model = trips_merged.groupby("model")["trip_id" if "trip_id" in trips_merged.columns else "model"].count().rename("count")
        st.bar_chart(rides_by_model)

    if "city" in trips_merged.columns and "duration" in trips_merged.columns:
        avg_duration_by_city = trips_merged.groupby("city")["duration"].mean()
        st.bar_chart(avg_duration_by_city)

    if "city" in trips_merged.columns and revenue_col:
        revenue_by_city = trips_merged.groupby("city")[revenue_col].sum()
        st.bar_chart(revenue_by_city)


if __name__ == "__main__":
    main()
