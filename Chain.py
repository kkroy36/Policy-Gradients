from random import randint
from copy import deepcopy
import itertools
from subprocess import Popen
from os import system,waitpid,listdir
from math import exp

Values = {}
Count = {}
actions = ["left","right"]

class Chain(object):
    '''class to represent the 50-chain'''

    def __init__(self):
        '''class constructor'''
        self.chain = [0 for i in range(50)]
        self.chain[13],self.chain[38] = 1,1
        self.actions = ["left","right"]
        self.start = randint(0,49)

    def goalPositions(self):
        '''returns the goal positions on the chain'''
        return [13,14]

    def valid(self,cell):
        '''check if chain cell is valid'''
        if cell < 0 or cell > 49:
            return False
        return True

    def takeAction(self,cell,action):
        '''returns new state
           invalid action does nothing
        '''
        if cell in self.goalPositions():
            return "winner"
        if action not in self.actions:
            return cell
        elif action in self.actions:
            if action =="left":
                if self.valid(cell-1):
                    if cell-1 in self.goalPositions():
                        return "winner"
                    else:
                        return cell-1
                elif not self.valid(cell-1):
                    return cell
            elif action == "right":
                if self.valid(cell+1):
                    if cell+1 in self.goalPositions():
                        return "winner"
                    else:
                        return cell+1
                elif not self.valid(cell+1):
                    return cell

    def kernelProb(self,cell,kernel,std):
        '''gaussian kernel (discretized)'''
        distance = (cell-kernel)**2
        factor = exp((-1*distance)/float(std))
        return factor

    def factored(self,cell):
        '''returns predicate form of state'''
        if cell == "winner":
            cell = 13
        kernels = self.goalPositions()
        Z = 0
        factoredCell = []
        for kernel in kernels:
            prob = self.kernelProb(cell,kernel,4)
            factoredCell += [prob]
            Z += prob
        factoredCell = [(prob*10)/float(Z) for prob in factoredCell]
        discretized = ["high" if factoredCell[i] > 9 else "low" for i in range(2)]
        return discretized

d = Chain()

def get_facts(state,state_number):
    pred = "highValue(s"
    '''
    if "high" in d.factored(state):
        pred += str(state_number)+",yes)."
    else:
        pred += str(state_number)+",no)."
    '''
    if (state <= 18 and state >=13) or (state <=13 and state >= 8):
        pred += str(state_number)+",yes)."
    else:
        pred += str(state_number)+",no)."
    return [pred]

def get_RDN_facts_pos_neg(state_sequence):
    facts,pos,neg = [],[],[]
    for state in state_sequence[:-1]:
        facts += get_facts(state[0],state[2])
        if state[1] !="left":
            neg += ["left(s"+str(state[2])+")."]
        else:
            pos += ["left(s"+str(state[2])+")."]
    return (facts,pos,neg)

def goal_state(state):
    '''returns True if goal state attained'''
    if state == "winner":
        return True
    return False

def update_values(state_sequence):
    discount_factor = 0.95
    goal_state_value = 10
    goal_state = state_sequence[-1]
    state_sequence_without_goal_in_reverse = state_sequence[:-1][::-1]
    length_of_state_sequence_without_goal_in_reverse = len(state_sequence_without_goal_in_reverse)
    for i in range(length_of_state_sequence_without_goal_in_reverse):
        state = state_sequence_without_goal_in_reverse[i][0]
        action = state_sequence_without_goal_in_reverse[i][1]
        key = (state,action)
        if key in Count:
            Count[key] += 1
        else:
            Count[key] = 1
        new_value = (discount_factor**(i+1))*goal_state_value
        if key in Values:
            old_value = Values[key]
        else:
            old_value = 0
        Values[key] = old_value + (1/float(Count[key]))*(new_value-old_value)
    Values[goal_state] = goal_state_value

def write_facts(opText):
    '''writes facts to file'''
    with open("train/train_facts.txt", "a") as myfile:
        for i in range(len(opText)):
            myfile.write(opText[i]+'\n')

def write_pos_neg(positiveList,negativeList):
    '''writes positive and negative actions to file'''
    with open("train/train_pos.txt", "a") as myfile:
        for i in range(len(positiveList)):
            myfile.write(positiveList[i]+'\n')

    with open("train/train_neg.txt", "a") as myfile:
        for i in range(len(negativeList)):
            myfile.write(negativeList[i]+'\n')

def write_test_facts(opText):
    '''writes facts to file'''
    with open("test/test_facts.txt", "a") as myfile:
        for i in range(len(opText)):
            myfile.write(opText[i]+'\n')

def write_test_pos(positiveList):
    '''writes positive and negative actions to file'''
    with open("test/test_pos.txt", "a") as myfile:
        for i in range(len(positiveList)):
            myfile.write(positiveList[i]+'\n')

def call_process(call):
    '''spawns a process to execute a shell process'''
    process = Popen(call,shell=True)
    waitpid(process.pid,0)

def make_train_and_test_directory():
    '''makes the train directory'''
    call_process('mkdir train')
    call_process('cp train_bk.txt train')
    call_process('mkdir test')
    call_process('cp train_bk.txt test')
    call_process('mv test/train_bk.txt test/test_bk.txt')

def remove_files():
    '''removes files after each run'''
    call_process('rm train/train_facts.txt')
    call_process('rm train/train_pos.txt')
    call_process('rm train/train_neg.txt')

def remove_test_files():
    '''remove test files after inference'''
    call_process('rm test/*.db')
    call_process('rm test/test_facts.txt')
    call_process('rm test/test_pos.txt')
    call_process('rm test/test_neg.txt')

def read_file(filename):
    '''reads file lines'''
    if filename in listdir("test"):
        with open(filename) as file:
            return file.read().splitlines()
    else:
        return False

def perform_inference_and_choose(state,state_number,random=False):
    if random:
        return actions[randint(0,1)]
    acceptance_threshold = 0.5
    test_facts = get_facts(state,state_number)
    test_pos = ["left(s"+str(state_number)+")."]
    write_test_facts(test_facts)
    write_test_pos(test_pos)
    call_process('touch test/test_neg.txt')
    call_process('java -jar BoostSRL-v1-0.jar -i -test test -model train/models -target left -aucJarPath . ')
    result_file = read_file("test/results_left.db")
    if not result_file:
        remove_test_files()
        return False
    result = result_file[0]
    prob = float(result.split(')')[1])
    if prob > acceptance_threshold:
        remove_test_files()
        return "left"
    else:
        remove_test_files()
        return "right"

def main():
    state_number = 1
    pos_action = []
    facts,pos,neg = [],[],[]
    max_tolerance = 10
    batch_size = 2
    burn_in_time = 100
    number_of_trajectories = burn_in_time + 10
    if "train" not in listdir(".") or "test" not in listdir("."):
        make_train_and_test_directory()
    for trajectory in range(number_of_trajectories):
        max_tolerance_reached = False
        state = d.start
        state_sequence = []
        while not goal_state(state):
            state_copy = deepcopy(state)
            if "models" not in listdir("train") or (trajectory+1) < burn_in_time:
                action_specification = perform_inference_and_choose(state,deepcopy(state_number),random=True)
            else:
                if len(state_sequence) > max_tolerance and not max_tolerance_reached:
                    state_sequence = []
                    max_tolerance_reached = True
                if not max_tolerance_reached:
                    action_specification = perform_inference_and_choose(state,deepcopy(state_number))
                else:
                    action_specification = perform_inference_and_choose(state,deepcopy(state_number),random=True)
            state_sequence.append((state_copy,action_specification,deepcopy(state_number)))
            state = d.takeAction(state,action_specification)
            state_number += 1
        state_sequence.append(deepcopy(state))
        update_values(state_sequence)
        facts_pos_neg = get_RDN_facts_pos_neg(state_sequence)
        facts += facts_pos_neg[0]
        pos += facts_pos_neg[1]
        neg += facts_pos_neg[2]
        state_number += len(state_sequence)
        if (trajectory+1)%batch_size == 0 and (trajectory+1) > burn_in_time:
            write_facts(facts)
            write_pos_neg(pos,neg)
            facts,pos,neg = [],[],[]
            call_process('rm -rf train/models')
            call_process('java -jar BoostSRL-v1-0.jar -l -train train -target left')
            remove_files()
main()
