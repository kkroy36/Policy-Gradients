from random import randint
from copy import deepcopy
import itertools
from subprocess import Popen
from os import system,waitpid,listdir
from random import randint

Values = {}
Count = {}
actions = ["hit","stand"]

class Game(object):
    '''class for new blackjack game'''

    def __init__(self):
        '''class constructor'''
        self.cards = self.makeCardDeck()
        self.initPSum = self.drawTwo(tot=True)
        self.initDCards = self.drawTwo()
        self.start = (self.initPSum,self.initDCards[0])
        self.actions = ["hit","stand"]

    def bust(self,state):
        '''checks if player has bust'''
        pSum = state[0]
        if pSum > 21:
            return True
        return False

    def takeAction(self,state,action):
        '''performs action and returns state'''
        if state == "loser":
            return state
        if action not in self.actions:
            return state
        if action == "hit":
            card = self.drawCard()
            if not card:
                return "loser"
            pSum = state[0]
            npSum = float(pSum)+float(card)
            if self.bust((npSum,state[1])):
                return "loser"
            return (npSum,state[1])
        return state

    def makeCardDeck(self):
        '''makes a deck of 52 cards'''
        cards = [10 for i in range(16)]
        cards += [11 for i in range(4)]
        for i in range(1,10):
            cards += [i for j in range(4)]
        return cards

    def drawCard(self):
        '''draws a random card'''
        N = len(self.cards)
        if N == 0:
            return False
        i = randint(0,N-1)
        card = self.cards[i]
        self.cards.remove(card)
        return card

    def drawTwo(self,tot=False):
        '''draws two cards for player'''
        card1 = self.drawCard()
        card2 = self.drawCard()
        total = float(card1)+float(card2)
        if tot:
            return total
        else:
            return (card1,card2)

#d = Game()

def get_facts(state,state_number):
    facts = []
    pSum = state[0]
    dealer_face_card = state[1]
    if pSum > 18:
        facts += ["playerSum(s"+str(state_number)+",high)."]
    elif pSum > 13 and pSum <= 18:
        facts += ["playerSum(s"+str(state_number)+",medium)."]
    else:
        facts += ["playerSum(s"+str(state_number)+",low)."]
    facts += ["faceCard(s"+str(state_number)+","+str(dealer_face_card)+")."]
    return facts

def get_RDN_facts_pos_neg(state_sequence):
    facts,pos,neg = [],[],[]
    for state in state_sequence[:-1]:
        facts += get_facts(state[0],state[2])
        action = state[1]
        if action == "hit":
            pos += ["hit(s"+str(state[2])+")."]
        else:
            neg += ["hit(s"+str(state[2])+")."]
    return (facts,pos,neg)

def goal_state(state):
    if state == "loser":
        return True
    return False

def update_values(state_sequence):
    discount_factor = 0.95
    goal_state = state_sequence[-1]
    goal_state_value = -10
    state_sequence_without_goal_in_reverse = state_sequence[:-1][::-1]
    length_of_state_sequence_without_goal_in_reverse = len(state_sequence_without_goal_in_reverse)
    for i in range(length_of_state_sequence_without_goal_in_reverse):
        state = state_sequence_without_goal_in_reverse[i][0]
        if i == length_of_state_sequence_without_goal_in_reverse-1:
            hit_value = stand_value = goal_state_value
        else:
            next_state = state_sequence_without_goal_in_reverse[i+1][0]
            if (next_state,"hit") in Values.keys():
                hit_value = Values[(next_state,"hit")]
            else:
                hit_value = 0
            if (next_state,"stand") in Values.keys():
                stand_value = Values[(next_state,"stand")]
            else:
                stand_value = 0
        action = state_sequence_without_goal_in_reverse[i][1]
        key = (state,action)
        if key in Count:
            Count[key] += 1
        else:
            Count[key] = 1
        new_value = -1 + (hit_value+stand_value)/float(2)
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
        with open("test/"+filename) as file:
            return file.read().splitlines()
    else:
        return False

def perform_inference_and_choose(state,state_number,random=False):
    if random:
        return actions[randint(0,1)]
    acceptance_threshold = 0.5
    test_facts = get_facts(state,state_number)
    test_pos = ["hit(s"+str(state_number)+")."]
    write_test_facts(test_facts)
    write_test_pos(test_pos)
    call_process('touch test/test_neg.txt')
    call_process('java -jar BoostSRL-v1-0.jar -i -test test -model train/models -target hit -aucJarPath . ')
    print state
    raw_input()
    result_file = read_file("results_hit.db")
    if not result_file:
        remove_test_files()
        return False
    result = result_file[0]
    prob = float(result.split(')')[1])
    if prob > acceptance_threshold:
        remove_test_files()
        return "hit"
    else:
        remove_test_files()
        return "stand"

def main():
    state_number = 1
    pos_action = []
    facts,pos,neg = [],[],[]
    max_tolerance = 2
    batch_size = 2
    burn_in_time = 100
    number_of_trajectories = burn_in_time + 10
    if "train" not in listdir(".") or "test" not in listdir("."):
        make_train_and_test_directory()
    for trajectory in range(number_of_trajectories):
        d = Game()
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
                    print action_specification
                else:
                    action_specification = perform_inference_and_choose(state,deepcopy(state_number),random=True)
            state_sequence.append((state_copy,action_specification,deepcopy(state_number)))
            state = d.takeAction(state,action_specification)
            if trajectory > 101:
                print state_copy,action_specification,state
                raw_input()
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
            print Values
            call_process('java -jar BoostSRL-v1-0.jar -l -train train -target hit')
            remove_files()
main()
