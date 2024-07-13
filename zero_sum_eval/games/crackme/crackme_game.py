#file: crackme.py
import pyyaml
import ast
import random
import concurrent.futures
from game_manager import GameManager
from game_state import GameState



class CrackMeGame(GameState):
    '''
    This is a two player game where one player creates an obfoscation program,
    and another attempts to reverse it.

    In each round:
        1. The environment is initilized with a key and a base program.
        2. The first player inserts operations into the base program to obfoscate the key.
        3. If the new program is valid, the second player annotates the new program ( with obfoscated key )
        4. The second player creates a new program which outputs the original key given the obfoscated key.
        5. If the second player suceeds, the new program may become the base program to continue the game.

    The roles for this game are:
        DefenderObfoscateKey
        AttackerAnnotateTarget
        AttackerReverseEngineer

    The environment for this game is:
        base_program: a program which takes an input and returns an output
    
    
    key: a randomly generated number
    obfoscated_key: the result of base_program(key)

    '''
    def __init__(self, roles=None, environment=None, context=None, key=None):
        super().__init__()
        self.environment = environment if environment is not None else "" 
        self.roles = roles if roles is not None else self.get_next_roles()
        self.context = context if context is not None else {"history": [], "message": None}
        self.key = key if key is not None else random.random() 

    def initilize(self, environment, context=None ,roles=None, key=None):
        return CrackMeGame(
            roles=roles,
            environment=environment,
            context=context,
            key=key
        )

    def update_game(self, move):
        new_context = self.context.copy()
        new_environment = self.environment.copy() 
        #TODO: verify that self.roles[0] is the current move 

        if self.roles[0] == "AttackerAnnotateTarget":
            new_context['message'] = None          
            new_context.get('annotation','').append(f"\n {move}")

        else:
            key_in = self.key if self.roles[0] is "DefenderObfoscateKey" else self.context['obfoscated_key']
            success, result = self.execute_and_verify(move, key_in)
            if success: 
                if self.roles[0] == "DefenderObfoscateKey":
                    new_context['obfoscated_key'] = result
                    new_context['annotation_target'] = self.environment
                    new_context['annotation'] = None
                    new_context['message'] = None
                     
                if self.roles[0] == "AttackerReverseEngineer":
                    if self.key == result:
                        #ATTACKER WINS!! reset the game here
                        # update history with a tuple (defender_code,annotation,attacker_code)
                        new_context['history'].append((new_context['annotation_target'],new_context['annotation'], self.environment))
                        new_context['message'] = None
                        return self.initialize(
                            environment=new_environment,
                            context=new_context
                        )
                          
                    else:
                        new_context['message'] = f"result {result} is incorrect. ACCESS DENIED"        
            else: 
                new_context['message'] = result # this will return error from verify and execute 

        return self.initialize(
            roles=self.roles,
            environment=new_environment,
            context=new_context,
            key=self.key #maybe change?
        )


    def query_game(self):
        #TODO: change the message and context for each role so info does not leak 
    
        new_context = self.context.copy()
        new_roles = self.get_next_roles()
        msg = self.validate_game()
        new_context['message'] = msg if msg is not None else f"You will move as {new_roles[0]}" 
        # add specific 
        return self.initialize(
            environment=self.environment,
            context=new_context,
            roles=new_roles
        )

    def validate_game(self):
        ''' 
            TODO:
            put win conditions here depending on current message etc. 
            for now just have failure of either exceeding turn # mean end
        '''
        return self.context['message']



        
        
    def execute_and_verify(code_str, key_in, timeout=1):
    '''
        this function can be overwritten/overloaded to change/expand the representation(s) 
        and method(s) of exectuion
    '''
    code_str = f"{code_str}"

        def validate_nodes(tree):
            allowed_nodes = {
                ast.Module, ast.Expr, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load, ast.Add,
                ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.UAdd, ast.USub, ast.Assign,
                ast.Name, ast.Constant, ast.For, ast.While, ast.If, ast.Compare, ast.Lt, ast.LtE,
                ast.Gt, ast.GtE, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Break, ast.Continue,
                ast.Pass
            }
            
            for node in ast.walk(tree):
                if type(node) not in allowed_nodes:
                    raise ValueError(f"Operation {type(node).__name__} is not allowed")
        def restricted_exec(code_str, input_value):

            # this may need to be modified...
            allowed_builtins = {'__builtins__': {}}
            restricted_globals = {'__builtins__': allowed_builtins}
            restricted_locals = {'input_value': input_value}

            # wrapper code to capture the output
            #TODO: fix this wrapper to work with above restrictions
            wrapper_code = f"""
    result = None
    def wrapper():
        global result = {key_in}
        {code_str}
        return result

    result = wrapper()
    """
        try:
            tree = ast.parse(move)
            validate_nodes(tree)
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}, column {e.offset}: {e.text}"      
        except Exception as e
            new_context['message'] = f"Error during parsing: {str(e)}"

        with concurrent.futures.ThreadPoolExecutor() as executor:

            # make sure this works, maybe use ast.compile() 
            future = executor.submit(restricted_exec, wrapper_code, key_in)
            try:
                result, error = future.result(timeout=timeout)
                if error:
                    return False, error
                else: 
                    return True, result
            except concurrent.futures.TimeoutError:
                return False, "Timeout occurred"

            except Exception as e
                # for now dont leak error info to llm
                return False, f"Error during execution"
                # maybe use logger here?

    #TODO: impliment export later
