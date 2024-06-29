import re
import json
import os
# Tokenizer class
class Tokenizer:
    token_patterns = {
        'NUMBER': r'\d+(\.\d+)?',
        'OPERATOR': r'[+\-*/]',
        'PAREN': r'[()]',
        'IDENTIFIER': r'[a-zA-Z]\w*',
        'ASSIGN': r'='
    }

    def __init__(self):
        self.token_regex = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_patterns.items()))
    
    def tokenize(self, input_string):
        tokens = []
        for match in self.token_regex.finditer(input_string):
            token_type = match.lastgroup
            token_value = match.group(token_type)
            tokens.append((token_type, token_value))
        return tokens

    def tokenize_to_file(self, input_string, filename):
        tokens = self.tokenize(input_string)
        with open(filename, 'w') as file:
            file.write(json.dumps(tokens))
        return tokens

# Parser class
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.error = None
    
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self):
        self.pos += 1
    
    def parse_expression(self):
        try:
            node = self.parse_term()
            while self.peek() and self.peek()[1] in '+-':
                token = self.peek()
                self.consume()
                right = self.parse_term()
                node = ('bin_op', token[1], node, right)
            return node
        except SyntaxError as se:
            self.error = str(se)
            return None
    
    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()[1] in '*/':
            token = self.peek()
            self.consume()
            right = self.parse_factor()
            node = ('bin_op', token[1], node, right)
        return node
    
    def parse_factor(self):
        token = self.peek()
        if token[0] == 'NUMBER':
            self.consume()
            return ('number', token[1])
        elif token[0] == 'IDENTIFIER':
            self.consume()
            return ('identifier', token[1])
        elif token[1] == '(':
            self.consume()
            expr = self.parse_expression()
            if self.peek() and self.peek()[1] == ')':
                self.consume()
                return expr
            else:
                raise SyntaxError("Unmatched parenthesis")
        else:
            raise SyntaxError(f"Unexpected token: {token}")

    def parse_to_file(self, filename):
        parse_tree = self.parse_expression()
        if self.error:
            with open(filename, 'w') as file:
                file.write(f"Error: {self.error}\n")
            return None
        else:
            with open(filename, 'w') as file:
                file.write(json.dumps(parse_tree))
            return parse_tree

# Symbol Table class
class SymbolTable:
    def __init__(self, filename):
        self.filename = filename
        self.table = {}
        self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                self.table = json.load(file)
    
    def save(self):
        with open(self.filename, 'w') as file:
            json.dump(self.table, file)
    
    def set(self, variable, value):
        self.table[variable] = value
        self.save()
    
    def get(self, variable):
        return self.table.get(variable, None)

# Evaluation Engine
def evaluate(node, symbol_table):
    if node[0] == 'number':
        return float(node[1])
    elif node[0] == 'identifier':
        value = symbol_table.get(node[1])
        if value is None:
            raise NameError(f"Undefined variable: {node[1]}")
        return value
    elif node[0] == 'bin_op':
        left_val = evaluate(node[2], symbol_table)
        right_val = evaluate(node[3], symbol_table)
        if node[1] == '+':
            return left_val + right_val
        elif node[1] == '-':
            return left_val - right_val
        elif node[1] == '*':
            return left_val * right_val
        elif node[1] == '/':
            return left_val / right_val

# Main Program
def process_expression(input_string, tokenizer, symbol_table):
    tokens_file = "tokens.txt"
    parse_tree_file = "parse_tree.txt"
    error_file = "error.txt"

    # Tokenize the input
    try:
        tokens = tokenizer.tokenize_to_file(input_string, tokens_file)
    except Exception as e:
        print(f"Tokenization error: {e}")
        return f"Tokenization error: {e}"

    # Check for assignment
    if '=' in input_string:
        parts = input_string.split('=')
        variable = parts[0].strip()
        expression = parts[1].strip()
        tokens = tokenizer.tokenize(expression)
        # Evaluate the expression and store the variable
        parser = Parser(tokens)
        parse_tree = parser.parse_expression()
        if parse_tree and not parser.error:
            try:
                value = evaluate(parse_tree, symbol_table)
                symbol_table.set(variable, value)
                return f"{variable} = {value}"
            except Exception as e:
                with open(error_file, 'w') as file:
                    file.write(f"Evaluation error: {e}\n")
                return f"Evaluation error: {e}"
        else:
            with open(error_file, 'w') as file:
                file.write(f"Error: {parser.error}\n")
            return f"Parsing error: {parser.error}"
    else:
        # Parse the tokens
        parser = Parser(tokens)
        parse_tree = parser.parse_to_file(parse_tree_file)
        if parser.error:
            with open(error_file, 'w') as file:
                file.write(f"Error: {parser.error}\n")
            return f"Parsing error: {parser.error}"
        else:
            # Evaluate the expression
            try:
                result = evaluate(parse_tree, symbol_table)
                return f"Result: {result}"
            except Exception as e:
                with open(error_file, 'w') as file:
                    file.write(f"Evaluation error: {e}\n")
                return f"Evaluation error: {e}"

def main():
    # Setup file names
    symbol_table_file = "symbol_table.txt"
    output_file = "results.txt"

    # Initialize classes
    tokenizer = Tokenizer()
    symbol_table = SymbolTable(symbol_table_file)

    while True:
        # Input options
        print("Choose an option:")
        print("1. Enter expression")
        print("2. Read expressions from file")
        print("3. Exit")
        input_source = input("Enter your choice (1, 2, or 3): ")

        if input_source == '1':
            input_string = input("Enter the expression: ")
            result = process_expression(input_string, tokenizer, symbol_table)
            print(result)
        elif input_source == '2':
            input_filename = input("Enter the input file name: ")
            try:
                with open(input_filename, 'r') as infile:
                    expressions = infile.readlines()
                
                with open(output_file, 'w') as outfile:
                    for expression in expressions:
                        expression = expression.strip()
                        if expression:
                            print(f"Processing: {expression}")
                            result = process_expression(expression, tokenizer, symbol_table)
                            print(result)
                            outfile.write(f"{expression}: {result}\n")
                print(f"Results have been written to {output_file}")
            except FileNotFoundError:
                print("File not found.")
        elif input_source == '3':
            print("Exiting...")
            break
        else:
            print("Invalid input source.")

if __name__ == "__main__":
    main()
