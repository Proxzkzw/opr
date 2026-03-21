import math
import logging
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fleet")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ── Global exception handler — returns detail instead of empty 500 ──
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    tb = traceback.format_exc()
    log.error(f"Unhandled error on {request.url}:\n{tb}")
    return JSONResponse(status_code=500,
                        content={"detail": str(exc), "traceback": tb})


class StopModel(BaseModel):
    lat: float
    lon: float


class RouteRequest(BaseModel):
    stops: List[StopModel]
    warehouse: Optional[StopModel] = None


class SplitRequest(BaseModel):
    stops: List[StopModel]
    num_routes: int
    warehouse: Optional[StopModel] = None


# ── Haversine distance in metres ─────────────────────────
def haversine(a: StopModel, b: StopModel) -> int:
    R = 6371000
    la1, lo1 = math.radians(a.lat), math.radians(a.lon)
    la2, lo2 = math.radians(b.lat), math.radians(b.lon)
    dlat, dlon = la2 - la1, lo2 - lo1
    x = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return int(R * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x)))


# ── TSP solver ───────────────────────────────────────────
def _tsp_order(stops: List[StopModel],
               warehouse: Optional[StopModel] = None,
               time_limit_seconds: int = 5) -> List[int]:
    n = len(stops)
    if n == 0: return []
    if n == 1: return [0]
    if n == 2: return [0, 1]   # trivial — no solver needed

    nodes  = ([warehouse] + stops) if warehouse else stops
    N      = len(nodes)

    # Build distance matrix as a flat list for safe closure capture
    matrix = [[haversine(nodes[i], nodes[j]) for j in range(N)] for i in range(N)]

    if warehouse:
        # Add dummy end node with zero cost so route is open (no return)
        for row in matrix:
            row.append(0)
        matrix.append([0] * (N + 1))
        total_nodes = N + 1
        manager = pywrapcp.RoutingIndexManager(total_nodes, 1, 0, N)
    else:
        total_nodes = N
        manager = pywrapcp.RoutingIndexManager(total_nodes, 1, 0)

    routing = pywrapcp.RoutingModel(manager)

    # Capture matrix as a local variable to avoid closure issues
    _matrix = matrix
    _manager = manager

    def dist_cb(fi, ti):
        return _matrix[_manager.IndexToNode(fi)][_manager.IndexToNode(ti)]

    cb_idx = routing.RegisterTransitCallback(dist_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(cb_idx)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Only use GLS (local search) when there are enough stops to benefit.
    # GLS REQUIRES a non-zero time limit — without it OR-Tools errors out.
    # For small routes (<=6 stops) PATH_CHEAPEST_ARC alone is already optimal.
    if n > 6:
        params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        # Minimum 3s, scale up with size, cap at 10s
        params.time_limit.seconds = min(max(3, (n - 6) // 2 + 3), 10)
    # For small routes: no time limit needed, no GLS — just fast greedy

    log.info(f"TSP: {n} stops, warehouse={'yes' if warehouse else 'no'}, "
             f"GLS={'yes' if n > 6 else 'no'}")

    sol = routing.SolveWithParameters(params)

    if not sol:
        log.warning("TSP solver returned no solution, falling back to original order")
        return list(range(n))

    plan, curr = [], routing.Start(0)
    while not routing.IsEnd(curr):
        node = manager.IndexToNode(curr)
        if warehouse:
            # Skip warehouse node (0) and dummy end node (N)
            if 0 < node < N:
                plan.append(node - 1)   # shift back to stops index
        else:
            plan.append(node)
        curr = sol.Value(routing.NextVar(curr))

    log.info(f"TSP result: {plan}")

    # Sanity check
    if sorted(plan) != list(range(n)):
        log.warning(f"TSP plan {plan} doesn't cover all {n} stops, falling back")
        return list(range(n))

    return plan


# ── Geographic clustering ─────────────────────────────────
def _cluster(stops: List[StopModel], k: int) -> List[List[int]]:
    k = min(k, len(stops))
    if k == 1:
        return [list(range(len(stops)))]

    step      = max(1, len(stops) // k)
    centroids = [(stops[i * step].lat, stops[i * step].lon) for i in range(k)]

    def nearest(s: StopModel) -> int:
        best, best_d = 0, float("inf")
        for ci, (clat, clon) in enumerate(centroids):
            d = haversine(s, StopModel(lat=clat, lon=clon))
            if d < best_d:
                best_d = d; best = ci
        return best

    for _ in range(30):
        clusters: List[List[int]] = [[] for _ in range(k)]
        for i, s in enumerate(stops):
            clusters[nearest(s)].append(i)

        new_centroids = []
        for ci, members in enumerate(clusters):
            if members:
                new_centroids.append((
                    sum(stops[m].lat for m in members) / len(members),
                    sum(stops[m].lon for m in members) / len(members),
                ))
            else:
                new_centroids.append(centroids[ci])

        if new_centroids == centroids:
            break
        centroids = new_centroids

    clusters = [[] for _ in range(k)]
    for i, s in enumerate(stops):
        clusters[nearest(s)].append(i)

    return [c for c in clusters if c]


# ── Endpoints ─────────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/api/optimize")
async def optimize(data: RouteRequest):
    n = len(data.stops)
    if n < 2:
        return {"optimized_indices": list(range(n))}
    try:
        result = _tsp_order(data.stops, data.warehouse)
        return {"optimized_indices": result}
    except Exception as e:
        log.error(f"/api/optimize error: {traceback.format_exc()}")
        # Fallback — return unoptimized order rather than 500
        log.warning("Falling back to unoptimized order")
        return {"optimized_indices": list(range(n))}


@app.post("/api/split")
async def split(data: SplitRequest):
    n = len(data.stops)
    k = min(data.num_routes, n)
    if k < 1:
        raise HTTPException(400, "num_routes must be >= 1")
    try:
        clusters = _cluster(data.stops, k)
    except Exception as e:
        log.error(f"/api/split clustering error: {traceback.format_exc()}")
        # Fallback — split evenly without clustering
        clusters = []
        size = max(1, n // k)
        all_indices = list(range(n))
        for i in range(0, n, size):
            clusters.append(all_indices[i:i+size])

    result = []
    for cluster_indices in clusters:
        cluster_stops = [data.stops[i] for i in cluster_indices]
        try:
            order = _tsp_order(cluster_stops, data.warehouse, time_limit_seconds=5)
        except Exception as e:
            log.error(f"/api/split tsp error on cluster: {traceback.format_exc()}")
            # Fallback — unoptimized order for this cluster
            order = list(range(len(cluster_stops)))
        result.append({
            "stop_indices":    cluster_indices,
            "optimized_order": order,
        })
    return {"routes": result}
