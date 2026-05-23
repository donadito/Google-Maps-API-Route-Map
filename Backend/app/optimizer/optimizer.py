from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class GAConfig:
  population_size: int
  generations: int
  mutation_rate: float
  elite_rate: float
  tournament_size: int
  seed: int | None = None


def route_cost(
  order: list[int],
  distance_matrix: list[list[float]],
  return_to_origin: bool,
) -> float:
  cost = 0.0
  current = 0
  for node in order:
    cost += distance_matrix[current][node]
    current = node
  if return_to_origin:
    cost += distance_matrix[current][0]
  return cost


def greedy_seed(nodes: list[int], distance_matrix: list[list[float]]) -> list[int]:
  remaining = nodes[:]
  route: list[int] = []
  current = 0
  while remaining:
    next_node = min(remaining, key=lambda node: distance_matrix[current][node])
    route.append(next_node)
    remaining.remove(next_node)
    current = next_node
  return route


def random_individual(nodes: list[int], rng: random.Random) -> list[int]:
  order = nodes[:]
  rng.shuffle(order)
  return order


def tournament_select(
  population: list[list[int]],
  rng: random.Random,
  tournament_size: int,
  cost_fn: Callable[[list[int]], float],
) -> list[int]:
  contenders = rng.sample(population, tournament_size)
  return min(contenders, key=cost_fn)


def ordered_crossover(
  parent_a: list[int],
  parent_b: list[int],
  rng: random.Random,
) -> list[int]:
  size = len(parent_a)
  if size < 2:
    return parent_a[:]
  start, end = sorted(rng.sample(range(size), 2))
  child: list[int | None] = [None] * size
  child[start:end] = parent_a[start:end]
  fill = [node for node in parent_b if node not in child]
  fill_index = 0
  for idx in range(size):
    if child[idx] is None:
      child[idx] = fill[fill_index]
      fill_index += 1
  return [node for node in child if node is not None]


def mutate(order: list[int], rng: random.Random, mutation_rate: float) -> None:
  if len(order) < 2:
    return
  if rng.random() > mutation_rate:
    return
  i, j = rng.sample(range(len(order)), 2)
  order[i], order[j] = order[j], order[i]


def optimize_route(
  distance_matrix: list[list[float]],
  return_to_origin: bool,
  config: GAConfig,
) -> list[int]:
  total_nodes = len(distance_matrix)
  if total_nodes <= 1:
    return list(range(total_nodes))
  if total_nodes == 2:
    return [0, 1]

  rng = random.Random(config.seed)
  nodes = list(range(1, total_nodes))
  cost = lambda order: route_cost(order, distance_matrix, return_to_origin)

  population_size = max(6, config.population_size)
  population = [random_individual(nodes, rng) for _ in range(population_size - 1)]
  population.append(greedy_seed(nodes, distance_matrix))

  elite_count = max(1, int(population_size * config.elite_rate))

  for _ in range(config.generations):
    population.sort(key=cost)
    elites = population[:elite_count]

    new_population = elites[:]
    while len(new_population) < population_size:
      parent_a = tournament_select(population, rng, config.tournament_size, cost)
      parent_b = tournament_select(population, rng, config.tournament_size, cost)
      child = ordered_crossover(parent_a, parent_b, rng)
      mutate(child, rng, config.mutation_rate)
      new_population.append(child)

    population = new_population

  best = min(population, key=cost)
  return [0, *best]
