# Impprt the regular expression module from Python.
import re

TOKEN_REGEX = re.compile(
    r"""
    # Match the exact word "function".
    # Prevent words such as "functionality" being used and being mistaken for the "function" keyword.
    (?P<FUNCTION>function\b)
    # Match the + operator, escaped using \+ because + has a special meaning in regex.
    |(?P<PLUS>\+)
    # Match the - operator.
    |(?P<MINUS>-)
    # Match the * operator, escaped using \* because * has a special meaning in regex.
    |(?P<STAR>\*)
    # Match the / operator.
    |(?P<SLASH>/)
    # Match an opening parenthesis, escaped using \( because ( has a special meaning in regex.
    |(?P<LPAREN>\()
    # Match a closing parenthesis.
    |(?P<RPAREN>\))
    # Match a semicolon.
    |(?P<SEMICOLON>;)
    # Allow numbers including decimal points to give this pattern a token name NUMBER.
    |(?P<NUMBER>\d+(?:\.\d+)?)
    # Match whitespace, \s means a whitespace character, + means one or more.
    # This includes: spaces, tabs and new lines.
    |(?P<WHITESPACE>\s+)
    """,
    # Allows us to write regular expressions over multiple lines including comments and whitespace.
    re.VERBOSE,
)

# Define a function called tokenize. It accepts source code as a string.
def tokenize(source):
    # Create an empty list where each token will be added that is discovered.
    tokens = []
    # Start reading the source code at character position 0.
    # In a function, character position 0 would be: "f" in "function (2 + 2);".
    position = 0

    # Keep looping whilst there are characters in the source code left to examine
    # Whilst position is less than the total source length.
    while position < len(source):
        # Try to match one of the token patterns starting at the current character position.
        # TOKEN_REGEX contains all of the patterns defined above.
        match = TOKEN_REGEX.match(source, position)

        # If nothing matches, the language does not recognise the character at the current position, run this:
        if not match:
            # Stop the program and report a syntax error.
            raise SyntaxError(
                f"Unexpected character: {source[position]}"
            )
        # Find out which named regex group matched e.g. "function" -> FUNCTION, "2" -> NUMBER
        token_type = match.lastgroup
        # Get the actual text that was matched e.g. token_type = "NUMBER" value = "2"
        value = match.group()

        # Whitespace not normally needed after tokenization.
        # Only add a token if it is NOT whitespace.
        if token_type != "WHITESPACE":
            # Add a tuple containing:
            # 1. The token type
            # 2. The original text
            # Example: ("NUMBER", "2")
            tokens.append((token_type, value))

        # Move the current position forward to the end of the text that was just matched.
        position = match.end()
    
    # Once all the source code has been read, add a special EOF (End of File) token.
    # This tells the parser that there are no more tokens.
    tokens.append(("EOF", None))

    # Return the complete list of tokens.
    return tokens

# -------------------------
# AST NODES
#
# Abstract Syntax Tree
# Is a structured representation of the code.
# For example: function (2 + 2); can become:
#
# Function
# └── Binary
#     ├── Number(2)
#     ├── PLUS
#     └── Number(2)
#
# These classes define the different kinds of nodes that can appear inside that tree.
# -------------------------

# Create a Number node.
# This represents a number in the source code.
# For example: 2 becomes: Number(2)
class Number:
    # __init__ runs when a new Number object is created.
    def __init__(self, value):
        # Store the actual numeric value.
        # Example: Number(2) - self.value will contain: 2
        self.value = value

# Create a Binary node.
# "Binary" means an operation involving two sides.
# For example: 2 + 2 has:
# left: = 2
# operator = +
# right = 2
# The AST representation becomes:
#
# Binary
# ├── Number(2)
# ├── PLUS
# └── Number(2)
class Binary:
    # Create a new Binary node.
    def __init__(self, left, operator, right):
        # Store the expression on the left side. 
        # For 2 + 3, this would represent: 2
        self.left = left
        # Store the operator.
        # For 2 + 3, this would contain: "PLUS"
        self.operator = operator
        # Store the expression on the right side.
        # For 2 + 3, this would represent: 3
        self.right = right

# Create a Function node.
# This represents the language syntax: function (...)
# For example: function (2 + 2), becomes:
#
# Function
# └── Binary
#     ├── Number(2)
#     ├── PLUS
#     └── Number(2)
class Function:
    # Create a new Function node.
    def __init__(self, body):
        # Store the expression inside the function.
        # For: function (2 + 2), body will contain the AST for: 2 + 2
        self.body = body

# -------------------------
# PARSER
#
# The parser receives the tokens produced by the tokenizer.
# The tokens are then turned into the AST defined above.
#
# For example:
#
# Tokenizer output:
#
# FUNCTION
# LPAREN
# NUMBER
# PLUS
# NUMBER
# RPAREN
# SEMICOLON
# EOF
#
# becomes:
#
# Function
# └── Binary
#     ├── Number(2)
#     ├── PLUS
#     └── Number(2)
# -------------------------

class Parser:
    # Create a parser.
    # Tokens shoukd be in the list produced by tokenize().
    def __init__(self, tokens):
        # Store the complete token list.
        self.tokens = tokens
        # Start reading at the first token.
        # Position 0 means: tokens[0].
        self.position = 0

    # Return the token the parser is currently looking at.
    def current(self):
        # Use self.position as the index into the token list.
        return self.tokens[self.position]

    # Require a specific token type.
    # For example: self.expect("FUNCTION") means: "The next token must be FUNCTION.".
    def expect(self, token_type):
        # Get the current token.
        token = self.current()
        # A token looks something like: ("NUMBER", "2")
        # token[0] is the token type: "NUMBER".
        # token[1] is its original text: "2".
        # Check whether the current token has the expected type.
        if token[0] != token_type:
            # If it does not match, stop parsing and report an error.
            # Example: Expected RPAREN, got NUMBER
            raise SyntaxError(
                f"Expected {token_type}, got {token[0]}"
            )
        
        # Move forward to the next token.
        self.position += 1
        # Return the token that was successfully consumed.
        return token

    # Parse the entire program.
    def parse(self):
        # At the moment, the language expects the program to contain exactly one function.
        # So begin by parsing that function.
        function = self.parse_function()
        # After the function, require the semicolon to be added to the end.
        # Example: function (2 + 2);
        self.expect("SEMICOLON")
        # Then, require the EOF token.
        # This makes sure that there is nothing unexpected after the program.
        self.expect("EOF")
        # Return the complete AST.
        return function

    # Parse a function expression.
    # Expected syntax: function (...)
    def parse_function(self):
        # The first token must be: FUNCTION
        # This comes from the word: function
        self.expect("FUNCTION")
        # The next token must be: (
        self.expect("LPAREN")
        # Parse the expression inside the parenthesis.
        # For: function (2 + 2) this parses: 2 + 2
        body = self.parse_expression()
        # Require the closing )
        self.expect("RPAREN")
        # Create and return a Function node.
        # If body represents: 2 + 2, the result becomes:
        # Function
        # └── Binary(...)
        return Function(body)

    # Parse an artithmetic expression.
    # For now, this parser supports simple expressions such as: 2 + 2 or 10 - 5
    # If does NOT yet support longer expressions, such as: 2 + 3 * 4
    # Proper operator precedence will require a slighly more advanced parser.
    def parse_expression(self):
        # Parse the first number
        left = self.parse_number()
        # Look at the next token's type.
        # For 2 + 2 the current token is: ("PLUS", "+"), so operator becomes: "PLUS"
        operator = self.current()[0]

        # Check whether the next token is one of the operators the language understands.
        if operator in ("PLUS", "MINUS", "STAR", "SLASH"):
            # Move past the operator token.
            # This is done manually here because we know which operator it is.
            self.position += 1
            # Parse the number on the right-hand side.
            right = self.parse_number()
            # Create a Binary node representing the expression.
            return Binary(left, operator, right)
        
        # If there was no operator after the first number, then the expression is just that number.
        return left

    # Parse a NUMBER token.
    def parse_number(self):
        # Reuire the current token to be NUMBER
        # For example: ("NUMBER", "2")
        token = self.expect("NUMBER")
        # Get the original text of the number.
        # For: ("NUMBER", "2") token[1] is: "2"
        value = token[1]
        # The tokenizer gives us text, so we need to convert it into an actual Python number.
        # If the number contains a decimal point...
        if "." in value:
            # Convert it into a floating-point number.
            # Example: "2.5" becomes: 2.5
            return Number(float(value))
        # Otherwise convert it into an integer.
        # Example: "2" becomes: 2
        return Number(int(value))

# -------------------------
# EVALUATOR
# An evaluator is the part of your interpreter that takes the parsed syntax tree and actually performs the computation.
# -------------------------

def evaluate(node):
    # If the node is a Number, return the actual numerical value.
    if isinstance(node, Number):
        return node.value

    # If the node is a Binary expression, evaluate the left and right sides.
    if isinstance(node, Binary):
        left = evaluate(node.left)
        right = evaluate(node.right)

        # Perform the correct operation.
        if node.operator == "PLUS":
            return left + right

        if node.operator == "MINUS":
            return left - right

        if node.operator == "STAR":
            return left * right

        if node.operator == "SLASH":
            return left / right

    # If the node is a Function, evaluate the function body
    if isinstance(node, Function):
        return evaluate(node.body)

    # If we reach a node type we do not understand, raise an error.
    raise RuntimeError(
        f"Cannot evaluate node: {type(node).__name__}"
    )

# -------------------------
# TEST THE TOKENIZER
# -------------------------

# Call the tokenizer with example source code.
# The string below represents a small program written using the language.
# Pass in the source code into the tokenize function to test the tokenizer is working.
# It is a simple function: function (2 + 2);
##tokens = tokenize("function (2 + 2);")
# Print the list of tokens so the result can be inspected.
##print(tokens)

# Call the tokenizer with example source code.
source = "function (2 + 2);"

tokens = tokenize(source)
# Print the list of tokens so the result can be inspected.
print(tokens)

# Output:
# [('FUNCTION', 'function'), ('LPAREN', '('), ('NUMBER', '2'), ('PLUS', '+'), ('NUMBER', '2'), ('RPAREN', ')'), ('SEMICOLON', ';'), ('EOF', None)]

# -------------------------
# USING THE PARSER
# -------------------------

# Example source code written using the language
source = "function (2 + 2);"

# 1. Send the source code through the tokenizer.
tokens = tokenize(source)
# Give the tokens to the Parser.
parser = Parser(tokens)
# Ask the parser to build the AST.
tree = parser.parse()

# At this point, tree conceptually looks like:
#
# Function
# └── Binary
#     ├── Number(2)
#     ├── PLUS
#     └── Number(2)
#
# It has understood the STRUCTURE of your program,
# but it has not yet calculated 2 + 2.

# The tokenizer creates the tokens, and the parser is already consuming those tokens and building an AST.

def run(source):
    tokens = tokenize(source)
    parser = Parser(tokens)
    tree = parser.parse()
    return evaluate(tree)

# -------------------------
# TEST
# -------------------------

print(run("function (2 + 2);"))
print(run("function (10 - 3);"))
print(run("function (4 * 5);"))
print(run("function (20 / 4);"))