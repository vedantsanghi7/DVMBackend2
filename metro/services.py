import networkx as nx
from decimal import Decimal
from .models import Station, Connection, MetroLine


def build_graph():
    """
    Build an undirected graph of stations,
    edges labelled with line code, like your CLI program.
    """
    G = nx.Graph()

    for station in Station.objects.all():
        G.add_node(station.id)

    for edge in Connection.objects.select_related('line', 'from_station', 'to_station'):
        G.add_edge(
            edge.from_station.id,
            edge.to_station.id,
            line=edge.line.code
        )

    return G


def shortest_path_between_stations(source_station, dest_station):
    """
    Uses NetworkX shortest_path, like your previous main.py/metro_system.
    """
    G = build_graph()
    try:
        path_ids = nx.shortest_path(G, source_station.id, dest_station.id)
        return path_ids
    except nx.NetworkXNoPath:
        return None


def calculate_price_from_path(path_ids, rate_per_edge=Decimal('5.00')):
    """
    Price = (number of edges) * rate, same as (len(path) - 1) * 5.
    """
    if not path_ids or len(path_ids) < 2:
        return Decimal('0.00')
    num_edges = len(path_ids) - 1
    return rate_per_edge * num_edges
