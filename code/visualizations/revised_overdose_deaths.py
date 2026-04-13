import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import requests

# Load GeoJSON from Plotly GitHub
url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
response = requests.get(url)
counties = response.json()

# Add 'id' field to each feature (same as STATE + COUNTY)
for feature in counties["features"]:
    state = feature["properties"]["STATE"]
    county = feature["properties"]["COUNTY"]
    feature["id"] = f"{state}{county}"

# Extract all FIPS
all_geo_fips = [feature["id"] for feature in counties["features"]]
all_fips_df = pd.DataFrame({"fips": all_geo_fips})

# Load your main dataset (adjust path as needed)
full_data = pd.read_csv("../../data/clean_data/joined_data.csv")

# Format fips and compute per capita + log-transformed death rates
full_data2_raw = full_data.copy()
full_data2_raw["fips"] = full_data2_raw["fips"].astype(int).astype(str).str.zfill(5)
full_data2_raw["Deaths_per_capita"] = (
    full_data2_raw["mean_addiction_deaths"] / full_data2_raw["census_2020_pop"]
)
full_data2_raw["Log_deaths_per_capita"] = np.log(
    np.maximum(full_data2_raw["Deaths_per_capita"], 1e-6)
)
full_data2_raw["log_county_hover_text"] = (
    "County: "
    + full_data2_raw["county_name"]
    + "<br>"
    + "County FIP: "
    + full_data2_raw["fips"]
    + "<br>"
    + "Average Deaths per Capita: "
    + full_data2_raw["Deaths_per_capita"].round(4).astype(str)
)

# Merge to ensure every FIPS is represented
full_data2 = pd.merge(all_fips_df, full_data2_raw, on="fips", how="left")
full_data2["Log_deaths_per_capita"] = full_data2["Log_deaths_per_capita"].fillna(
    np.log(1e-6)
)
full_data2["log_county_hover_text"] = full_data2["log_county_hover_text"].fillna(
    "County FIP: " + full_data2["fips"] + "<br>No data available"
)

# Create choropleth
fig = go.Figure(
    go.Choropleth(
        geojson=counties,
        locations=full_data2["fips"],
        z=full_data2["Log_deaths_per_capita"],
        text=full_data2["log_county_hover_text"],
        hoverinfo="text",
        featureidkey="id",
        colorscale=[
            [0.0, "#eef0f8"],
            [0.25, "#9ba8cc"],
            [0.5, "#6b7db3"],
            [0.75, "#3d4f8a"],
            [1.0, "#1a2557"],
        ],
        colorbar=dict(
            title=dict(text="Logged<br>Overdose<br>Deaths", font=dict(size=12)),
            thickness=15,
            len=0.75,
        ),
        marker_line_width=0,
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="<b>Log Transformed Drug Overdose Deaths<br>Per Capita in the US from 2020 to 2024</b>",
        x=0.5,
        y=0.97,
        font=dict(size=18),
    ),
    margin=dict(l=0, r=0, t=60, b=0),
    height=550,
    geo=dict(
        scope="usa",
        projection=dict(type="albers usa"),
        showlakes=True,
        lakecolor="white",
    ),
)

# Show (optional)
# fig.show()

# Save interactive map to HTML
fig.write_html("../../outputs/us_overdose_map_county.html", include_plotlyjs="cdn")


### FIGURE #2: State Level Map ###

# Load your main dataset
full_data = pd.read_csv("../../data/clean_data/joined_data.csv")

# Map full state names to abbreviations
state_abbrev_map = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}
full_data["ST_ABBREV"] = full_data["state_name"].map(state_abbrev_map)

# Aggregate to state level
state_data = (
    full_data.groupby(["state_name", "ST_ABBREV"])
    .agg(
        Log_state_deaths_per_capita=(
            "mean_addiction_deaths",
            lambda x: np.log(np.maximum(x.mean(), 1e-6)),
        )
    )
    .reset_index()
)

# Hover text
state_data["log_state_hover_text"] = (
    "State: "
    + state_data["state_name"]
    + "<br>Log Avg Overdose Deaths Per Capita: "
    + state_data["Log_state_deaths_per_capita"].round(4).astype(str)
)

# Build the figure
fig2 = go.Figure(
    go.Choropleth(
        locations=state_data["ST_ABBREV"],
        z=state_data["Log_state_deaths_per_capita"],
        text=state_data["log_state_hover_text"],
        hoverinfo="text",
        locationmode="USA-states",
        colorscale=[
            [0.00, "#610061"],
            [0.15, "#8b0e4d"],
            [0.40, "#a31931"],
            [0.70, "#cf3e2a"],
            [1.00, "#ff6e42"],
        ],
        reversescale=True,
        colorbar=dict(
            title=dict(text="Log Drug<br>Overdose<br>Deaths", font=dict(size=12)),
            thickness=15,
            len=0.75,
        ),
        marker_line_width=0,
    )
)

fig2.update_layout(
    title=dict(
        text="<b>Log Transformed Drug Overdose Deaths<br>Per Capita in the US from 2020 to 2024<br>State Level</b>",
        x=0.5,
        y=0.97,
        font=dict(size=18),
    ),
    margin=dict(l=0, r=0, t=70, b=0),
    height=550,
    geo=dict(
        scope="usa",
        projection=dict(type="albers usa"),
        showlakes=True,
        lakecolor="white",
    ),
)

# Save to HTML
fig2.write_html("../../outputs/us_overdose_map_state.html", include_plotlyjs="cdn")

fig2
