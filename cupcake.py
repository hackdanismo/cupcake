# Import the regular expression module from Python.
import re
import sys


# -------------------------
# TOKENS
# -------------------------

TOKEN_REGEX = re.compile(
    r"""
    (?P<NUMBER>\d+(?:\.\d+)?)
    |(?P<STRING>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
    |(?P<FUNCTION>function\b)
    |(?P<RETURN>return\b)
    |(?P<LET>let\b)
    |(?P<IF>if\b)
    |(?P<ELSE>else\b)
    |(?P<WHILE>while\b)
    |(?P<TRY>try\b)
    |(?P<CATCH>catch\b)
    |(?P<TRUE>true\b)
    |(?P<FALSE>false\b)
    |(?P<AND>and\b)
    |(?P<OR>or\b)
    |(?P<NOT>not\b)
    |(?P<IDENTIFIER>[A-Za-z_][A-Za-z0-9_]*)
    |(?P<EQ>==)
    |(?P<NE>!=)
    |(?P<LE><=)
    |(?P<GE>>=)
    |(?P<ASSIGN>=)
    |(?P<LT><)
    |(?P<GT>>)
    |(?P<PLUS>\+)
    |(?P<MINUS>-)
    |(?P<STAR>\*)
    |(?P<SLASH>/)
    |(?P<PERCENT>%)
    |(?P<LPAREN>\()
    |(?P<RPAREN>\))
    |(?P<LBRACE>\{)
    |(?P<RBRACE>\})
    |(?P<LBRACKET>\[)
    |(?P<RBRACKET>\])
    |(?P<COMMA>,)
    |(?P<COLON>:)
    |(?P<SEMICOLON>;)
    |(?P<WHITESPACE>\s+)
    """,
    re.VERBOSE,
)


def tokenize(source):
    tokens = []
    position = 0

    while position < len(source):
        # Block comments use ## ... ##
        if source.startswith("##", position):
            end_position = source.find("##", position + 2)
            if end_position == -1:
                raise SyntaxError("Block comment was not closed with ##")
            position = end_position + 2
            continue

        # Single-line comments use # ... end-of-line
        if source[position] == "#":
            end_position = source.find("\n", position)
            if end_position == -1:
                position = len(source)
            else:
                position = end_position + 1
            continue

        match = TOKEN_REGEX.match(source, position)

        if not match:
            raise SyntaxError(
                f"Unexpected character at position {position}: {source[position]!r}"
            )

        token_type = match.lastgroup
        value = match.group()

        if token_type != "WHITESPACE":
            tokens.append((token_type, value))

        position = match.end()

    tokens.append(("EOF", None))
    return tokens


# -------------------------
# AST NODES
# -------------------------

class Program:
    def __init__(self, statements):
        self.statements = statements


class Block:
    def __init__(self, statements):
        self.statements = statements


class Number:
    def __init__(self, value):
        self.value = value


class String:
    def __init__(self, value):
        self.value = value


class Boolean:
    def __init__(self, value):
        self.value = value


class Array:
    def __init__(self, elements):
        self.elements = elements


class Map:
    def __init__(self, entries):
        self.entries = entries


class Variable:
    def __init__(self, name):
        self.name = name


class Let:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Assign:
    def __init__(self, target, value):
        self.target = target
        self.value = value


class Binary:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class Unary:
    def __init__(self, operator, expression):
        self.operator = operator
        self.expression = expression


class If:
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class While:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class TryCatch:
    def __init__(self, try_block, error_name, catch_block):
        self.try_block = try_block
        self.error_name = error_name
        self.catch_block = catch_block


class Function:
    def __init__(self, name, parameters, body, legacy_expression=False):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.legacy_expression = legacy_expression
        self.closure = None


class Call:
    def __init__(self, callee, arguments):
        self.callee = callee
        self.arguments = arguments


class Return:
    def __init__(self, value):
        self.value = value


class Index:
    def __init__(self, target, index):
        self.target = target
        self.index = index


class ExpressionStatement:
    def __init__(self, expression):
        self.expression = expression


# -------------------------
# PARSER
# -------------------------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        return self.tokens[self.position]

    def previous(self):
        return self.tokens[self.position - 1]

    def check(self, token_type):
        return self.current()[0] == token_type

    def check_next(self, token_type):
        if self.position + 1 >= len(self.tokens):
            return False
        return self.tokens[self.position + 1][0] == token_type

    def match(self, *token_types):
        if self.current()[0] in token_types:
            token = self.current()
            self.position += 1
            return token
        return None

    def expect(self, token_type):
        token = self.match(token_type)
        if token is None:
            actual = self.current()[0]
            raise SyntaxError(f"Expected {token_type}, got {actual}")
        return token

    def parse(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.parse_statement())
        self.expect("EOF")
        return Program(statements)

    def parse_statement(self):
        if self.check("FUNCTION"):
            function = self.parse_function()

            # Legacy expression-body functions use a trailing semicolon.
            if function.legacy_expression:
                self.expect("SEMICOLON")

            # A block-style function may optionally use a semicolon.
            else:
                self.match("SEMICOLON")

            return function

        if self.match("LET"):
            statement = self.parse_let()
            self.expect("SEMICOLON")
            return statement

        if self.match("RETURN"):
            statement = self.parse_return()
            self.expect("SEMICOLON")
            return statement

        if self.match("IF"):
            return self.parse_if()

        if self.match("WHILE"):
            return self.parse_while()

        if self.match("TRY"):
            return self.parse_try_catch()

        expression = self.parse_expression()

        if self.match("ASSIGN"):
            value = self.parse_expression()
            self.expect("SEMICOLON")

            if not isinstance(expression, (Variable, Index)):
                raise SyntaxError("Invalid assignment target")

            return Assign(expression, value)

        self.expect("SEMICOLON")
        return ExpressionStatement(expression)

    def parse_block(self):
        self.expect("LBRACE")
        statements = []

        while not self.check("RBRACE"):
            if self.check("EOF"):
                raise SyntaxError("Expected RBRACE before end of file")
            statements.append(self.parse_statement())

        self.expect("RBRACE")
        return Block(statements)

    def parse_let(self):
        name = self.expect("IDENTIFIER")[1]
        self.expect("ASSIGN")
        value = self.parse_expression()
        return Let(name, value)

    def parse_return(self):
        if self.check("SEMICOLON"):
            return Return(None)
        return Return(self.parse_expression())

    def parse_if(self):
        self.expect("LPAREN")
        condition = self.parse_expression()
        self.expect("RPAREN")
        then_branch = self.parse_block()

        else_branch = None
        if self.match("ELSE"):
            if self.match("IF"):
                else_branch = self.parse_if()
            else:
                else_branch = self.parse_block()

        return If(condition, then_branch, else_branch)

    def parse_while(self):
        self.expect("LPAREN")
        condition = self.parse_expression()
        self.expect("RPAREN")
        body = self.parse_block()
        return While(condition, body)

    def parse_try_catch(self):
        try_block = self.parse_block()

        self.expect("CATCH")
        self.expect("LPAREN")
        error_name = self.expect("IDENTIFIER")[1]
        self.expect("RPAREN")

        catch_block = self.parse_block()

        return TryCatch(try_block, error_name, catch_block)

    def parse_function(self):
        self.expect("FUNCTION")

        name = None

        # A named function has an identifier before its opening parenthesis:
        #
        # function add(a, b) { ... }
        #
        # An anonymous function begins directly with "(":
        #
        # function(a, b) { ... }
        if self.check("IDENTIFIER") and self.check_next("LPAREN"):
            name = self.expect("IDENTIFIER")[1]

        self.expect("LPAREN")

        # Cake supports both the original expression-body syntax:
        #
        # function (2 + 2);
        # function add (2 + 2);
        #
        # and the newer block-body syntax:
        #
        # function add(a, b) { return a + b; }
        #
        # To tell them apart, first look ahead to see whether the contents
        # of (...) form a parameter list AND are immediately followed by {.
        saved_position = self.position
        parameters = []
        parameter_list_is_valid = True

        if not self.check("RPAREN"):
            if not self.check("IDENTIFIER"):
                parameter_list_is_valid = False
            else:
                parameters.append(self.expect("IDENTIFIER")[1])

                while self.match("COMMA"):
                    if not self.check("IDENTIFIER"):
                        parameter_list_is_valid = False
                        break
                    parameters.append(self.expect("IDENTIFIER")[1])

        if parameter_list_is_valid and self.check("RPAREN"):
            self.position += 1

            if self.check("LBRACE"):
                body = self.parse_block()
                return Function(name, parameters, body, legacy_expression=False)

        # It was not a parameter-list + block function, so rewind and parse
        # everything inside (...) as the original Cake expression body.
        self.position = saved_position
        body = self.parse_expression()
        self.expect("RPAREN")
        return Function(name, [], body, legacy_expression=True)

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        expression = self.parse_and()
        while self.match("OR"):
            expression = Binary(expression, "OR", self.parse_and())
        return expression

    def parse_and(self):
        expression = self.parse_equality()
        while self.match("AND"):
            expression = Binary(expression, "AND", self.parse_equality())
        return expression

    def parse_equality(self):
        expression = self.parse_comparison()

        while self.current()[0] in ("EQ", "NE"):
            operator = self.current()[0]
            self.position += 1
            expression = Binary(expression, operator, self.parse_comparison())

        return expression

    def parse_comparison(self):
        expression = self.parse_addition()

        while self.current()[0] in ("LT", "LE", "GT", "GE"):
            operator = self.current()[0]
            self.position += 1
            expression = Binary(expression, operator, self.parse_addition())

        return expression

    def parse_addition(self):
        expression = self.parse_multiplication()

        while self.current()[0] in ("PLUS", "MINUS"):
            operator = self.current()[0]
            self.position += 1
            expression = Binary(expression, operator, self.parse_multiplication())

        return expression

    def parse_multiplication(self):
        expression = self.parse_unary()

        while self.current()[0] in ("STAR", "SLASH", "PERCENT"):
            operator = self.current()[0]
            self.position += 1
            expression = Binary(expression, operator, self.parse_unary())

        return expression

    def parse_unary(self):
        if self.current()[0] in ("MINUS", "NOT"):
            operator = self.current()[0]
            self.position += 1
            return Unary(operator, self.parse_unary())

        return self.parse_postfix()

    def parse_postfix(self):
        expression = self.parse_primary()

        while True:
            if self.match("LPAREN"):
                arguments = []

                if not self.check("RPAREN"):
                    arguments.append(self.parse_expression())
                    while self.match("COMMA"):
                        arguments.append(self.parse_expression())

                self.expect("RPAREN")
                expression = Call(expression, arguments)
                continue

            if self.match("LBRACKET"):
                index = self.parse_expression()
                self.expect("RBRACKET")
                expression = Index(expression, index)
                continue

            break

        return expression

    def parse_primary(self):
        token_type, value = self.current()

        if token_type == "NUMBER":
            self.position += 1
            if "." in value:
                return Number(float(value))
            return Number(int(value))

        if token_type == "STRING":
            self.position += 1
            # Decode common escaped characters such as \n and \".
            decoded = bytes(value[1:-1], "utf-8").decode("unicode_escape")
            return String(decoded)

        if token_type == "TRUE":
            self.position += 1
            return Boolean(True)

        if token_type == "FALSE":
            self.position += 1
            return Boolean(False)

        if token_type == "IDENTIFIER":
            self.position += 1
            return Variable(value)

        if token_type == "FUNCTION":
            # Anonymous modern function expression.
            return self.parse_function()

        if token_type == "LPAREN":
            self.position += 1
            expression = self.parse_expression()
            self.expect("RPAREN")
            return expression

        if token_type == "LBRACKET":
            return self.parse_array()

        if token_type == "LBRACE":
            return self.parse_map()

        raise SyntaxError(f"Unexpected token: {token_type}")

    def parse_array(self):
        self.expect("LBRACKET")
        elements = []

        if not self.check("RBRACKET"):
            elements.append(self.parse_expression())
            while self.match("COMMA"):
                elements.append(self.parse_expression())

        self.expect("RBRACKET")
        return Array(elements)

    def parse_map(self):
        self.expect("LBRACE")
        entries = []

        if not self.check("RBRACE"):
            while True:
                if self.check("STRING"):
                    key = self.parse_primary()
                elif self.check("IDENTIFIER"):
                    key = String(self.expect("IDENTIFIER")[1])
                else:
                    raise SyntaxError("Map keys must be strings or identifiers")

                self.expect("COLON")
                value = self.parse_expression()
                entries.append((key, value))

                if not self.match("COMMA"):
                    break

        self.expect("RBRACE")
        return Map(entries)


# -------------------------
# RUNTIME
# -------------------------

class CakeRuntimeError(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name)

        raise CakeRuntimeError(f"Variable '{name}' is not defined")

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return value

        if self.parent is not None:
            return self.parent.assign(name, value)

        raise CakeRuntimeError(f"Variable '{name}' is not defined")


class CakeFunction:
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure

    def call(self, interpreter, arguments):
        if len(arguments) != len(self.declaration.parameters):
            raise CakeRuntimeError(
                f"Function '{self.declaration.name or '<anonymous>'}' expected "
                f"{len(self.declaration.parameters)} argument(s), got {len(arguments)}"
            )

        environment = Environment(self.closure)

        for name, value in zip(self.declaration.parameters, arguments):
            environment.define(name, value)

        try:
            if self.declaration.legacy_expression:
                return interpreter.evaluate(self.declaration.body, environment)

            interpreter.evaluate(self.declaration.body, environment)

        except ReturnSignal as signal:
            return signal.value

        return None


class BuiltinFunction:
    def __init__(self, name, function, arity=None):
        self.name = name
        self.function = function
        self.arity = arity

    def call(self, interpreter, arguments):
        if self.arity is not None and len(arguments) != self.arity:
            raise CakeRuntimeError(
                f"{self.name} expected {self.arity} argument(s), got {len(arguments)}"
            )

        try:
            return self.function(*arguments)
        except CakeRuntimeError:
            raise
        except Exception as error:
            raise CakeRuntimeError(f"{self.name}: {error}") from error


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.install_builtins()

    def install_builtins(self):
        self.globals.define("print", BuiltinFunction("print", self.builtin_print))
        self.globals.define("length", BuiltinFunction("length", self.builtin_length, 1))
        self.globals.define("charAt", BuiltinFunction("charAt", self.builtin_char_at, 2))
        self.globals.define("substring", BuiltinFunction("substring", self.builtin_substring, 3))
        self.globals.define("readFile", BuiltinFunction("readFile", self.builtin_read_file, 1))
        self.globals.define("append", BuiltinFunction("append", self.builtin_append, 2))
        self.globals.define("keys", BuiltinFunction("keys", self.builtin_keys, 1))
        self.globals.define("typeOf", BuiltinFunction("typeOf", self.builtin_type_of, 1))
        self.globals.define("toString", BuiltinFunction("toString", self.builtin_to_string, 1))
        self.globals.define("toNumber", BuiltinFunction("toNumber", self.builtin_to_number, 1))
        self.globals.define("error", BuiltinFunction("error", self.builtin_error, 1))

    def builtin_print(self, *values):
        print(*[self.stringify(value) for value in values])
        return None

    def builtin_length(self, value):
        if not isinstance(value, (str, list, dict)):
            raise CakeRuntimeError("length expects a string, array, or map")
        return len(value)

    def builtin_char_at(self, value, index):
        if not isinstance(value, str):
            raise CakeRuntimeError("charAt expects a string")
        if not isinstance(index, int):
            raise CakeRuntimeError("charAt index must be an integer")
        try:
            return value[index]
        except IndexError:
            raise CakeRuntimeError("charAt index is out of range")

    def builtin_substring(self, value, start, end):
        if not isinstance(value, str):
            raise CakeRuntimeError("substring expects a string")
        if not isinstance(start, int) or not isinstance(end, int):
            raise CakeRuntimeError("substring indexes must be integers")
        return value[start:end]

    def builtin_read_file(self, filename):
        if not isinstance(filename, str):
            raise CakeRuntimeError("readFile expects a string filename")
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return file.read()
        except OSError as error:
            raise CakeRuntimeError(f"Could not read file '{filename}': {error}")

    def builtin_append(self, array, value):
        if not isinstance(array, list):
            raise CakeRuntimeError("append expects an array as its first argument")
        array.append(value)
        return array

    def builtin_keys(self, mapping):
        if not isinstance(mapping, dict):
            raise CakeRuntimeError("keys expects a map")
        return list(mapping.keys())

    def builtin_type_of(self, value):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "map"
        if isinstance(value, (CakeFunction, BuiltinFunction)):
            return "function"
        return type(value).__name__

    def builtin_to_string(self, value):
        return self.stringify(value)

    def builtin_to_number(self, value):
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                number = float(value)
                return int(number) if number.is_integer() else number
            except ValueError:
                raise CakeRuntimeError(f"Cannot convert {value!r} to a number")
        raise CakeRuntimeError("toNumber expects a string, number, or boolean")

    def builtin_error(self, message):
        raise CakeRuntimeError(str(message))

    def stringify(self, value):
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        if isinstance(value, list):
            return "[" + ", ".join(self.stringify(item) for item in value) + "]"
        if isinstance(value, dict):
            return "{" + ", ".join(
                f"{self.stringify(key)}: {self.stringify(item)}"
                for key, item in value.items()
            ) + "}"
        return str(value)

    def is_truthy(self, value):
        return bool(value)

    def evaluate(self, node, environment=None):
        if environment is None:
            environment = self.globals

        if isinstance(node, Program):
            result = None
            for statement in node.statements:
                value = self.evaluate(statement, environment)
                if value is not None:
                    result = value
            return result

        if isinstance(node, Block):
            result = None
            for statement in node.statements:
                value = self.evaluate(statement, environment)
                if value is not None:
                    result = value
            return result

        if isinstance(node, ExpressionStatement):
            return self.evaluate(node.expression, environment)

        if isinstance(node, Number):
            return node.value

        if isinstance(node, String):
            return node.value

        if isinstance(node, Boolean):
            return node.value

        if isinstance(node, Array):
            return [self.evaluate(element, environment) for element in node.elements]

        if isinstance(node, Map):
            return {
                self.evaluate(key, environment): self.evaluate(value, environment)
                for key, value in node.entries
            }

        if isinstance(node, Variable):
            return environment.get(node.name)

        if isinstance(node, Let):
            value = self.evaluate(node.value, environment)
            environment.define(node.name, value)
            return None

        if isinstance(node, Assign):
            value = self.evaluate(node.value, environment)

            if isinstance(node.target, Variable):
                return environment.assign(node.target.name, value)

            if isinstance(node.target, Index):
                target = self.evaluate(node.target.target, environment)
                index = self.evaluate(node.target.index, environment)

                try:
                    target[index] = value
                    return value
                except (TypeError, IndexError, KeyError) as error:
                    raise CakeRuntimeError(f"Invalid indexed assignment: {error}")

        if isinstance(node, Unary):
            value = self.evaluate(node.expression, environment)

            if node.operator == "MINUS":
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise CakeRuntimeError("Unary - expects a number")
                return -value

            if node.operator == "NOT":
                return not self.is_truthy(value)

        if isinstance(node, Binary):
            if node.operator == "AND":
                left = self.evaluate(node.left, environment)
                if not self.is_truthy(left):
                    return left
                return self.evaluate(node.right, environment)

            if node.operator == "OR":
                left = self.evaluate(node.left, environment)
                if self.is_truthy(left):
                    return left
                return self.evaluate(node.right, environment)

            left = self.evaluate(node.left, environment)
            right = self.evaluate(node.right, environment)

            if node.operator == "PLUS":
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if (
                    isinstance(left, (int, float))
                    and not isinstance(left, bool)
                    and isinstance(right, (int, float))
                    and not isinstance(right, bool)
                ):
                    return left + right
                if isinstance(left, list) and isinstance(right, list):
                    return left + right
                raise CakeRuntimeError("+ expects two numbers, two strings, or two arrays")

            if node.operator == "MINUS":
                return left - right

            if node.operator == "STAR":
                return left * right

            if node.operator == "SLASH":
                if right == 0:
                    raise CakeRuntimeError("Division by zero")
                return left / right

            if node.operator == "PERCENT":
                if right == 0:
                    raise CakeRuntimeError("Modulo by zero")
                return left % right

            if node.operator == "EQ":
                return left == right

            if node.operator == "NE":
                return left != right

            if node.operator == "LT":
                return left < right

            if node.operator == "LE":
                return left <= right

            if node.operator == "GT":
                return left > right

            if node.operator == "GE":
                return left >= right

        if isinstance(node, If):
            if self.is_truthy(self.evaluate(node.condition, environment)):
                return self.evaluate(node.then_branch, Environment(environment))

            if node.else_branch is not None:
                return self.evaluate(node.else_branch, Environment(environment))

            return None

        if isinstance(node, While):
            result = None

            while self.is_truthy(self.evaluate(node.condition, environment)):
                value = self.evaluate(node.body, Environment(environment))
                if value is not None:
                    result = value

            return result

        if isinstance(node, TryCatch):
            try:
                return self.evaluate(node.try_block, Environment(environment))
            except CakeRuntimeError as error:
                catch_environment = Environment(environment)
                catch_environment.define(node.error_name, str(error))
                return self.evaluate(node.catch_block, catch_environment)

        if isinstance(node, Function):
            function = CakeFunction(node, environment)
            node.closure = environment

            # Anonymous legacy functions execute immediately, preserving
            # the original Cupcake behavior:
            #
            # function (2 + 2);
            #
            # returns 4.
            if node.name is None and node.legacy_expression:
                return function.call(self, [])

            # Anonymous modern functions are values and can be assigned:
            #
            # let add = function(a, b) { return a + b; };
            if node.name is None:
                return function

            environment.define(node.name, function)
            return None

        if isinstance(node, Call):
            callee = self.evaluate(node.callee, environment)
            arguments = [
                self.evaluate(argument, environment)
                for argument in node.arguments
            ]

            if not isinstance(callee, (CakeFunction, BuiltinFunction)):
                raise CakeRuntimeError("Attempted to call a value that is not a function")

            return callee.call(self, arguments)

        if isinstance(node, Return):
            value = None
            if node.value is not None:
                value = self.evaluate(node.value, environment)
            raise ReturnSignal(value)

        if isinstance(node, Index):
            target = self.evaluate(node.target, environment)
            index = self.evaluate(node.index, environment)

            if isinstance(target, (list, str)):
                if not isinstance(index, int):
                    raise CakeRuntimeError("Array/string index must be an integer")
                try:
                    return target[index]
                except IndexError:
                    raise CakeRuntimeError("Index is out of range")

            if isinstance(target, dict):
                if index not in target:
                    raise CakeRuntimeError(f"Map key {index!r} does not exist")
                return target[index]

            raise CakeRuntimeError("Only arrays, strings, and maps can be indexed")

        raise CakeRuntimeError(
            f"Cannot evaluate node: {type(node).__name__}"
        )


# -------------------------
# RUN SOURCE CODE
# -------------------------

def run(source):
    tokens = tokenize(source)
    parser = Parser(tokens)
    tree = parser.parse()
    interpreter = Interpreter()
    return interpreter.evaluate(tree)


# -------------------------
# RUN EXTERNAL SOURCE FILES
# Run an external source file with the file extension of: .cake
# -------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 cupcake.py <file.cake>")
        sys.exit(1)

    filename = sys.argv[1]

    if not filename.endswith(".cake"):
        print("Error: Cupcake source files must use the .cake extension.")
        sys.exit(1)

    try:
        with open(filename, "r", encoding="utf-8") as file:
            source = file.read()

        result = run(source)

        if result is not None:
            print(Interpreter().stringify(result))

    except (SyntaxError, CakeRuntimeError) as error:
        print(f"Cupcake error: {error}")
        sys.exit(1)

    except OSError as error:
        print(f"Cupcake file error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
