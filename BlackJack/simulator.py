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

d = Game()
