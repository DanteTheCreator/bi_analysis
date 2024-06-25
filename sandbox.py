import pandas
import matplotlib.pyplot as plt
import seaborn

class MinimalSandbox:
    def __init__(self):
        self._allowed_imports = {
            'pandas': pandas,
            'matplotlib.pyplot': plt,
            'seaborn': seaborn
        }

    def allow_import(self, module_name):
        try:
            self._allowed_imports[module_name] = __import__(module_name)
        except ImportError:
            pass

    def execute(self, code):
        restricted_globals = {"__builtins__": {}}
        restricted_globals.update(self._allowed_imports)

        try:
            exec(compile(code, '<string>', 'exec'), restricted_globals)
        except SyntaxError as e:
            return f"Syntax error in code: {e}"

        return restricted_globals

# * Example Usage 
# sandbox = MinimalSandbox()
# sandbox.allow_import('math')
# result = sandbox.execute('result = math.sqrt(16)')
# print(result['result'])
