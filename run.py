
import random

# ---------------- HARBOUR SETTINGS ----------------

GRID_WIDTH = 24
GRID_HEIGHT = 16
TOTAL_WORKERS = 10
RUN_LENGTH = 600
CARGO_PER_SHIP = 8

WAREHOUSE = (1, 0)

BERTHS = {
    "B1": (3, 15),
    "B2": (8, 15),
    "B3": (15, 15),
    "B4": (20, 15)
}

UNSAFE_BERTHS = ["B1", "B4"]
SEEDS = [11, 12, 13]


# ---------------- AGENT CLASSES ----------------

class Ship:
    def __init__(self, ship_id, preferred_berth):
        self.ship_id = ship_id
        self.preferred_berth = preferred_berth
        self.berth = None
        self.remaining_cargo = CARGO_PER_SHIP
        self.delivered_cargo = 0


class Dockworker:
    def __init__(self, worker_id, policy):
        self.worker_id = worker_id
        self.policy = policy
        self.position = WAREHOUSE
        self.target_ship = None
        self.carrying = False
        self.delivered = 0
        self.knockouts = 0
        self.known_storms = []
        self.stunned_until = 0


class Lookout:
    def __init__(self, storm_starts):
        self.storm_starts = storm_starts
        self.warnings = []

    def check_storms(self, tick):
        for start in self.storm_starts:
            if tick == start - 5:
                self.warnings.append(start)
                print(f"Tick {tick}: Lookout warns about an approaching storm.")


# ---------------- ENVIRONMENT SETUP ----------------

def generate_scenario(seed):
    rng = random.Random(seed)

    storm_starts = []

    while len(storm_starts) < 3:
        candidate = rng.randint(60, 540)

        if all(abs(candidate - old) >= 15 for old in storm_starts):
            storm_starts.append(candidate)

    storm_starts.sort()

    arrivals = []
    tick = rng.randint(6, 10)
    ship_id = 1

    berth_names = list(BERTHS.keys())

    while tick < RUN_LENGTH:
        preferred_berth = rng.choice(berth_names)
        arrivals.append((tick, ship_id, preferred_berth))

        ship_id += 1
        tick += rng.randint(6, 10)

    return storm_starts, arrivals


def display_harbour():
    print("\nSTORMWATCH HARBOUR")
    print("=" * 48)

    for y in range(GRID_HEIGHT - 1, -1, -1):
        row = ""

        for x in range(GRID_WIDTH):
            position = (x, y)

            if position == WAREHOUSE:
                row += "W "
            elif position in BERTHS.values():
                row += "B "
            else:
                row += ". "

        print(row)

    print("=" * 48)
    print("W = Warehouse | B = Berth")


# ---------------- MOVEMENT AND STORM HELPERS ----------------

def move_one_step(current, destination):
    x, y = current
    target_x, target_y = destination

    if x < target_x:
        x += 1
    elif x > target_x:
        x -= 1
    elif y < target_y:
        y += 1
    elif y > target_y:
        y -= 1

    return (x, y)


def distance_between(first, second):
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def storm_is_active(tick, storm_starts):
    return any(start <= tick < start + 15 for start in storm_starts)


def unsafe_storm_expected(worker, ship, tick):
    if ship.berth not in UNSAFE_BERTHS:
        return False

    travel_time = distance_between(
        worker.position, BERTHS[ship.berth]
    )

    expected_arrival = tick + travel_time

    for start in worker.known_storms:
        if start <= expected_arrival < start + 15:
            return True

    return False


# ---------------- QUARTERMASTER ----------------

def assign_waiting_ships(ships):
    occupied = [
        ship.berth for ship in ships
        if ship.berth is not None
    ]

    for ship in ships:
        if ship.berth is not None:
            continue

        available = [
            name for name in BERTHS
            if name not in occupied
        ]

        if not available:
            break

        if ship.preferred_berth in available:
            chosen = ship.preferred_berth
        else:
            chosen = available[0]

        ship.berth = chosen
        occupied.append(chosen)


# ---------------- DOCKWORKER POLICIES ----------------

def choose_ship(worker, ships, tick):
    available = [
        ship for ship in ships
        if ship.berth is not None and ship.remaining_cargo > 0
    ]

    if worker.policy == "model-based":
        available = [
            ship for ship in available
            if not unsafe_storm_expected(worker, ship, tick)
        ]

    if not available:
        return None

    return min(
        available,
        key=lambda ship: distance_between(
            worker.position, BERTHS[ship.berth]
        )
    )


def worker_step(worker, ships, tick, storm_starts, lookout):
    if tick < worker.stunned_until:
        return

    # Model-based workers remember Lookout warnings.
    if worker.policy == "model-based":
        worker.known_storms = list(lookout.warnings)

    # Return to warehouse when carrying cargo.
    if worker.carrying:
        worker.position = move_one_step(
            worker.position, WAREHOUSE
        )

        if worker.position == WAREHOUSE:
            worker.carrying = False
            worker.delivered += 1
            worker.target_ship.delivered_cargo += 1
            worker.target_ship = None

        return

    # Select a ship if the worker has no suitable target.
    if (
        worker.target_ship is None
        or worker.target_ship.remaining_cargo <= 0
        or worker.target_ship.berth is None
    ):
        worker.target_ship = choose_ship(worker, ships, tick)

    # Model-based worker changes target if a storm is expected.
    if (
        worker.policy == "model-based"
        and worker.target_ship is not None
        and unsafe_storm_expected(worker, worker.target_ship, tick)
    ):
        worker.target_ship = choose_ship(worker, ships, tick)

    if worker.target_ship is None:
        return

    ship = worker.target_ship
    berth_position = BERTHS[ship.berth]

    # Check for a knockout at an unsafe berth.
    if worker.position == berth_position:
        if (
            storm_is_active(tick, storm_starts)
            and ship.berth in UNSAFE_BERTHS
        ):
            worker.knockouts += 1
            worker.position = WAREHOUSE
            worker.target_ship = None
            worker.stunned_until = tick + 3
            return

        if ship.remaining_cargo > 0:
            worker.carrying = True
            ship.remaining_cargo -= 1

        return

    # Move towards the assigned ship.
    worker.position = move_one_step(
        worker.position, berth_position
    )


# ---------------- SIMULATION ----------------

def run_simulation(seed, policy, scenario):
    storm_starts, arrivals = scenario

    workers = [
        Dockworker(i + 1, policy)
        for i in range(TOTAL_WORKERS)
    ]

    lookout = Lookout(storm_starts)
    ships = []
    arrival_index = 0

    for tick in range(RUN_LENGTH):

        lookout.check_storms(tick)

        # Add ships arriving at this tick.
        while (
            arrival_index < len(arrivals)
            and arrivals[arrival_index][0] == tick
        ):
            _, ship_id, preferred_berth = arrivals[arrival_index]

            ships.append(Ship(ship_id, preferred_berth))
            arrival_index += 1

        # Assign available berths to waiting ships.
        assign_waiting_ships(ships)

        # Workers perform their tasks.
        for worker in workers:
            worker_step(
                worker, ships, tick, storm_starts, lookout
            )

        # Remove ships whose full cargo has been delivered.
        ships = [
            ship for ship in ships
            if ship.delivered_cargo < CARGO_PER_SHIP
        ]

        # Free berths and assign them to waiting ships.
        assign_waiting_ships(ships)

    total_delivered = sum(worker.delivered for worker in workers)
    total_knockouts = sum(worker.knockouts for worker in workers)

    return {
        "seed": seed,
        "policy": policy,
        "ships": len(arrivals),
        "cargo": total_delivered,
        "knockouts": total_knockouts,
        "warnings": len(lookout.warnings)
    }


# ---------------- RUN BOTH POLICIES ----------------

def main():
    display_harbour()

    results = []

    for seed in SEEDS:
        print(f"\n========== SEED {seed} ==========")

        # Generate one scenario and reuse it for both policies.
        scenario = generate_scenario(seed)

        for policy in ["baseline", "model-based"]:
            result = run_simulation(seed, policy, scenario)
            results.append(result)

            print(
                f"{policy.upper()}: "
                f"Ships={result['ships']}, "
                f"Cargo Delivered={result['cargo']}, "
                f"Knockouts={result['knockouts']}, "
                f"Warnings={result['warnings']}"
            )

    print("\n========== FINAL RESULTS ==========")
    print("Seed | Policy      | Cargo Delivered | Knockouts")

    for result in results:
        print(
            f"{result['seed']:4} | "
            f"{result['policy']:11} | "
            f"{result['cargo']:15} | "
            f"{result['knockouts']}"
        )

    print("\n========== AVERAGES ==========")

    for policy in ["baseline", "model-based"]:
        policy_results = [
            result for result in results
            if result["policy"] == policy
        ]

        average_cargo = sum(
            result["cargo"] for result in policy_results
        ) / len(policy_results)

        average_knockouts = sum(
            result["knockouts"] for result in policy_results
        ) / len(policy_results)

        print(
            f"{policy.upper()}: "
            f"Average cargo = {average_cargo:.2f}, "
            f"Average knockouts = {average_knockouts:.2f}"
        )


if __name__ == "__main__":
    main()
