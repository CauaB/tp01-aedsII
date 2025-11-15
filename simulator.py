# simulator.py
import struct
import os
from typing import List, Dict
from student import Student

# Tenta importar o matplotlib para o gráfico opcional
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ==============================================================================
# --- SEÇÃO DE SERIALIZAÇÃO ---
# Converte o objeto Student (RAM) em bytes (Disco)
# ==============================================================================

def pack_fixed(student: Student) -> bytes:
    """
    Converte um registro de aluno em bytes usando a estratégia de TAMANHO FIXO.
    Todos os campos de string são preenchidos (padding) até o tamanho máximo.
    """
    try:
        # Empacota os campos numéricos de tamanho fixo (int, int, float)
        # 'i' = 4 bytes, 'i' = 4 bytes, 'f' = 4 bytes. Total: 12 bytes
        header = struct.pack('iif', student.matricula, student.ano, student.ca)
        
        # Codifica strings para utf-8, limita ao tamanho máximo,
        # e aplica 'ljust' (Left Justify) com o caractere de preenchimento '#'.
        nome_b = student.nome.encode('utf-8')[:Student.MAX_NOME].ljust(Student.MAX_NOME, b'#')
        cpf_b = student.cpf.encode('utf-8')[:Student.CPF_LEN].ljust(Student.CPF_LEN, b'#')
        curso_b = student.curso.encode('utf-8')[:Student.MAX_CURSO].ljust(Student.MAX_CURSO, b'#')
        mae_b = student.mae.encode('utf-8')[:Student.MAX_MAE].ljust(Student.MAX_MAE, b'#')
        pai_b = student.pai.encode('utf-8')[:Student.MAX_PAI].ljust(Student.MAX_PAI, b'#')

        # Tamanho total fixo: 12 + 50 + 11 + 30 + 30 + 30 = 163 bytes
        return header + nome_b + cpf_b + curso_b + mae_b + pai_b
    except Exception as e:
        print(f"Erro ao empacotar (fixo) {student.matricula}: {e}")
        return b''

def pack_variable(student: Student) -> bytes:
    """
    Converte um registro de aluno em bytes usando a estratégia de TAMANHO VARIÁVEL.
    Usa um caractere nulo (b'\0') como delimitador de fim de string.
    """
    try:
        # Empacota os campos numéricos (12 bytes)
        header = struct.pack('iif', student.matricula, student.ano, student.ca)
        
        # Concatena todas as strings, cada uma terminada com b'\0'.
        # O tamanho final do registro depende do conteúdo real dos dados.
        strings_b = b''.join([
            student.nome.encode('utf-8') + b'\0',
            student.cpf.encode('utf-8') + b'\0',
            student.curso.encode('utf-8') + b'\0',
            student.mae.encode('utf-8') + b'\0',
            student.pai.encode('utf-8') + b'\0'
        ])
        return header + strings_b
    except Exception as e:
        print(f"Erro ao empacotar (variável) {student.matricula}: {e}")
        return b''

def get_variable_size(student: Student) -> int:
    """
    Calcula o tamanho "útil" real de um registro, como se fosse 'variável'.
    Isso é usado para calcular a 'Eficiência de Armazenamento' no modo Fixo,
    comparando o espaço usado (163 bytes) vs o espaço que seria útil (ex: 80 bytes).
    """
    try:
        size = struct.calcsize('iif') # 12 bytes
        size += len(student.nome.encode('utf-8'))
        size += len(student.cpf.encode('utf-8'))
        size += len(student.curso.encode('utf-8'))
        size += len(student.mae.encode('utf-8'))
        size += len(student.pai.encode('utf-8'))
        return size + 5 # +5 pelos 5 delimitadores b'\0'
    except Exception:
        return 0

# ==============================================================================
# --- CLASSE DO SIMULADOR ---
# Gerencia a lógica de blocos e a escrita no arquivo .DAT
# ==============================================================================

class StorageSimulator:
    """Simula o armazenamento de registros em um arquivo .DAT dividido em blocos."""
    
    def __init__(self, block_size: int, strategy: str, allow_spanning: bool):
        self.block_size = block_size
        self.strategy = strategy          # 'fixed' ou 'variable'
        self.allow_spanning = allow_spanning  # True (Espalhado) ou False (Contíguo)
        
        self.output_file = 'alunos.dat'
        self.chart_file = 'ocupacao_blocos.png' 
        self.file_handle = None
        
        # O 'bloco' atual mantido em memória (RAM)
        self.current_block = bytearray()
        
        # --- Estatísticas ---
        self.block_stats: List[Dict[str, int]] = [] # Lista para o relatório e gráfico
        self.total_useful_data = 0 # Acumulador para o cálculo de eficiência

    def __enter__(self):
        """
        Abre o arquivo .DAT em modo 'wb' (write, binary).
        'w' garante que o arquivo seja sobrescrito a cada nova simulação.
        """
        self.file_handle = open(self.output_file, 'wb')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Garante que o último bloco seja salvo antes de fechar o arquivo.
        Isso é chamado automaticamente ao sair do bloco 'with' em main.py.
        """
        self._flush_block() # Salva o último bloco (parcial)
        if self.file_handle:
            self.file_handle.close()
        print(f"\nArquivo '{self.output_file}' gerado com sucesso.")

    def _flush_block(self):
        """
        Escreve o bloco da memória (RAM) para o disco (Arquivo .DAT)
        e preenche o espaço restante com padding (bytes nulos).
        """
        if not self.current_block:
            return # Não faz nada se o bloco estiver vazio

        used_bytes = len(self.current_block)
        
        # Calcula o 'padding' (preenchimento) de bloco.
        # Este é o espaço desperdiçado *dentro* do bloco.
        padding_size = self.block_size - used_bytes
        if padding_size < 0:
            padding_size = 0 # Segurança para o modo 'spanning'
            
        self.current_block.extend(b'\0' * padding_size)
        
        # Escreve o bloco inteiro (dados + padding) no arquivo
        self.file_handle.write(self.current_block)
        
        # Salva as estatísticas deste bloco
        self.block_stats.append({
            'used': used_bytes,
            'total': self.block_size
        })
        
        # Reseta o bloco da memória para o próximo ciclo
        self.current_block = bytearray()

    def _get_record_data(self, student: Student) -> (bytes, int):
        """Helper para selecionar a função de packing correta e calcular o tamanho útil."""
        if self.strategy == 'fixed':
            record_bytes = pack_fixed(student)
            useful_size = get_variable_size(student)
            return record_bytes, useful_size
        else:
            record_bytes = pack_variable(student)
            useful_size = len(record_bytes) # No modo variável, todo o registro é útil
            return record_bytes, useful_size

    def write_record(self, student: Student):
        """
        Coração da lógica do simulador. Organiza e escreve um registro
        conforme a estratégia de armazenamento escolhida.
        """
        record_bytes, useful_size = self._get_record_data(student)
        record_size = len(record_bytes)
        
        if record_size == 0:
            return # Falha ao empacotar

        # --- Validação de Tamanho (ANTES de contar) ---
        # Impede que registros impossíveis (maiores que o bloco) sejam escritos
        # ou contados, exceto no modo 'spanning'.
        if (self.strategy == 'fixed' or not self.allow_spanning) and record_size > self.block_size:
            print(f"Erro: Registro {student.matricula} ({record_size}b) é maior que o bloco ({self.block_size}b) e não pode ser escrito.")
            return

        # Soma ao total de dados "reais" (sem padding)
        self.total_useful_data += useful_size

        # ======================================================
        # --- LÓGICA DE ARMAZENAMENTO (Tratamento de Limites) ---
        # ======================================================

        # --- Estratégia 1: Tamanho Fixo ---
        if self.strategy == 'fixed':
            # Se o registro (fixo de 163b) não cabe no espaço que sobrou,
            # "fecha" (flusha) o bloco atual e inicia um novo.
            if len(self.current_block) + record_size > self.block_size:
                self._flush_block()
            self.current_block.extend(record_bytes)

        # --- Estratégia 2: Variável (Contíguo, Sem Espalhamento) ---
        elif self.strategy == 'variable' and not self.allow_spanning:
            # Lógica idêntica ao Fixo: se não cabe, vai para o próximo.
            # A diferença é que 'record_size' é variável.
            # Isso gera a "Fragmentação Interna".
            if len(self.current_block) + record_size > self.block_size:
                self._flush_block()
            self.current_block.extend(record_bytes)

        # --- Estratégia 3: Variável (Com Espalhamento) ---
        elif self.strategy == 'variable' and self.allow_spanning:
            bytes_to_write = record_size
            record_offset = 0 # Controla qual parte do registro estamos lendo
            
            while bytes_to_write > 0:
                # Calcula o espaço livre no bloco atual
                space_in_block = self.block_size - len(self.current_block)
                
                if space_in_block == 0:
                    # Se o bloco está 100% cheio, "fecha" e começa um novo
                    self._flush_block()
                    space_in_block = self.block_size

                # Calcula o pedaço (chunk) que cabe no bloco atual
                chunk_size = min(bytes_to_write, space_in_block)
                
                chunk = record_bytes[record_offset : record_offset + chunk_size]
                self.current_block.extend(chunk)
                
                # Atualiza os contadores para o loop
                bytes_to_write -= chunk_size
                record_offset += chunk_size

    # ==============================================================================
    # --- SEÇÃO DE ESTATÍSTICAS E RELATÓRIO ---
    # ==============================================================================

    def _generate_chart(self, block_percentages: List[float]):
        """Gera um gráfico de barras da ocupação dos blocos."""
        if not MATPLOTLIB_AVAILABLE:
            print("\n(Biblioteca 'matplotlib' não encontrada. Pulando geração do gráfico.)")
            print("(Para instalar, rode: pip install matplotlib)")
            return
        
        print(f"Gerando gráfico em '{self.chart_file}'...")
        
        # Limita a 50 blocos no gráfico para não poluir
        num_blocks_to_show = min(len(block_percentages), 50)
        data_to_plot = block_percentages[:num_blocks_to_show]
        block_numbers = [str(i+1) for i in range(num_blocks_to_show)]

        plt.figure(figsize=(15, 7))
        bar_colors = ['#007acc' if p < 100 else '#004c80' for p in data_to_plot]
        plt.bar(block_numbers, data_to_plot, color=bar_colors)
        
        plt.title(f'Taxa de Ocupação dos Blocos (Primeiros {num_blocks_to_show} Blocos)', fontsize=16)
        plt.xlabel('Número do Bloco')
        plt.ylabel('Ocupação (%)')
        plt.ylim(0, 100)
        
        plt.axhline(y=100, color='red', linestyle='--', linewidth=0.8, label='100% Cheio')
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.savefig(self.chart_file)
        plt.close()

    def print_report(self):
        """Calcula e exibe as estatísticas finais e gera o gráfico."""
        if not self.block_stats:
            print("Nenhum dado foi escrito.")
            return

        print("\n" + "="*30)
        print("📊 Relatório de Armazenamento")
        print("="*30)

        # --- 1. Número total de blocos utilizados ---
        total_blocks = len(self.block_stats) 
        
        # Dados para os próximos cálculos
        total_used_bytes = sum(b['used'] for b in self.block_stats)
        total_capacity_bytes = total_blocks * self.block_size
        
        # --- 2. Percentual médio de ocupação de cada bloco ---
        block_percentages = [(b['used'] / b['total']) * 100 for b in self.block_stats]
        avg_occupancy = sum(block_percentages) / total_blocks 
        
        # --- 3. Número de blocos parcialmente utilizados ---
        # (Conta blocos que não estão 100% cheios, mas que também não estão vazios)
        partial_blocks = sum(1 for b in self.block_stats if b['used'] < b['total'] and b['used'] > 0) 
        
        # --- 4. Eficiência de armazenamento (% de bytes úteis) ---
        # (Compara o total de dados "reais" com a capacidade total alocada)
        storage_efficiency = (self.total_useful_data / total_capacity_bytes) * 100 

        # --- Exibição do Resumo --- 
        print(f"1. Número total de blocos utilizados: {total_blocks}")
        print(f"2. Percentual médio de ocupação: {avg_occupancy:.2f}%")
        print(f"3. Blocos parcialmente utilizados: {partial_blocks}")
        print(f"4. Eficiência de armazenamento (dados úteis): {storage_efficiency:.2f}%")
        
        # --- Exibição do Mapa Textual --- 
        print("\n--- Mapa de Ocupação dos Blocos ---") 
        # Mostra apenas os 10 primeiros para não poluir o console
        for i, stats in enumerate(self.block_stats[:10]):
            percent_full = (stats['used'] / stats['total']) * 100
            print(f"Bloco {i+1}: {stats['used']} bytes usados / {stats['total']} bytes ( {percent_full:.2f}% cheio )")
        if total_blocks > 10:
            print(f"(... e mais {total_blocks - 10} blocos)")

        # --- Geração do Gráfico Opcional --- 
        self._generate_chart(block_percentages)