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

# Call the tokenizer with example source code.
# The string below represents a small program written using the language.
# Pass in the source code into the tokenize function to test the tokenizer is working.
# It is a simple function: function (2 + 2);
tokens = tokenize("function (2 + 2);")
# Print the list of tokens so the result can be inspected.
print(tokens)

# Output:
# [('FUNCTION', 'function'), ('LPAREN', '('), ('NUMBER', '2'), ('PLUS', '+'), ('NUMBER', '2'), ('RPAREN', ')'), ('SEMICOLON', ';'), ('EOF', None)]

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
# -------------------------