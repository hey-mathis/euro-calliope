import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

WGS_84 = "EPSG:4326"

def determine_hydro_capacities(path_to_plants, path_to_locations, path_to_supply_output, path_to_storage_output):
    locations = gpd.read_file(path_to_locations).to_crs(WGS_84).set_index("id")
    plants = pd.read_csv(path_to_plants, index_col="id")

    supply_capacities = pd.concat(
        [capacities_per_location(
            plants[plants.type == tech_name.upper()].copy(),
            locations,
            tech_name=tech_name
        ) for tech_name in ["hror", "hdam"]],
        axis=1
    )
    supply_capacities.to_csv(path_to_supply_output)
    storage_capacities = capacities_per_location(
        plants[plants.type == "HPHS"].copy(),
        locations,
        tech_name="hphs"
    )
    storage_capacities.to_csv(path_to_storage_output, header=True, index=True)


def capacities_per_location(plants, locations, tech_name):
    plant_centroids = gpd.GeoDataFrame(
        crs=WGS_84,
        geometry=list(map(Point, zip(plants.lon, plants.lat))),
        index=plants.index
    )
    location_of_plant = gpd.sjoin(plant_centroids, locations, how="left", op='intersects')["index_right"]
    location_of_plant = location_of_plant[~location_of_plant.index.duplicated()]
    return (plants.groupby(location_of_plant)
                  .agg({"installed_capacity_MW": sum, "storage_capacity_MWh": sum})
                  .reindex(index=locations.index, fill_value=0)
                  .rename(columns={"installed_capacity_MW": f"installed_capacity_{tech_name}_MW"})
                  .rename(columns={"storage_capacity_MWh": f"storage_capacity_{tech_name}_MWh"}))


if __name__ == "__main__":
    determine_hydro_capacities(
        path_to_plants=snakemake.input.plants,
        path_to_locations=snakemake.input.locations,
        path_to_supply_output=snakemake.output.supply,
        path_to_storage_output=snakemake.output.storage,
    )
