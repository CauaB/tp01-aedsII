# utils.py
from faker import Faker
from typing import List
from student import Student

# Inicializa o gerador de dados fictícios.
# 'pt_BR' garante que nomes e CPFs sejam gerados no formato brasileiro.
fake = Faker('pt_BR')

def generate_students(n: int) -> List[Student]:
    """Gera uma lista de n registros de alunos fictícios."""
    
    students = []
    for _ in range(n):
        students.append(
            Student(
                # Gera dados fictícios para cada campo do modelo Student
                matricula=fake.unique.random_int(min=100000000, max=999999999),
                nome=fake.name(),
                cpf=fake.cpf().replace('.', '').replace('-', ''), # Remove formatação do CPF
                curso=fake.job()[:Student.MAX_CURSO], # Limita o tamanho para ser mais realista
                mae=fake.name(),
                pai=fake.name(),
                ano=fake.random_int(min=2015, max=2024),
                ca=round(fake.random_int(min=500, max=1000) / 100, 2) # Coeficiente entre 5.0 e 10.0
            )
        )
    return students