import pandas as pd
import osmnx as ox
import networkx as nx
import folium
import webbrowser
from heapq import heappop, heappush

# we are using osmnx to fetch the road network of jaipur
city_graph = ox.graph_from_place("Jaipur, India", network_type="drive")

# importing the dataset
df = pd.read_csv(r"C:\Users\vansh\Desktop\ml\Hospital_Accident_Data.csv")

# converting latitudes and longitudes to tuple form 
df["Accident_Location"] = df["Latitude_Longitude(Accident's site)"].apply(
    lambda x: tuple(map(float, str(x).split(','))) if isinstance(x, str) else None
)
df["Hospital_Location"] = df["Latitude_Longitude(Hospital)"].apply(
    lambda x: tuple(map(float, str(x).split(','))) if isinstance(x, str) else None
)

# applying dijkstra algorithm, to find the shortest route to the nearest hospital
def dijkstra(graph, source, target):
    pq = []
    heappush(pq, (0, source))
    distances = {node: float('inf') for node in graph.nodes}
    previous_nodes = {node: None for node in graph.nodes}
    distances[source] = 0
    
    while pq:
        current_distance, current_node = heappop(pq)
        if current_node == target:
            break
        
        for neighbor, edge_data in graph[current_node].items():
            distance = edge_data[0]['length']
            new_distance = current_distance + distance
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heappush(pq, (new_distance, neighbor))

    path = []
    node = target
    while node is not None:
        path.append(node)
        node = previous_nodes[node]
    
    return path[::-1]

# making an overview of all the hospitals and accident prone sites, on the jaipur city road network.
overview_map = folium.Map(location=[26.9124, 75.7873], zoom_start=12)

for idx, row in df.iterrows():
    accident_coords = row["Accident_Location"]
    if accident_coords:
        folium.Marker(
            location=accident_coords,
            icon=folium.Icon(color="red"),
            popup=f"Accident Site: {row['Accident_Prone_Site']}"
        ).add_to(overview_map)

for index, row in df.iterrows():
    hospital_coords = row["Hospital_Location"]
    if hospital_coords:
        folium.Marker(
            location=hospital_coords,
            icon=folium.Icon(color="green"),
            popup=f"Hospital: {row['Hospitals_Name']}"
        ).add_to(overview_map)

output_file = "overview_map.html"
overview_map.save(output_file)
webbrowser.open(output_file)

# asking user what is his accident location
accident_site_name = input("Enter accident site name: ")
accident_row = df[df["Accident_Prone_Site"] == accident_site_name]
if accident_row.empty:
    print("Accident site not found!")
    exit()

accident_coords = accident_row["Accident_Location"].values[0]

# finding all the hospitals near the accident site, using dijkstra through networkx library, and saving them in a list.
hospital_distances = []
accident_node = ox.distance.nearest_nodes(city_graph, accident_coords[1], accident_coords[0])

for idx, row in df.iterrows():
    hospital_coords = row["Hospital_Location"]
    hospital_node = ox.distance.nearest_nodes(city_graph, hospital_coords[1], hospital_coords[0])
    path_length = nx.shortest_path_length(city_graph, accident_node, hospital_node, weight="length")
    hospital_distances.append((path_length, row["Hospitals_Name"], hospital_node, hospital_coords))

# sorting the list of nearest hospitals, based on how far they are.
hospital_distances.sort()
nearest_hospital = hospital_distances[0]

# initializing the route to the nearest hospital
shortest_path_nodes = dijkstra(city_graph, accident_node, nearest_hospital[2])
print(f"Route to nearest hospital ({nearest_hospital[1]}) mapped!")
print("INQUIRING IF BEDS ARE AVAILABLE...")
availability = input("Are beds available? (yes/no): ")

# SCENARIO: user contacts the hospital, asking if they have a bed empty or not. if yes, then we got he nearest hospital. if no, then we choose the 2nd or 3rd nearest hospital.
if availability.lower() == "yes":
    selected_hospital = nearest_hospital
else:
    print("Beds not available! Finding alternative hospitals...")
    print(f"2nd Nearest Hospital: {hospital_distances[1][1]}")
    print(f"3rd Nearest Hospital: {hospital_distances[2][1]}")
    choice = input("Select hospital (2 for 2nd nearest, 3 for 3rd nearest): ")
    selected_hospital = hospital_distances[1] if choice == "2" else hospital_distances[2]

# displaying the final route based on th euser's selection of the hospital
final_path_nodes = dijkstra(city_graph, accident_node, selected_hospital[2])
m = folium.Map(location=accident_coords, zoom_start=13)
folium.Marker(accident_coords, icon=folium.Icon(color="blue"), popup="Accident Site").add_to(m)
folium.Marker(selected_hospital[3], icon=folium.Icon(color="green"), popup=f"Hospital: {selected_hospital[1]}").add_to(m)
path_coords = [(city_graph.nodes[node]['y'], city_graph.nodes[node]['x']) for node in final_path_nodes]
folium.PolyLine(path_coords, color="red", weight=5, opacity=0.8, tooltip="Final Route").add_to(m)
m.save("ambulance_route.html")
webbrowser.open("ambulance_route.html")
print("Final route mapped! Open 'ambulance_route.html' to view.")

