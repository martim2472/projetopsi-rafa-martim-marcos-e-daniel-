from conexaobasededados import get_connection
from mysql.connector import Error

# Classe de gestão da base de dados
class BD:
    def __init__(self):
        self.conn = get_connection()
    
    def cursor(self, dictionary=False):
        return self.conn.cursor(dictionary=dictionary)
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

# Modelo de utilizador (herança simples)
class Utilizador:
    def __init__(self, id_, nome_utilizador, papel, nome=None, contacto=None):
        self.id = id_
        self.nome_utilizador = nome_utilizador
        self.papel = papel
        self.nome = nome
        self.contacto = contacto

class Admin(Utilizador): pass
class Voluntario(Utilizador): pass
class Doador(Utilizador): pass

# Repositório de operações
class Repositorio:
    def __init__(self, bd: BD):
        self.bd = bd

    # Autenticação (em produção usar hash seguro)
    def verificar_credenciais(self, nome_utilizador, palavra_passe):
        cur = self.bd.cursor(dictionary=True)
        cur.execute('SELECT * FROM utilizadores WHERE nome_utilizador=%s AND palavra_passe=%s', 
                    (nome_utilizador, palavra_passe))
        row = cur.fetchone()
        cur.close()
        if row:
            papel = row['papel']
            cls = {'admin': Admin, 'voluntario': Voluntario, 'doador': Doador}.get(papel, Utilizador)
            return cls(row['id'], row['nome_utilizador'], row['papel'], row.get('nome'), row.get('contacto'))
        return None

    # Gestão de utilizadores
    def criar_utilizador(self, nome_utilizador, palavra_passe, papel, nome=None, contacto=None):
        cur = self.bd.cursor()
        cur.execute(
            'INSERT INTO utilizadores (nome_utilizador,palavra_passe,papel,nome,contacto) VALUES (%s,%s,%s,%s,%s)',
            (nome_utilizador, palavra_passe, papel, nome, contacto)
        )
        self.bd.commit()
        cur.close()

    def atualizar_utilizador(self, id_utilizador, nome=None, contacto=None):
        updates = []
        params = []
        if nome is not None:
            updates.append('nome=%s')
            params.append(nome)
        if contacto is not None:
            updates.append('contacto=%s')
            params.append(contacto)
        
        if not updates:
            return False
            
        query = 'UPDATE utilizadores SET ' + ', '.join(updates) + ' WHERE id=%s'
        params.append(id_utilizador)
        
        cur = self.bd.cursor()
        try:
            cur.execute(query, tuple(params))
            self.bd.commit()
            return cur.rowcount > 0
        except Error as e:
            print(f"Erro ao atualizar utilizador: {e}")
            return False
        finally:
            cur.close()

    # Campanhas
    def criar_campanha(self, titulo, descricao=None, data_inicio=None, data_fim=None):
        cur = self.bd.cursor()
        cur.execute(
            'INSERT INTO campanhas (titulo,descricao,data_inicio,data_fim) VALUES (%s,%s,%s,%s)',
            (titulo, descricao, data_inicio, data_fim)
        )
        self.bd.commit()
        cur.close()

    def encerrar_campanha(self, id_campanha):
        cur = self.bd.cursor()
        cur.execute('UPDATE campanhas SET ativa=FALSE WHERE id=%s', (id_campanha,))
        self.bd.commit()
        cur.close()

    def listar_campanhas(self, apenas_ativas=True):
        cur = self.bd.cursor(dictionary=True)
        if apenas_ativas:
            cur.execute('SELECT * FROM campanhas WHERE ativa=TRUE')
        else:
            cur.execute('SELECT * FROM campanhas')
        rows = cur.fetchall()
        cur.close()
        return rows

    # Doações
    def registar_doacao(self, id_utilizador, id_campanha, tipo_item, quantidade, valor):
        cur = self.bd.cursor()
        cur.execute(
            'INSERT INTO doacoes (id_utilizador,id_campanha,tipo_item,quantidade,valor) VALUES (%s,%s,%s,%s,%s)',
            (id_utilizador, id_campanha, tipo_item, quantidade, valor)
        )
        self.bd.commit()
        cur.close()

    def atualizar_estado_doacao(self, id_doacao, estado):
        cur = self.bd.cursor()
        cur.execute('UPDATE doacoes SET estado=%s WHERE id=%s', (estado, id_doacao))
        self.bd.commit()
        cur.close()

    def obter_doacoes_por_utilizador(self, id_utilizador):
        cur = self.bd.cursor(dictionary=True)
        cur.execute('SELECT * FROM doacoes WHERE id_utilizador=%s', (id_utilizador,))
        rows = cur.fetchall()
        cur.close()
        return rows

    # Voluntários em campanhas
    def atribuir_voluntario(self, id_utilizador, id_campanha, funcao='voluntario'):
        cur = self.bd.cursor()
        cur.execute('INSERT INTO voluntarios_campanhas (id_utilizador,id_campanha,funcao) VALUES (%s,%s,%s)',
                    (id_utilizador, id_campanha, funcao))
        self.bd.commit()
        cur.close()

    # Tarefas
    def atribuir_tarefa(self, id_campanha, descricao, id_voluntario=None):
        cur = self.bd.cursor()
        cur.execute('INSERT INTO tarefas (id_campanha,descricao,id_voluntario) VALUES (%s,%s,%s)',
                    (id_campanha, descricao, id_voluntario))
        self.bd.commit()
        cur.close()

    def listar_tarefas_por_voluntario(self, id_voluntario):
        cur = self.bd.cursor(dictionary=True)
        cur.execute('SELECT * FROM tarefas WHERE id_voluntario=%s', (id_voluntario,))
        rows = cur.fetchall()
        cur.close()
        return rows

    def atualizar_estado_tarefa(self, id_tarefa, estado):
        cur = self.bd.cursor()
        cur.execute('UPDATE tarefas SET estado=%s WHERE id=%s', (estado, id_tarefa))
        self.bd.commit()
        cur.close()

    # Relatórios
    def total_doacoes_por_campanha(self, id_campanha):
        cur = self.bd.cursor(dictionary=True)
        cur.execute(
            'SELECT SUM(valor) as total_valor, SUM(quantidade) as total_quantidade FROM doacoes WHERE id_campanha=%s',
            (id_campanha,)
        )
        row = cur.fetchone()
        cur.close()
        return row

    def contar_voluntarios_ativos(self):
        cur = self.bd.cursor(dictionary=True)
        cur.execute("SELECT COUNT(DISTINCT id_utilizador) as n FROM voluntarios_campanhas")
        row = cur.fetchone()
        cur.close()
        return row['n'] if row else 0

    def distribuicao_por_tipo_item(self):
        cur = self.bd.cursor(dictionary=True)
        cur.execute('SELECT tipo_item, SUM(quantidade) as total FROM doacoes GROUP BY tipo_item')
        rows = cur.fetchall()
        cur.close()
        return rows
        
    def listar_voluntarios(self):
        cur = self.bd.cursor(dictionary=True)
        cur.execute('''
            SELECT u.id, u.nome_utilizador, u.nome, u.contacto, 
                   GROUP_CONCAT(DISTINCT c.titulo) as campanhas
            FROM utilizadores u
            LEFT JOIN voluntarios_campanhas vc ON u.id = vc.id_utilizador
            LEFT JOIN campanhas c ON vc.id_campanha = c.id
            WHERE u.papel = 'voluntario'
            GROUP BY u.id
        ''')
        rows = cur.fetchall()
        cur.close()
        return rows

    def check_credentials(self, username, password=None):
        cur = self.bd.cursor(dictionary=True)
        if password:
            query = 'SELECT * FROM utilizadores WHERE nome_utilizador=%s AND palavra_passe=%s'
            params = (username, password)
        else:
            query = 'SELECT * FROM utilizadores WHERE nome_utilizador=%s'
            params = (username,)
            
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close()
        
        if row:
            papel = row['papel']
            cls = {'admin': Admin, 'voluntario': Voluntario, 'doador': Doador}.get(papel, Utilizador)
            return cls(row['id'], row['nome_utilizador'], row['papel'], row.get('nome'), row.get('contacto'))
        return None

