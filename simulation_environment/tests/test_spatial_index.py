import numpy as np
from simulation_environment.simulation.agent import PedestrianAgent
from simulation_environment.simulation.spatial_index import QuadTree


def agent(identifier, x, y):
    return PedestrianAgent(identifier, np.array([x, y], dtype=float), "exit")


def test_quadtree_returns_only_nearby_agents():
    items = [agent(1, 1, 1), agent(2, 1.2, 1.1), agent(3, 9, 9)]
    tree = QuadTree(items, bounds=(0, 0, 10, 10))
    found = {a.id for a in tree.query_radius(1, 1, 0.5)}
    assert found == {1, 2}


def test_quadtree_handles_empty_and_boundary_points():
    assert QuadTree().query_radius(0, 0, 1) == []
    items = [agent(1, 0, 0), agent(2, 10, 10)]
    tree = QuadTree(items, bounds=(0, 0, 10, 10))
    assert {a.id for a in tree.query_radius(10, 10, 0)} == {2}
