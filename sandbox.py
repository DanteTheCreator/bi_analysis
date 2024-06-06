class MinimalSandbox:
    def __init__(self):
        self._allowed_imports = {}

    def allow_import(self, module_name):
        try:
            self._allowed_imports[module_name] = __import__(module_name)
        except ImportError:
            pass

    def execute(self, code):
        restricted_globals = {"__builtins__": {}}
        restricted_globals.update(self._allowed_imports)

        exec(compile(code, '<string>', 'exec'), restricted_globals)

        return restricted_globals

# Example Usage
sandbox = MinimalSandbox()
sandbox.allow_import('math')
result = sandbox.execute('result = math.sqrt(16)')
print(result['result'])
