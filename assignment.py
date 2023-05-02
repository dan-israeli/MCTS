# imports
import time
import random
import math
from copy import deepcopy
from Simulator import Simulator


# ids
IDS = ["209190172", "322794629"]

# constants for the "check_valid" and "result" functions
ACTION_NAME, TAXI_NAME, NEW_LOCATION, PASSENGER_NAME = 0, 1, 2, 2

# constant for the "act" function
MAX_TIME = 4.85


def check_valid(new_sa, sa_list, taxis, rival_taxis_locations):
    """
    Gets a new sub-action 'new_sa' (for example, ('pick up', 'taxi 1', 'Yossi')), and a list of other
    sub-actions, and returns whether 'new_sa' is allowed given 'sa_list'.
    """

    # can't move to a location were a rival taxi is already
    if new_sa[ACTION_NAME] == "move" and tuple(new_sa[NEW_LOCATION]) in rival_taxis_locations:
        return False

    for sa in sa_list:

        if new_sa[ACTION_NAME] != "move" and sa[ACTION_NAME] == "move":
            if tuple(taxis[new_sa[TAXI_NAME]]["location"]) == tuple(sa[NEW_LOCATION]):
                return False

        elif new_sa[ACTION_NAME] == "move" and sa[ACTION_NAME] != "move":
            if tuple(new_sa[NEW_LOCATION]) == tuple(taxis[sa[TAXI_NAME]]["location"]):
                return False

        elif new_sa[ACTION_NAME] == "move" and sa[ACTION_NAME] == "move":
            if tuple(new_sa[NEW_LOCATION]) == tuple(sa[NEW_LOCATION]):
                return False

    return True


def find_action_list(i, n, sa_lists, sub_res, res, taxis, rival_taxis_locations):
    """
    Finds all possible actions in a given state and appends them to res.
    """

    # sa = sub-action (atomic action of one taxi, out of list of actions)
    if i == n:
        sub_res = tuple(sub_res.copy())
        res.append(sub_res)
        return

    sa_list = sa_lists[i]
    for j in range(len(sa_list)):

        if check_valid(sa_list[j], sub_res, taxis, rival_taxis_locations):
            sub_res.append(sa_list[j])
            find_action_list(i + 1, n, sa_lists, sub_res, res, taxis, rival_taxis_locations)
            sub_res.pop()


def actions(state, player_number):
    """Returns all the actions that can be executed in the given
    state. The result should be a tuple (or other iterable) of actions
    as defined in the problem description file"""

    mapp, taxis, passengers = state["map"], state["taxis"], state["passengers"]

    # sa = sub action (an action is defined as a series of one sub-action for every taxi)
    sa_per_taxi = {}
    rival_taxis_locations = []

    for taxi_name, taxi_dict in taxis.items():

        if taxi_dict["player"] == player_number:
            sa_per_taxi[taxi_name] = []

        else:
            rival_taxis_locations.append(taxi_dict["location"])

    for taxi_name, taxi_dict in taxis.items():

        # going over only the relevant taxis of the player
        if taxi_dict["player"] != player_number:
            continue

        (t_x, t_y) = taxi_dict["location"]

        # wait
        action_tup = ("wait", taxi_name)
        sa_per_taxi[taxi_name].append(action_tup)

        # pick up and drop off
        for passenger_name, passenger_dict in passengers.items():

            # indicates that the passenger arrived to their destination
            # if so, no taxi will pick him up
            if passenger_dict["location"] == passenger_dict["destination"]:
                continue

            # pick up
            if taxi_dict["location"] == passenger_dict["location"] and taxi_dict["capacity"] > 0:
                sa_per_taxi[taxi_name].append(("pick up", taxi_name, passenger_name))

            # drop off
            # the taxi is at passenger's destination AND the taxi is the one that picked up the passenger
            if taxi_dict["location"] == passenger_dict["destination"] and taxi_name == passenger_dict["location"]:
                sa_per_taxi[taxi_name].append(("drop off", taxi_name, passenger_name))

        # move
        n, m = len(mapp), len(mapp[0])

        # up
        if t_x != 0 and mapp[t_x - 1][t_y] != "I":
            sa_per_taxi[taxi_name].append(("move", taxi_name, (t_x - 1, t_y)))
        # down
        if t_x != n - 1 and mapp[t_x + 1][t_y] != "I":
            sa_per_taxi[taxi_name].append(("move", taxi_name, (t_x + 1, t_y)))
        # left
        if t_y != 0 and mapp[t_x][t_y - 1] != "I":
            sa_per_taxi[taxi_name].append(("move", taxi_name, (t_x, t_y - 1)))
        # right
        if t_y != m - 1 and mapp[t_x][t_y + 1] != "I":
            sa_per_taxi[taxi_name].append(("move", taxi_name, (t_x, t_y + 1)))

    sa_per_taxi_lists = []

    for sa_per_taxi_list in sa_per_taxi.values():
        sa_per_taxi_lists.append(sa_per_taxi_list)

    actions_list = []
    find_action_list(0, len(sa_per_taxi_lists), sa_per_taxi_lists, [], actions_list, taxis, rival_taxis_locations)

    return tuple(actions_list)


def result(state, action):
    """Return the state that results from executing the given
    action in the given state. The action must be one of
    self.actions(state)."""

    new_state = deepcopy(state)
    taxis, passengers = new_state["taxis"], new_state["passengers"]

    # sa = sub action (an action is defined as a series of one sub-action for every taxi)
    for sa in action:
        sa_name, taxi_name = sa[ACTION_NAME], sa[TAXI_NAME]

        if sa_name == "wait":
            continue

        elif sa_name == "pick up":
            # the passenger we pick up
            passenger_name = sa[PASSENGER_NAME]

            passengers[passenger_name]["location"] = taxi_name
            taxis[taxi_name]["capacity"] -= 1

        elif sa_name == "drop off":
            # the passenger we drop off
            passenger_name = sa[PASSENGER_NAME]

            passengers[passenger_name]["location"] = passengers[passenger_name]["destination"]
            taxis[taxi_name]["capacity"] += 1

        elif sa_name == "move":
            taxis[taxi_name]["location"] = sa[NEW_LOCATION]

    return new_state


def find_new_state_action_tuples(state, player_number):
    actions_lst = actions(state, player_number)
    new_state_action_tuples = []

    for action in actions_lst:
        new_state = result(state, action)
        new_tup = (new_state, action)
        new_state_action_tuples.append(new_tup)

    return new_state_action_tuples


def remove_wait_actions(actions):
    updated_actions, n = [], 0

    for action in actions:
        wait_flag = False

        for sa in action:
            if sa[ACTION_NAME] == "wait":
                wait_flag = True
                break

        # including only actions that don't contain the sub-action "wait"
        if not wait_flag:
            n += 1
            updated_actions.append(action)

    return tuple(updated_actions), n


def select_action(state, player_num, remove_wait=False):
    available_actions = actions(state, player_num)
    max_pick_ups, max_drop_offs = 0, 0

    for action in available_actions:
        pick_up_cnt, drop_off_cnt = 0, 0

        for sa in action:

            if sa[ACTION_NAME] == "drop off":
                drop_off_cnt += 1

            elif sa[ACTION_NAME] == "pick up":
                pick_up_cnt += 1

        # the action that contains the most drop_offs
        if drop_off_cnt > max_drop_offs:
            max_drop_offs = drop_off_cnt
            drop_off_action = action

        # the action that contains the most pick_ups
        elif pick_up_cnt > max_pick_ups:
            max_pick_ups = pick_up_cnt
            pick_up_action = action

    # found an action that contains drop-off
    if max_drop_offs > 0:
        return drop_off_action

    # found an action that contains pick-up
    if max_pick_ups > 0:
        return pick_up_action

    # there isn't an action that contains drop-off or pick-up, we will choose an action randomly

    if remove_wait:
        updated_available_actions, n = remove_wait_actions(available_actions)

        # if there's an action that doesn't contain the sub-action "wait" then n > 0
        # we will choose (randomly) from these actions
        if n > 0:
            return random.sample(updated_available_actions, k=1)[0]

    # must choose an action that contains the sub-action "wait"
    return random.sample(available_actions, k=1)[0]


class Agent:

    def __init__(self, initial_state, player_num):
        self.ids = IDS
        self.initial_state = initial_state
        self.t = 0
        self.player_num = player_num
        self.rival_player_num = 3 - player_num

        # the number of turns played so far
        self.turns = 0

    def selection(self, node):
        current_node = node

        # continue the loop until reached to a node with undiscovered children
        while len(current_node.undiscovered_state_action_tuples) == 0:
            self.t += 1
            current_node = current_node.find_max_child(self.t)

        return current_node

    def expansion(self, parent_node):
        self.t += 1
        return parent_node.discover_child(self.player_num)

    def simulation(self, new_node):
        state = new_node.state
        simulator = Simulator(state)

        # the real simulation of the game doesn't update the "turns to go" after each action
        # therefore "turns to go" in all given states are as the initial state
        # we use self.turns (the number of turns played) to get the real number of "turns to go"
        turns_to_go = state["turns to go"] - self.turns

        for i in range(turns_to_go):
            # simulate player's action (the action is chosen randomly)
            player_action = select_action(state, self.player_num, remove_wait=True)
            simulator.act(player_action, self.player_num)
            next_state = simulator.get_state()

            # simulate rival player's action (the action is chosen randomly)
            rival_player_action = select_action(next_state, self.rival_player_num, remove_wait=True)
            simulator.act(rival_player_action, self.rival_player_num)
            state = simulator.get_state()

        simulation_result = simulator.get_score()[f"player {self.player_num}"]
        return simulation_result

    def backpropagation(self, node, simulation_result):
        current_node = node

        # continue the loop until reach the root
        while current_node is not None:
            current_node.update_emp_score_mean(simulation_result)
            current_node = current_node.get_parent()

    def act(self, state):
        start_time = time.time()
        root = Node(state, self.player_num, action=None, parent=None)
        # each time the "act" function is called, a turn is played
        self.turns += 1

        while time.time() - start_time <= MAX_TIME:
            node = self.selection(root)
            new_node = self.expansion(node)
            simulation_result = self.simulation(new_node)
            self.backpropagation(new_node, simulation_result)

        best_action = root.find_best_action(self.player_num)
        return best_action

# -----------------------------------------------------------------------------------

class UCTAgent:

    def __init__(self, initial_state, player_num):
        self.initial_state = initial_state
        self.t = 0
        self.player_num = player_num
        self.rival_player_num = 3 - player_num

    def selection(self, node):
        current_node = node

        # continue the loop until reached to a node with undiscovered children
        while len(current_node.undiscovered_state_action_tuples) == 0:
            self.t += 1
            current_node = current_node.find_max_child(self.t)

        return current_node

    def expansion(self, parent_node):
        self.t += 1
        return parent_node.discover_child(self.player_num)

    def simulation(self, new_node):
        state = new_node.state
        simulator = Simulator(state)

        for i in range(state["turns to go"]):
            # simulate player's action (the action is chosen randomly)
            player_available_actions = actions(state, self.player_num)
            player_action = random.sample(player_available_actions, k=1)[0]
            simulator.act(player_action, self.player_num)
            next_state = simulator.get_state()

            # simulate rival player's action (the action is chosen randomly)
            rival_player_available_actions = actions(next_state, self.rival_player_num)
            rival_player_action = random.sample(rival_player_available_actions, k=1)[0]
            simulator.act(rival_player_action, self.rival_player_num)
            state = simulator.get_state()

        simulation_result = simulator.get_score()[f"player {self.player_num}"]
        return simulation_result

    def backpropagation(self, node, simulation_result):
        current_node = node

        # continue the loop until reach the root
        while current_node is not None:
            current_node.update_emp_score_mean(simulation_result)
            current_node = current_node.get_parent()

    def act(self, state):
        start_time = time.time()
        root = Node(state, self.player_num, action=None, parent=None)

        while time.time() - start_time <= MAX_TIME:
            node = self.selection(root)
            new_node = self.expansion(node)
            simulation_result = self.simulation(new_node)
            self.backpropagation(new_node, simulation_result)

        best_action = root.find_best_action_UCT()
        return best_action


class Node:

    def __init__(self, state, player_number, action, parent):
        self.state = state
        self.action = action
        self.parent = parent

        self.n = 0
        self.score_sum = 0
        self.emp_score_mean = 0

        self.undiscovered_state_action_tuples = find_new_state_action_tuples(state, player_number)
        self.discovered_children = []

    def get_action(self):
        return self.action

    def get_emp_score_mean(self):
        return self.emp_score_mean

    def get_parent(self):
        return self.parent

    def get_UCB1(self, t):
        return self.emp_score_mean + (2 * math.log(t) / self.n) ** 0.5

    def update_emp_score_mean(self, new_score):
        self.n += 1
        self.score_sum += new_score
        self.emp_score_mean = self.score_sum / self.n

    def discover_child(self, player_number):
        # find new (state, action) tuple and remove if from the undiscovered list (randomly)
        new_child_tup = random.sample(list(self.undiscovered_state_action_tuples), k=1)[0]
        self.undiscovered_state_action_tuples.remove(new_child_tup)

        # create a new node from 'new_state', 'new_action'
        (new_child_state, new_child_action) = new_child_tup
        new_child = Node(new_child_state, player_number, new_child_action, parent=self)
        self.discovered_children.append(new_child)

        return new_child

    def find_max_child(self, t):
        # finds the child with the highest UCB1 value
        return max(self.discovered_children, key=lambda child: child.get_UCB1(t))

    def find_best_action_UCT(self):
        # finds the root's child with the highest empirical score mean
        # returns the action the leads to the state it represents
        max_child = max(self.discovered_children, key=lambda child: child.get_emp_score_mean())
        best_action = max_child.get_action()

        return best_action

    def find_best_action(self, player_num):
        temp_action = select_action(self.state, player_num)

        for sa in temp_action:
            # if temp action contains a sub-action which is pick-up or drop-off we will return it
            if sa[ACTION_NAME] == "pick up" or sa[ACTION_NAME] == "drop off":
                return temp_action

        # else, we will return the action that maximizes the empirical score mean
        return self.find_best_action_UCT()
