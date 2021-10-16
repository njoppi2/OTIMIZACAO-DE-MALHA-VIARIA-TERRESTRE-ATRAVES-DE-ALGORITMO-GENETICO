import osmnx as ox
import networkx as nx

import matplotlib.pyplot as plt

utn = ox.settings.useful_tags_node
oxna = ox.settings.osm_xml_node_attrs
oxnt = ox.settings.osm_xml_node_tags
utw = ox.settings.useful_tags_way
oxwa = ox.settings.osm_xml_way_attrs
oxwt = ox.settings.osm_xml_way_tags
utn = list(set(utn + oxna + oxnt))
utw = list(set(utw + oxwa + oxwt))
ox.config(all_oneway=True, useful_tags_node=utn, useful_tags_way=utw)







place_name = "Forquilhinha, Brazil"
outputName=place_name #.replace(" ", "_")

graph = ox.graph_from_place(place_name, simplify=False,  network_type='drive')

type(graph)
nx.classes.multidigraph.MultiDiGraph


nx.write_pajek(graph, outputName+".net")
#nx.write_graphml(graph, "output.graphml")
#ox.save_graph_xml(graph, filepath='output.osm')
fig, ax = ox.plot_graph(graph)


plt.tight_layout()
