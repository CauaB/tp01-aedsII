# student.py
from dataclasses import dataclass

@dataclass
class Student:
    """
    Define a estrutura de dados para um registro de aluno.
    Usar um @dataclass simplifica a criação da classe,
    auto-gerando métodos como __init__ e __repr__.
    """
    
    # --- Campos de Dados ---
    matricula: int
    nome: str
    cpf: str
    curso: str
    mae: str
    pai: str
    ano: int
    ca: float
    
    # --- Constantes de Tamanho ---
    # Define os tamanhos máximos para os campos de string.
    # Isso é *obrigatório* para a estratégia de TAMANHO FIXO,
    # pois precisamos saber quanto espaço de 'padding' (preenchimento) usar.
    MAX_NOME = 50
    MAX_CURSO = 30
    MAX_MAE = 30
    MAX_PAI = 30
    CPF_LEN = 11