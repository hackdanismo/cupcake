# Cupcake
My own programming language. Released under the MIT licence.

Currently an interpreter written in `Python` with the intention to eventually be self-hosting, but for now designed to use `Python` to run code with file extensions of `.cake`. The focus initially is on syntax and functionality of the language.

## Tokenizer
A `tokenizer` is the first stage of the development of the programming language. A `tokenizer` is the part of a programming language that takes raw `source code` and breaks it into meaningful pieces called `tokens`.

In order to run a simple function like:

```
function (2 + 2);
```

This is just a string of characters at first. The `tokenizer` turns it into something like:

```
[
    ("FUNCTION", "function"),
    ("LPAREN", "("),
    ("NUMBER", "2"),
    ("PLUS", "+"),
    ("NUMBER", "2"),
    ("RPAREN", ")"),
    ("SEMICOLON", ";"),
    ("EOF", None)
]
```

Each token usually has two parts:

```
token type     token value
-----------    -----------
FUNCTION       function
LPAREN         (
NUMBER         2
PLUS           +
NUMBER         2
RPAREN         )
SEMICOLON      ;
```

The tokenizer does not yet understand:

```
2 + 2
```

It only recognizes the pieces:

```
NUMBER
PLUS
NUMBER
```

The `parser` comes next and works out the structure and meaning.

We need to extend the language further with a `parser` and `evaluator`. The `parser` needs to understand what the tokens mean and the `evaluator` needs to calculate the result. The key idea is that the `tokenizer` doesn't yet understand that `2 + 2` means addition. It only identifies the pieces. Understanding how those pieces relate to each other is the `parser's` job.:

```
Tokenizer → Parser → Evaluator
```

So the `tokenizer` is essentially the first reader of the programming language. It answers questions like:

- **Is this a number?**
- **Is this a keyword?**
- **Is this +?**
- **Is this (?**
- **Is this whitespace?**
- **Is this an invalid character?**

Then it hands those `tokens` to the `parser`.

## Parser
A `parser` is the part of the language that takes the `tokens` from the `tokenizer` and works out their structure.

Your `tokenizer` might turn:

```
function (2 + 2);
```

into:

```
FUNCTION
LPAREN
NUMBER
PLUS
NUMBER
RPAREN
SEMICOLON
EOF
```

The `parser` then asks: **"What do these tokens mean when they appear in this order?"**. In the code, the `parser` builds an `AST`, or `Abstract Syntax Tree`. 

```
FUNCTION LPAREN NUMBER PLUS NUMBER RPAREN
```

Becomes:

```
Function
└── Binary
    ├── Number(2)
    ├── PLUS
    └── Number(2)
```

That tree is much easier for the `evaluator` to understand than a flat list of tokens.

In the `parser`, `parse()` starts the process, `parse_function()` recognizes the shape of a function, and `parse_expression()` recognizes simple arithmetic expressions. The `tokenizer` identifies the pieces, the `parser` turns them into a structured tree, and the `evaluator` can then walk that tree and return the result of the code.

## Evaluator
An `evaluator` is the part of your interpreter that takes the `parsed` syntax tree and actually performs the computation.

## Running the Interpreter
Use `Python` to run the `Interpreter`. The file structure should be:

```
project/
    cupcake.py
    test.cake
```

Run the `test.cake` file:

```shell
$ python3 cupcake.py test.cake
```

## Syntax

### Comments
Code comments can be added as single-line comments or as block comments.

```
# Single-line comments

##
Block comments
over multiple lines
##
```

### Functions
`Anonymous` functions that do not have names are executed immediately when the program runs.

```
function (2 + 2);
```

A function can be called when it has a name:

```
function add (2 + 2);

add();
```