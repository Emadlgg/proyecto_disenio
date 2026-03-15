import sys
import importlib.util
from yalex.yalex_reader import read_file
from yalex.lexer_builder import build_lexer_from_spec
from yalex.generator import generate_lexer_file


def load_generated_lexer(path):
    spec = importlib.util.spec_from_file_location("generated_lexer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python yalex.py archivo.yal -o salida.py")
        print("  python yalex.py archivo.yal -run \"texto\"")
        sys.exit(1)

    input_file = sys.argv[1]
    text = read_file(input_file)
    afd = build_lexer_from_spec(text)

    # Caso 1: generar archivo
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
        else:
            output_file = "lexer.py"

        generate_lexer_file(afd, output_file)
        print(f"Lexer generado en: {output_file}")
        return

    # Caso 2: generar y ejecutar inmediatamente
    if "-run" in sys.argv:
        idx = sys.argv.index("-run")
        if idx + 1 < len(sys.argv):
            input_text = sys.argv[idx + 1]
        else:
            print("Debe proporcionar texto para -run")
            sys.exit(1)

        output_file = "temp_lexer.py"
        generate_lexer_file(afd, output_file)

        lexer = load_generated_lexer(output_file)
        print("Tokens:", lexer.tokenize(input_text))
        return

    # Caso por defecto: solo generar lexer.py
    generate_lexer_file(afd, "lexer.py")
    print("Lexer generado en: lexer.py")


if __name__ == "__main__":
    main()