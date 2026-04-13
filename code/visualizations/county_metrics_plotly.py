import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Load overdose counts
addiction_df = pd.read_csv("../../data/clean_data/cleaned_addiction.csv")
addiction_df["FIPS"] = addiction_df["FIPS"].astype(str).str.zfill(5)

# Aggregate overdose deaths per county
overdose_totals = (
    addiction_df.groupby("FIPS")["Count_drug_overdose_deaths"]
    .sum()
    .reset_index()
    .rename(
        columns={"FIPS": "fips", "Count_drug_overdose_deaths": "total_overdose_deaths"}
    )
)

# Load base dataset
df = pd.read_csv("../../data/clean_data/joined_data.csv")
df["fips"] = df["fips"].astype(str).str.zfill(5)
df = df.drop_duplicates(subset="fips", keep="first")

# Merge overdose totals
df = df.merge(overdose_totals, on="fips", how="left")
df = df[df["total_overdose_deaths"].notna()]

# Transformations
df["log_overdose"] = np.log1p(df["total_overdose_deaths"])
df["log_population"] = np.log1p(df["census_2020_pop"])

# Rename fields for hover tooltip
hover_rename = {
    "county_name": "County",
    "total_overdose_deaths": "Total Overdose Deaths",
    "total_pov": "Poverty Rate (%)",
    "unemployment_rate_2021": "Unemployment Rate",
    "census_2020_pop": "Population",
}

# Initial metric
initial_metric = "log_overdose"

# Create initial map
fig = px.choropleth(
    df,
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="fips",
    color=initial_metric,
    color_continuous_scale=[
        [0.00, "#610061"],
        [0.15, "#8b0e4d"],
        [0.40, "#a31931"],
        [0.70, "#cf3e2a"],
        [1.00, "#ff6e42"],
    ],
    scope="usa",
    labels=hover_rename,
    hover_data={
        "county_name": True,
        "total_overdose_deaths": True,
        "total_pov": True,
        "unemployment_rate_2021": True,
        "census_2020_pop": True,
        "log_population": False,
        "log_overdose": False,
        "fips": False,
    },
    featureidkey="id",
)

# Manually set colorbar for the initial metric
fig.update_coloraxes(
    colorbar=dict(
        title="Total<br>Overdose<br>Deaths<br>(Log)",
        thickness=15,
        len=0.75,
        y=0.5,
        yanchor="middle",
    ),
    reversescale=True,
)

# Dropdown config
metric_configs = {
    "log_overdose": {
        "label": "Total<br>Overdose<br>Deaths<br>(Log)",
        "colorscale": [
            [0.00, "#610061"],
            [0.15, "#8b0e4d"],
            [0.40, "#a31931"],
            [0.70, "#cf3e2a"],
            [1.00, "#ff6e42"],
        ],
        "reverse": True,
    },
    "total_pov": {
        "label": "Poverty<br>Rate (%)",
        "colorscale": "Plasma",
        "reverse": True,
    },
    "unemployment_rate_2021": {
        "label": "Unemployment<br>Rate (%)",  # stacked here too if you want
        "colorscale": "Viridis",
        "reverse": True,
    },
    "log_population": {
        "label": "Population<br>(Log)",
        "colorscale": "Blues",
        "reverse": True,
    },
}

# Dropdown buttons
dropdown_buttons = []
for metric, config in metric_configs.items():
    zmin = df[metric].min()
    zmax = df[metric].max()
    dropdown_buttons.append(
        dict(
            method="update",
            label=config["label"].replace("<br>", " "),
            args=[
                {"z": [df[metric]]},
                {
                    "coloraxis": {
                        "colorscale": config["colorscale"],
                        "cmin": zmin,
                        "cmax": zmax,
                        "reversescale": config["reverse"],
                        "colorbar": {
                            "title": {"text": config["label"]},
                            "thickness": 15,
                            "len": 0.75,
                            "y": 0.5,
                            "yanchor": "middle",
                        },
                    }
                },
            ],
        )
    )

# Final layout
fig.update_layout(
    title=dict(
        text="<b>Overdose, Poverty, and Unemployment</b>", x=0.5, xanchor="center"
    ),
    geo=dict(scope="usa", showlakes=False),
    updatemenus=[
        dict(
            buttons=dropdown_buttons,
            direction="down",
            showactive=True,
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
        )
    ],
    margin=dict(r=0, t=40, l=0, b=20),
    height=530,
)

fig.write_html("../../outputs/plotly_county_metrics_map.html", include_plotlyjs="cdn")
fig.show()
