# tp01-aedsII

Este trabalho implementa um simulador em Python que gerencia a persistência de registros de alunos em um arquivo .DAT, e compara três estratégias distintas de alocação de registros dentro de blocos de tamanho fixo:
1. Registros de Tamanho Fixo: Todos os registros ocupam o mesmo espaço (o tamanho do maior registro possível), preenchido com caracteres de padding (#).
2. Registros de Tamanho Variável (Contíguos): Cada registro ocupa apenas o espaço necessário. Se um registro não cabe em um bloco, ele é movido inteiro para o próximo bloco, gerando fragmentação interna.
3. Registros de Tamanho Variável (Com Espalhamento): O registro pode ser dividido (espalhado) entre blocos, preenchendo 100% do bloco atual antes de continuar no próximo.
