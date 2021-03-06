"""
Pull tract information from database,
compute new congressional districts based on criteria in request,
and update the database.
"""

import json
import networkx as nx
from gerry_flask.models import Tract, Edge, DistrictView


def fill_graph(dbsession):
    """Build state graph from tract and edge databases."""
    graph = nx.Graph()
    tracts = dbsession.query(Tract).all()
    edges = dbsession.query(Edge).all()
    for tract in tracts:
        graph.add_node(tract)
    for edge in edges:
        source = dbsession.query(Tract).get(edge.tract_source)
        target = dbsession.query(Tract).get(edge.tract_target)
        graph.add_edge(source, target)
    return graph


class OccupiedDist(object):
    """A stucture to contain and separate tracts in a State object.

    add_node(self, node): adds node to nodes and updates district
    properties accordingly
    rem_node(self, node): removes node from nodes and updates district
    properties accordingly
    """

    def __init__(self, districtID, state, tracts=None):
        """Initialize the OccupiedDist Object."""
        self.nodes = nx.Graph()
        self.perimeter = []
        self.population = 0
        self.area = 0
        self.state = state
        self.districtID = districtID
        if tracts:
            try:
                for tract in tracts:
                    self.add_node(tract, self.state.state_graph)
            except TypeError:
                raise TypeError('Tracts must be iterable.')

    def add_node(self, node, state_graph):
        """Add node to nodes and updates district properties."""
        node.districtid = self.districtID
        self.nodes.add_node(node)
        tract = self.state.dbsession.query(Tract).get(node.gid)
        tract.districtid = self.districtID
        self.state.dbsession.flush()
        neighbors = state_graph.neighbors(node)
        if node in self.perimeter:
            self.perimeter.remove(node)
        for neighbor in neighbors:  # After node is added, make the edge connections within the occupied district.
            if neighbor in self.nodes.nodes():
                self.nodes.add_edge(neighbor, node)
            if neighbor not in self.nodes.nodes() and neighbor not in self.perimeter:
                self.perimeter.append(neighbor)
        self.population += node.tract_pop
        self.area += node.shape_area

    def rem_node(self, node, state_graph):
        """Remove node from nodes and updates district properties."""
        self.population -= node.tract_pop
        self.nodes.remove_node(node)
        self.area -= node.shape_area
        neighbors = state_graph.neighbors(node)
        to_perimeter = False
        for neighbor in neighbors:  # Decide whether to remove nodes from the district perimeter.
            takeout = True
            if neighbor in self.perimeter:  # if its a perimeter node,
                neighborneighbors = state_graph.neighbors(neighbor)
                for neighborneighbor in neighborneighbors:  # check its neighbors
                    if neighborneighbor in self.nodes.nodes():  # if it has a neighbor in the district
                        takeout = False  # it should remain in the perimeter list.
                if takeout:  # If it should be removed,
                    self.perimeter.remove(neighbor)  # Remove it!
            elif neighbor in self.nodes.nodes():  # If the removed node neighbors the district (which it should)
                to_perimeter = True  # mark it to be added to the perimeter
        if to_perimeter:  # If its marked,
            self.perimeter.append(node)  # add it to the perimeter


class UnoccupiedDist(OccupiedDist):
    """A structure to contain tracts that haven't been claimed by a district.

    add_node(self, node): adds node to nodes and updates district
    properties accordingly
    rem_node(self, node): removes node from nodes and updates district
    properties accordingly
    """

    def __init__(self, districtID, state_graph, tracts=None):
        """Initialize the UnoccupiedDist Object."""
        self.nodes = nx.Graph()
        self.perimeter = []
        self.population = 0
        self.area = 0
        self.districtID = districtID
        if tracts:
            try:
                for tract in tracts:
                    self.add_node(tract, state_graph)
            except TypeError:
                raise TypeError('Tracts must be iterable.')

    def add_node(self, node, state_graph):
        """Add node to nodes and updates district properties accordingly."""
        node.districtid = None
        self.nodes.add_node(node)
        for neighbor in state_graph.neighbors(node):
            if neighbor in self.nodes:
                self.nodes.add_edge(neighbor, node)
        self.population += node.tract_pop
        self.area += node.shape_area
        neighbors = state_graph.neighbors(node)
        to_add = False
        for neighbor in neighbors:  # Handling which nodes to add or remove from the perimeter.
            takeout = True
            if neighbor in self.perimeter:
                neighborneighbors = state_graph.neighbors(neighbor)
                for neighborneighbor in neighborneighbors:
                    if neighborneighbor not in self.nodes:
                        takeout = False
                if takeout:
                    self.perimeter.remove(neighbor)
            if neighbor not in self.nodes:
                to_add = True
        if to_add:
            self.perimeter.append(node)

    def rem_node(self, node, state_graph):
        """Remove node from nodes and updates district properties accordingly."""
        self.population -= node.tract_pop
        self.area -= node.shape_area
        if node in self.perimeter:
            self.perimeter.remove(node)
        neighbors = self.nodes.neighbors(node)
        for neighbor in neighbors:
            if neighbor not in self.perimeter:
                self.perimeter.append(neighbor)
        self.nodes.remove_node(node)


class State(object):
    """Manages how tracts are distributed into districts in a particular state.
    build_district(self, start, population):
    creates a new district stemming from the start node with a given population
    fill_state(self, request): continues to build districts until all unoccupied tracts are claimed
    """

    def __init__(self, dbsession, num_dst):
        """Initialize the State Object."""
        self.unoccupied = []
        self.districts = []
        self.population = 0
        self.area = 0
        self.num_dst = num_dst  # The Number of districts alotted for that state (7 for Colorado)
        self.dbsession = dbsession
        self.state_graph = fill_graph(self.dbsession)
        landmass = nx.connected_components(self.state_graph)  # Returns all of the connected/contiguous areas of land for a state.
        for island in landmass:
            unoc = UnoccupiedDist(None, self.state_graph, tracts=island)  # needs the state graph for its edges
            for tract in unoc.nodes.nodes():
                if tract.isborder == 1:  # This is a hardcoded field for Colorado.  A challenge of adding more states is finding these automatically.
                    unoc.perimeter.append(tract)  # begin with all border tracts in the perimeter.
            self.population += unoc.population
            self.unoccupied.append(unoc)
            self.area += unoc.area

    def fill_state(self, criteria):
        """Build districts until all unoccupied tracts are claimed."""
        for num in range(self.num_dst):
            rem_pop = sum(unoc.population for unoc in self.unoccupied)
            rem_dist = self.num_dst - len(self.districts)
            tgt_population = rem_pop / rem_dist  # Average available population is the target population.  It helps ensure the State gets totally filled.
            yield from self.build_district(tgt_population, num + 1, criteria)
        # assign_district(self.dbsession, self.state_graph)

    def build_district(self, tgt_population, dist_num, criteria):
        """Create a new district stemming from the start node with a given population."""
        dst = OccupiedDist(dist_num, self)
        self.districts.append(dst)
        start = self.find_start()
        yield self.swap(dst, start)  # if state is full, this wont work
        while True:
            new_tract = self.select_next(dst, criteria)
            if new_tract is None:  # If there are no more nodes in unoccupied, this will be None
                for unoc in self.unoccupied:  # This ends the building process
                    if not len(unoc.nodes.nodes()):
                        self.unoccupied.remove(unoc)
                break
            high_pop = (new_tract.tract_pop + dst.population)  # Population including the next tract.
            # If the population including the next district is further from the goal
            if abs(high_pop - tgt_population) > abs(dst.population - tgt_population):
                break  # We stop building that district
            else:
                # Swap removes the tract from its unoccupied district and adds it to the occupied district.
                yield self.swap(dst, new_tract)
                neighbors = self.state_graph.neighbors(new_tract)
                # Grab the new nodes unassigned neighbors
                unassigned_neighbors = [neighbor for neighbor in neighbors if neighbor in self.unoccupied[0].nodes]
                # If there is more than one, than a split is possible.
                if len(unassigned_neighbors) > 1:
                    for i in range(len(unassigned_neighbors)):
                        # We check each node and its previous neighbor to ensure they're connected.
                        if not nx.has_path(
                            self.unoccupied[0].nodes,
                            unassigned_neighbors[i],
                            unassigned_neighbors[i - 1]
                        ):  # If there is a split in the unoccupied district
                            # Identify each of the distinct unoccupied districts.
                            unoc_neighbors = [x for x in nx.connected_components(self.unoccupied[0].nodes)]
                            biggest = max(unoc_neighbors, key=lambda x: len(x))
                            # Ignore the largest (This should be highest pop, fixed in different version)
                            unoc_neighbors.remove(biggest)
                            # All unoccupied districts will be bordering, because as soon as there is a split, we do this.
                            for neigh in unoc_neighbors:  # Consume all of the rest (usually one small one)
                                for tract in neigh:  # This sometimes gives us a district that is too large, and is the major focus of improving the algorithm.
                                    yield self.swap(dst, tract)
                            break

    def swap(self, dst, new_tract):
        """Exchange tract from unoccupied district to district."""
        self.unoccupied[0].rem_node(new_tract, self.state_graph)
        dst.add_node(new_tract, self.state_graph)
        return make_feature(self.dbsession, new_tract)

    def select_next(self, dst, criteria):
        """Choose the next best tract to add to growing district."""
        best_rating = 0
        best = None  # We're building a score for each node based on our criteria, and saving the best.
        for perimeter_tract in dst.perimeter:  # dst.perimeter is every node bordering that district.
            if perimeter_tract.districtid is None:  # Grab those without a district assigned
                count = 0    # Check how many tracts that tract borders that are ALREADY in the district.  More borders gets more points
                for neighbor in self.state_graph.neighbors(perimeter_tract):
                    if neighbor.districtid == dst.districtID:
                        count += 1
                counties = set()    # If the tracts county is in the district already, it gets a point.
                for node in dst.nodes:
                    counties.add(node.county)
                same_county = 0
                if perimeter_tract.county in counties:
                    same_county = 1
                rating = count * int(criteria['compactness']) + same_county * int(criteria['county'])  # Calculate score based on criteria.
                if rating > best_rating:
                    best_rating = rating
                    best = perimeter_tract
        return best

    def find_start(self):
        """
        Choose best starting tract for a new district.
        Based on number of bordering districts.
        """
        best_set = set()
        best = None
        for tract in self.unoccupied[0].perimeter:
            unique_dists = set()
            for neighbor in self.state_graph.neighbors(tract):
                for dst in self.districts:
                    if neighbor in dst.nodes.nodes():
                        unique_dists.add(dst)
            if len(unique_dists) > len(best_set) or len(unique_dists) == 0:
                best_set = unique_dists
                best = tract
        return best


def assign_district(dbsession, graph):
    """Assign district IDs to all of the tracts in the tract table."""
    for node in graph.nodes():
        tract = dbsession.query(Tract).get(node.gid)
        tract.districtid = node.districtid
        dbsession.flush()


def tract_JSON(dbsession, tract):
    """Build JSON from the polygons in the database."""
    geojson = dbsession.query(tract.geom.ST_AsGeoJSON()).first()[0]
    colors = ['blue', 'red', 'yellow', 'purple', 'orange', 'green', 'black']
    json_string = '''{"type": "FeatureCollection","features": [\
{"type": "Feature", "properties": {"color": "%s"},\
"geometry": %s}]}'''
    return json_string % (colors[tract.districtid % len(colors)], geojson)


def make_feature(dbsession, tract):
    """."""
    colors = ['blue', 'red', 'yellow', 'purple', 'orange', 'green', 'black']
    geojson = dbsession.query(tract.geom.ST_AsGeoJSON()).first()[0]
    return {
        "type": "Feature",
        "properties": {"color": colors[tract.districtid % len(colors)]},
        "geometry": json.loads(geojson),
    }


def make_feature_collection(features):
    """."""
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    return json.dumps(feature_collection)


def full_JSON(dbsession):
    """Build JSON from the polygons in the database."""
    feature_collection = {
        "type": "FeatureCollection",
        "features": []
    }
    feature = {
        "type": "Feature",
        "properties": None,
        "geometry": None
    }

    districts = dbsession.query(DistrictView, DistrictView.geom.ST_AsGeoJSON()).all()
    colors = ['blue', 'red', 'yellow', 'purple', 'orange', 'green', 'black']

    for dst, geojson in districts:
        cur_feature = feature.copy()
        color = colors[int(dst.districtid) % len(colors)]
        cur_feature['properties'] = dict(zip(
            ['id', 'area', 'population', 'color'],
            map(str, [dst.districtid, dst.area, dst.population, color])
        ))
        cur_feature['geometry'] = json.loads(geojson)
        feature_collection['features'].append(cur_feature)
    return json.dumps(feature_collection)
