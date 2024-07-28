#file: crackme.py
#TODO: figure out multi line inputs
import yaml
import ast
import random
import concurrent.futures
from zero_sum_eval.game_manager import GameManager
from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY


@GAME_REGISTRY.register("crackme")
class CrackMeGame(GameState):
    '''
    This is a two player game where one player creates an obfuscation program,
    and another attempts to reverse it.

    In each round:
        1. The environment is initialized with a key and a base program.
        2. The first player inserts operations into the base program to obfuscate the key.
        3. If the new program is valid, the second player annotates the new program ( with obfuscated key )
        4. The second player creates a new program which outputs the original key given the obfuscated key.
        5. If the second player succeeds, the new program may become the base program to continue the game.

    The roles for this game are:
        DefenderobfuscateKey
        AttackerAnnotateTarget
        AttackerReverseEngineer

    The environment for this game is:
        code: a program which takes an input and returns an output

    key: a randomly generated number (not stored) 
    obfuscated_key: the result of base_program(key)

    '''
    def __init__(self, roles=None, environment=None, context=None):
        super().__init__()
        self.environment = environment if environment is not None else {"code":""}
        self.context = context if context is not None else {"annotation": "", "message": None}
        self.roles = roles if roles is not None else self.get_next_roles()

    def initialize(self, environment=None, context=None ,roles=None):
        return CrackMeGame(
            roles=roles,
            environment=environment,
            context=context,
        )

    def update_game(self, move):
        new_context = self.context.copy()
        new_environment = self.environment.copy()

        if self.roles[0] == "AttackerAnnotateTarget":
            new_context['message'] = None
            new_context['annotation'] = new_context.get('annotation',"") + f"\n {move}"


        else:
            key_in = random.randint(1000,100000) if self.roles[0] == "DefenderobfuscateKey" else self.context['obfuscated_key']
            success, result = self.execute_and_verify(move, key_in)
            if success:
                if self.roles[0] == "DefenderobfuscateKey":
                    new_environment['code'] = move
                    new_context['obfuscated_key'] = result
                #    new_environment['annotation_target'] = new_environment['code']
                    new_context['annotation'] = '' 
                    new_context['message'] = None

                if self.roles[0] == "AttackerReverseEngineer":
                    
                    # verify by checking if original_code( deobfuscation_code( obfuscated_key ) ) == obfuscated_key
                    _ , orig_result = self.execute_and_verify(self.environment['code'], result)
                    # this should be verified but it is possible to have an error if the gamestate is not correct 
                    #TODO: look into ways to make this more efficent... maybe  

                    if orig_result == new_context['obfuscated_key']:
                        #ATTACKER WINS!! 
                        # update history with a tuple (defender_code,annotation,attacker_code)
                        history = new_context.get('history', [])
                        new_environment['code'] = move
                        history.append((self.environment['code'],new_context['annotation'],new_environment['code']))
                        new_context.update({'history': history})

                        #reset 
                        new_context['obfuscated_key'] = None 
                        new_context['message'] = "Attacker Success" 

                        # move this to environment incase 
                        #new_environment.update({'status':"Attacker Success"})
                        return self.initialize(
                            environment=new_environment,
                            context=new_context
                        )

                    else:
                        new_context['message'] = f"result {result} is incorrect. ACCESS DENIED"
            else:
                new_context['message'] = result # this will return error from verify_and_execute

        return self.initialize(
            roles=self.roles,
            environment=new_environment,
            context=new_context,
        )


    def query_game(self):
        instructions = {
            "DefenderobfuscateKey": "Implement a code snippit to scramble and obfuscate a given input to prevent reverse engineering.",
            "AttackerReverseEngineer": "Reverse the provided code snippit such that reversed_code( code( key ) ) == key == reversed_code( obfuscated_key ) ",
            "AttackerAnnotateTarget": "Describe the target code to assist in reverse engineering later"
        }

        new_context = self.context.copy()
        new_roles = self.get_next_roles()
        msg = self.validate_game()
        new_context['message'] = msg if msg is not None else f"You will move as {new_roles[0]}.\n GOAL: {instructions[new_roles[0]]}"


        return self.initialize(
            environment=self.environment,
            context=new_context,
            roles=[new_roles[0]],
        )

    def validate_game(self):
        '''
            can put win conditions here relating to current environment, if nessiscary  
            attacker success is the only win case (game can also end in failure)
        '''
        #do not need right now
#        if self.environment.get('status',None) != None:
#            return self.environment['status']
        return self.context['message']


    def get_next_roles(self):
        #verify these are correct
        #if self.context.get('annotation_target',None) == None:
        if self.context.get('obfuscated_key',None) == None:
            return ["DefenderobfuscateKey","AttackerAnnotateTarget","AttackerReverseEngineer"]
        elif self.context.get('annotation',"") != "":
            return ["AttackerReverseEngineer","DefenderobfuscateKey","AttackerAnnotateTarget"]
        else:
            return ["AttackerAnnotateTarget","AttackerReverseEngineer","DefenderobfuscateKey"]


    def export(self):
        return yaml.dump(self.__dict__)
    

    def execute_and_verify(self, code_str, input_value, timeout = 1):

       # this function can be overwritten/overloaded to change/expand the representation(s) and method(s) of exectuion
       
        def validate_nodes(tree):
            allowed_nodes = {
                ast.Module, ast.Expr, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load, ast.Add,
                ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.UAdd, ast.USub, ast.Assign,
                ast.Name, ast.Constant, ast.For, ast.While, ast.If, ast.Compare, ast.Lt, ast.LtE,
                ast.Gt, ast.GtE, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Break, ast.Continue,
                ast.Pass, ast.Store, ast.AugAssign, ast.FloorDiv, ast.Call
            }
            for node in ast.walk(tree):
                if type(node) not in allowed_nodes:
                    raise ValueError(f"Operation {type(node).__name__} is not allowed")

        def restricted_exec(code_str, input_value):

            # These are the functions that can be called 
            restricted_globals = {
                '__builtins__': {
                    'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
                    'int': int, 'float': float, 'len': len, 'list': list, 'max': max,
                    'min': min, 'pow': pow, 'range': range, 'round': round, 'sum': sum, 'int': int
                }
            }
            restricted_locals = {'input_value': input_value, 'result': input_value}

            wrapper_code = f"""
def wrapper(input):
    res=input
    {code_str}
    return res

input_hidden = {input_value}
result = wrapper(input_hidden)
    """
            exec(wrapper_code, restricted_globals, restricted_locals)
            return restricted_locals['result']

        try:
            if not isinstance(code_str, (str, bytes, ast.AST)):
                raise TypeError(f"code_str must be a string, bytes or AST object, not {type(code_str)}")
            
            tree = ast.parse(code_str)
            validate_nodes(tree)
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}, column {e.offset}: {e.text}"
        except Exception as e:
            return False, f"Error during parsing: {str(e)}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(restricted_exec, code_str, input_value)
            try:
                result = future.result(timeout=timeout)
                return True, result
            except concurrent.futures.TimeoutError:
                return False, "Timeout occurred"
            except Exception as e:
                # for now dont leak error details to llm
                return False, f"Error during execution: {type(e).__name__}"

if __name__ == "__main__":
    '''
    example with human player: 
        for defender input: res=input**2
        some correct inputs for attacker:
            res=int(input**1/2)
            res=(input**(1/2) - ((input**(1/2)) % 1)) // 1
    '''
    from zero_sum_eval.player import HumanPlayer, Player
    config = {
        "game": {
            "name": "crackme_challenge",
                "args": {
                    "win_conditions": ["Attacker Success"],
                    "max_rounds": 10,
                    "players": [{"id":"defender", "role":"DefenderobfuscateKey"},
                                {"id":"attacker", "role":"AttackerAnnotateTarget"},
                                {"id":"attacker", "role":"AttackerReverseEngineer"}],

                    "challenges": [
                    {
                        "environment": None
                    },
                ],
            },
        }
    }

    game_manager = GameManager(config)
    for player_config in config["game"]["args"]["players"]:
        player = HumanPlayer(**player_config)
        
        player.max_tries = 2
        game_manager.register_player(player)

    game_state = CrackMeGame().initialize(None)
    result = game_manager.do_eval(game_state)
    
    print(result.query_game().export()) 


