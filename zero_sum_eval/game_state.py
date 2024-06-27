'''
Abstract class to define minumum API to represent a game
'''
import yaml
from abc import ABC, abstractmethod


class GameState(ABC):
    def __init__(self):
       roles = [] # a queue of players 
       environment = {} 
       context = {}

    @abstractmethod
    def initialize(self, roles, context, environment):
        self.roles = roles
        self.context = context
        self.environment = environment 

    @abstractmethod
    def update_game(self):
        '''
            returns: 
                - if the move is valid: a new gameState with context and environment updated to match new move and roles ordered in the updated order of play 
                - if the move is invalid: a gamestate that is the same as the move, but with an explination added in context for why it is invalid 
                - if a win condition is met: a gamestate detailing the game thus far, with the condition added  
        '''
        pass

    @abstractmethod
    def query_game(self):
        '''
            returns a game_state relevant to the next move
                - includes list of roles that player should act for  
                - includes a message with instructions for the move
                - environment should be the current state
                - anything else may be added since it will be passed directly to the player
        '''
        pass

    @abstractmethod
    def validate_game(self):
        '''
            to validate a state of the game
            requires: a gameState
            returns: None if valid move and game continues, anything else if invalid move or finished 
        '''
        pass
    
    @abstractmethod
    def export(self):
        ''' 
            returns a text based representation of the gameSatate object
            default is yaml 
        ''' 
        return yaml.dump(self.__dict__)




