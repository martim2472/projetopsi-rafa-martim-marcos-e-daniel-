from conexaobasededados import get_connection, DB_CONFIG
from mysql.connector import Error

DB_NAME = DB_CONFIG.get('database', 'voluntariado')

TABLES = {
    "utilizadores": """
    CREATE TABLE IF NOT EXISTS utilizadores (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome_utilizador VARCHAR(100) UNIQUE NOT NULL,
        palavra_passe VARCHAR(255) NOT NULL,
        papel ENUM('admin','voluntario','doador') NOT NULL,
        nome VARCHAR(255),
        contacto VARCHAR(255),
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    "campanhas": """
    CREATE TABLE IF NOT EXISTS campanhas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(255) NOT NULL,
        descricao TEXT,
        data_inicio DATE,
        data_fim DATE,
        ativa BOOLEAN DEFAULT TRUE,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    "doacoes": """
    CREATE TABLE IF NOT EXISTS doacoes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_utilizador INT,
        id_campanha INT,
        tipo_item VARCHAR(255),
        quantidade INT DEFAULT 0,
        valor DECIMAL(10,2) DEFAULT 0.0,
        estado ENUM('pendente','entregue','distribuida') DEFAULT 'pendente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_utilizador) REFERENCES utilizadores(id) ON DELETE SET NULL,
        FOREIGN KEY (id_campanha) REFERENCES campanhas(id) ON DELETE SET NULL
    )""",

    "voluntarios_campanhas": """
    CREATE TABLE IF NOT EXISTS voluntarios_campanhas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_utilizador INT,
        id_campanha INT,
        funcao VARCHAR(255),
        atribuido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_utilizador) REFERENCES utilizadores(id) ON DELETE CASCADE,
        FOREIGN KEY (id_campanha) REFERENCES campanhas(id) ON DELETE CASCADE
    )""",

    "tarefas": """
    CREATE TABLE IF NOT EXISTS tarefas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_campanha INT,
        descricao VARCHAR(255),
        estado ENUM('pendente','em_progresso','concluida') DEFAULT 'pendente',
        id_voluntario INT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_campanha) REFERENCES campanhas(id) ON DELETE CASCADE,
        FOREIGN KEY (id_voluntario) REFERENCES utilizadores(id) ON DELETE SET NULL
    )"""

}

def init_db():
    # Criar Base de Dados se necessário
    cnx = get_connection(use_database=False)
    cursor = cnx.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"Base de dados '{DB_NAME}' criada/verificada.")
    except Error as e:
        print("Erro ao criar BD:", e)
        cursor.close()
        cnx.close()
        return
    cursor.close()
    cnx.close()

    # Criar as tabelas dentro da BD
    cnx = get_connection(use_database=True)
    cursor = cnx.cursor()
    for name, ddl in TABLES.items():
        try:
            cursor.execute(ddl)
            print(f"Tabela '{name}' criada/verificada.")
        except Error as e:
            print(f"Erro ao criar tabela {name}: {e}")

    cnx.commit()
    cursor.close()
    cnx.close()
    print("Inicialização da Base de Dados concluída.")

if __name__ == "__main__":
    init_db()
