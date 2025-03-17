## Info

Small compiler created for University of Helsinki's spring 2025 [Compilers course](https://hy-compilers.github.io/spring-2025/).
Largely based on the course material, courtesy of Martin Pärtel.

Supported features:

- Integers
- Booleans
- Binary operators `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `and`, `or`
- Unary operators `-` and `not`
- Library functions `print_int`, `read_int` and `print_bool`
- Blocks of statements
- Local variables with initializers
- Assignment statements
- `if`-`then` and `if`-`then`-`else`
- `while` loops
- `break` and `continue` expressions
- Function definitions

## Setup

Requirements:

- [Pyenv](https://github.com/pyenv/pyenv) for installing Python 3.12+
    - Recommended installation method: the "automatic installer"
      i.e. `curl https://pyenv.run | bash`
    - Follow the instructions at the end of the output to make pyenv available in your shell.
      You may need to restart your shell or even log out and log in again to make
      the `pyenv` command available.
- [Poetry](https://python-poetry.org/) for installing dependencies
    - Recommended installation method: the "official installer"
      i.e. `curl -sSL https://install.python-poetry.org | python3 -`

Install dependencies:

    # Install Python specified in `.python-version`
    pyenv install
    # Install dependencies specified in `pyproject.toml`
    poetry install

If `pyenv install` gives an error about `_tkinter`, you can ignore it.
If you see other errors, you may have to investigate.

If you have trouble with Poetry not picking up pyenv's python installation,
try `poetry env remove --all` and then `poetry install` again.

## Compiling

The language specification for the compiler's language can be found [here](https://hy-compilers.github.io/spring-2025/language-spec/).
The compiler can be run by:

    ./compiler.sh compile path/to/source/code --output=path/to/output/file

Binaries are only compiled for x86 Linux, other platforms are not supported (though WSL naturally works).
