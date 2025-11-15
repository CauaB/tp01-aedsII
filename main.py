# main.py
from utils import generate_students
from simulator import StorageSimulator

def main():
    """Coleta os parâmetros do usuário e executa a simulação."""
    try:
        # --- 1. Definição dos Parâmetros ---
        num_records = int(input("Digite o número de registros a serem gerados: ")) 
        block_size = int(input("Digite o tamanho do bloco (em bytes, ex: 512): ")) 
        
        print("Escolha o modo de armazenamento:")
        print("  1. Registros de tamanho fixo") 
        print("  2. Registros de tamanho variável") 
        mode_choice = input("Opção: ")

        # Valores padrão
        strategy = 'fixed'
        allow_spanning = False
        desc = "Tamanho Fixo"

        if mode_choice == '2':
            strategy = 'variable'
            print("\nPara tamanho variável, escolha a estratégia:")
            print("  1. Contíguos (sem espalhamento)") 
            print("  2. Espalhados (com espalhamento)") 
            span_choice = input("Opção: ")
            
            if span_choice == '1':
                allow_spanning = False
                desc = "Variável (Contíguo)"
            elif span_choice == '2':
                allow_spanning = True
                desc = "Variável (Com Espalhamento)"
            else:
                print("Opção inválida.")
                return
        elif mode_choice != '1':
            print("Opção inválida.")
            return

        print("\nIniciando simulação...")
        print(f"Parâmetros: {num_records} registros, {block_size} bytes/bloco, Modo: {desc}")
        
        # --- 2. Geração dos dados ---
        print("Gerando dados fictícios...")
        students = generate_students(num_records)
        
        # --- 3. Simulação de escrita ---
        print("Simulando escrita em blocos...")
        
        # O 'with' garante que o arquivo (sim.file_handle) será
        # aberto e fechado corretamente, chamando __enter__ e __exit__.
        with StorageSimulator(block_size, strategy, allow_spanning) as sim:
            for student in students:
                sim.write_record(student)
        
        # --- 4. Exibição dos resultados ---
        sim.print_report()

    except ValueError:
        print("Erro: Entrada inválida. Por favor, insira um número.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Inicia o programa
if __name__ == "__main__":
    main()