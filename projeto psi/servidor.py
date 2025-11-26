import socket
import threading
from modelos import BD, Repositorio
from protocolo import Protocolo

HOST = '0.0.0.0'
PORT = 5000

class ManipuladorCliente(threading.Thread):
    def __init__(self, conn, addr, repo: Repositorio):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.repo = repo
        self.utilizador = None

    def run(self):
        Protocolo.enviar_mensagem(self.conn, Protocolo.empacotar_comando('BEMVINDO', 'Conectado ao servidor'))
        try:
            while True:
                payload = Protocolo.receber_mensagem(self.conn)
                if not payload:
                    break
                try:
                    partes = Protocolo.desempacotar_comando(payload)
                    if not partes:
                        raise ValueError("Comando inválido")
                    cmd = partes[0].upper()
                    args = partes[1:]
                    handler_name = f'tratar_{cmd.lower()}'
                    if hasattr(self, handler_name):
                        metodo = getattr(self, handler_name)
                        resposta = metodo(*args)
                    else:
                        resposta = Protocolo.empacotar_comando('ERRO', 'Comando desconhecido')
                except Exception as e:
                    resposta = Protocolo.empacotar_comando('ERRO', f'Erro interno: {e}')
                Protocolo.enviar_mensagem(self.conn, resposta)
        finally:
            self.conn.close()

    # --- Handlers ---
    def tratar_registar(self, nome_utilizador, palavra_passe, papel='doador', nome='', contacto=''):
        papel = papel.lower()
        if papel not in ('admin', 'voluntario', 'doador'):
            return Protocolo.empacotar_comando('ERRO', 'Papel inválido')
        self.repo.criar_utilizador(nome_utilizador, palavra_passe, papel, nome, contacto)
        cur = self.repo.bd.cursor(dictionary=True)
        cur.execute("SELECT id FROM utilizadores WHERE nome_utilizador=%s", (nome_utilizador,))
        row = cur.fetchone()
        cur.close()
        novo_id = row['id'] if row else 'desconhecido'
        return Protocolo.empacotar_comando('OK', 'Utilizador registado', papel, str(novo_id))

    def tratar_login(self, nome_utilizador, palavra_passe):
        user = self.repo.verificar_credenciais(nome_utilizador, palavra_passe)
        if user:
            self.utilizador = user
            return Protocolo.empacotar_comando('OK', 'Login bem sucedido', user.papel, str(user.id))
        return Protocolo.empacotar_comando('ERRO', 'Credenciais inválidas')

    def requer_autenticacao(self):
        return self.utilizador is not None

    # --- Campanhas ---
    def tratar_criar_campanha(self, titulo, descricao=''):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        if self.utilizador.papel != 'admin': return Protocolo.empacotar_comando('ERRO','Permissão negada')
        self.repo.criar_campanha(titulo, descricao)
        return Protocolo.empacotar_comando('OK','Campanha criada')

    def tratar_encerrar_campanha(self, id_campanha):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        if self.utilizador.papel != 'admin': return Protocolo.empacotar_comando('ERRO','Permissão negada')
        self.repo.encerrar_campanha(int(id_campanha))
        return Protocolo.empacotar_comando('OK','Campanha encerrada')

    def tratar_listar_campanhas(self, apenas_ativas='1'):
        apenas = apenas_ativas=='1'
        rows = self.repo.listar_campanhas(apenas_ativas=apenas)
        linhas = [f"{r['id']};{r['titulo']};{r['descricao']};{1 if r['ativa'] else 0}" for r in rows]
        return Protocolo.empacotar_comando('OK','\n'.join(linhas))

    # --- Doações ---
    def tratar_doar(self, id_campanha, tipo_item, quantidade, valor):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        if self.utilizador.papel not in ('doador','admin'): return Protocolo.empacotar_comando('ERRO','Apenas doadores podem doar')
        self.repo.registar_doacao(self.utilizador.id,int(id_campanha),tipo_item,int(quantidade),float(valor))
        return Protocolo.empacotar_comando('OK','Doação registada')

    def tratar_historico_doacoes(self):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        rows = self.repo.obter_doacoes_por_utilizador(self.utilizador.id)
        linhas = [f"{r['id']};{r['tipo_item']};{r['quantidade']};{r['valor']};{r['estado']}" for r in rows]
        return Protocolo.empacotar_comando('OK','\n'.join(linhas))

    # --- Voluntários ---
    def tratar_associar_voluntario(self, id_campanha):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        if self.utilizador.papel not in ('voluntario','admin'): return Protocolo.empacotar_comando('ERRO','Apenas voluntários podem associar-se')
        self.repo.atribuir_voluntario(self.utilizador.id,int(id_campanha))
        return Protocolo.empacotar_comando('OK','Voluntário associado')

    # --- Tarefas ---
    def tratar_listar_tarefas(self):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        if self.utilizador.papel != 'voluntario': return Protocolo.empacotar_comando('ERRO','Apenas voluntários têm tarefas')
        rows = self.repo.listar_tarefas_por_voluntario(self.utilizador.id)
        linhas = [f"{r['id']};{r['descricao']};{r['estado']}" for r in rows]
        return Protocolo.empacotar_comando('OK','\n'.join(linhas))

    def tratar_atualizar_tarefa(self, id_tarefa, estado):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        if estado not in ('pendente','em_progresso','concluida'):
            return Protocolo.empacotar_comando('ERRO','Estado inválido')
        self.repo.atualizar_estado_tarefa(int(id_tarefa),estado)
        return Protocolo.empacotar_comando('OK','Tarefa atualizada')

    # --- Relatórios ---
    def tratar_relatorio_total_por_campanha(self, id_campanha):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        row = self.repo.total_doacoes_por_campanha(int(id_campanha))
        total_valor = row.get('total_valor') or 0
        total_quant = row.get('total_quantidade') or 0
        return Protocolo.empacotar_comando('OK',f"total_valor={total_valor};total_quantidade={total_quant}")

    def tratar_contar_voluntarios(self):
        if not self.requer_autenticacao(): return Protocolo.empacotar_comando('ERRO','Autenticação necessária')
        n = self.repo.contar_voluntarios_ativos()
        return Protocolo.empacotar_comando('OK',f"voluntarios_ativos={n}")


def iniciar_servidor():
    bd = BD()
    repo = Repositorio(bd)

    # Criar admin root se não existir
    cur = bd.cursor()
    cur.execute("SELECT COUNT(*) FROM utilizadores WHERE papel='admin'")
    if cur.fetchone()[0]==0:
        cur.execute("INSERT INTO utilizadores (nome_utilizador,palavra_passe,papel,nome,contacto) VALUES ('root','1234','admin','Administrador','000')")
        bd.commit()
        print("[Servidor] Admin root criado: root/1234")
    cur.close()

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((HOST,PORT))
    s.listen(5)
    print(f"[Servidor] Escutando em {HOST}:{PORT}")
    try:
        while True:
            conn, addr = s.accept()
            print("[Servidor] Conexão de",addr)
            handler = ManipuladorCliente(conn,addr,repo)
            handler.start()
    except KeyboardInterrupt:
        print("[Servidor] Encerrado")
    finally:
        s.close()

if __name__=="__main__":
    iniciar_servidor()
