# Cupcake
My own programming language. Released under the MIT licence.

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