import socket
from protocolo import Protocolo

HOST = '127.0.0.1'
PORTO = 5000

class MenuCliente:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORTO))
        self.logado = False
        self.papel = None
        self.user_id = None

    def enviar_acao(self, acao, *args):
        Protocolo.enviar_mensagem(self.sock, Protocolo.empacotar_comando(acao,*args))
        resposta = Protocolo.receber_mensagem(self.sock)
        if resposta is None:
            return None
        return Protocolo.desempacotar_comando(resposta)

    def login(self):
        nome = input("Nome de utilizador: ")
        passe = input("Password: ")
        res = self.enviar_acao("LOGIN", nome, passe)
        if res and res[0] == 'OK':
            self.logado = True
            self.papel = res[2]
            self.user_id = res[3]
            print(f"Login efetuado! Papel: {self.papel}, ID: {self.user_id}")
        else:
            print("Erro:", res[1] if res else "Sem resposta do servidor")

    def registar(self):
        nome = input("Nome de utilizador: ")
        passe = input("Password: ")
        papel = input("Escolha o papel (admin/voluntario/doador): ")
        res = self.enviar_acao("REGISTAR", nome, passe, papel)
        if res and res[0]=='OK':
            print(f"Registo efetuado! ID: {res[3]}, Papel: {res[2]}")
        else:
            print("Erro:", res[1] if res else "Sem resposta do servidor")

    def menu_admin(self):
        while self.logado and self.papel=='admin':
            print("\n=== MENU ADMIN ===")
            print("1 - Criar campanha")
            print("2 - Listar campanhas")
            print("3 - Encerrar campanha")
            print("4 - Adicionar utilizador")
            print("5 - Ver relatórios")
            print("0 - Logout")
            opc = input("Escolha: ")
            if opc=='1':
                titulo = input("Título da campanha: ")
                descricao = input("Descrição: ")
                res = self.enviar_acao("CRIAR_CAMPANHA", titulo, descricao)
                print(res[1])
            elif opc=='2':
                res = self.enviar_acao("LISTAR_CAMPANHAS")
                print(res[1])
            elif opc=='3':
                idc = input("ID campanha: ")
                res = self.enviar_acao("ENCERRAR_CAMPANHA", idc)
                print(res[1])
            elif opc=='4':
                self.registar()
            elif opc=='5':
                idc = input("ID campanha para relatório: ")
                res = self.enviar_acao("RELATORIO_TOTAL_POR_CAMPANHA", idc)
                print(res[1])
                res2 = self.enviar_acao("CONTAR_VOLUNTARIOS")
                print(res2[1])
            elif opc=='0':
                self.logado=False
                self.papel=None
                self.user_id=None
                print("Logout efetuado.")
            else:
                print("Opção inválida.")

    def menu_voluntario(self):
        while self.logado and self.papel=='voluntario':
            print("\n=== MENU VOLUNTÁRIO ===")
            print("1 - Listar campanhas")
            print("2 - Associar-se a campanha")
            print("3 - Ver tarefas atribuídas")
            print("4 - Atualizar estado de tarefa")
            print("0 - Logout")
            opc = input("Escolha: ")
            if opc=='1':
                res = self.enviar_acao("LISTAR_CAMPANHAS")
                print(res[1])
            elif opc=='2':
                idc = input("ID campanha: ")
                res = self.enviar_acao("ASSOCIAR_VOLUNTARIO", idc)
                print(res[1])
            elif opc=='3':
                res = self.enviar_acao("LISTAR_TAREFAS")
                print(res[1])
            elif opc=='4':
                idt = input("ID tarefa: ")
                estado = input("Novo estado (pendente/em_progresso/concluida): ")
                res = self.enviar_acao("ATUALIZAR_TAREFA", idt, estado)
                print(res[1])
            elif opc=='0':
                self.logado=False
                self.papel=None
                self.user_id=None
                print("Logout efetuado.")
            else:
                print("Opção inválida.")

    def menu_doador(self):
        while self.logado and self.papel=='doador':
            print("\n=== MENU DOADOR ===")
            print("1 - Listar campanhas")
            print("2 - Realizar doação")
            print("3 - Consultar histórico de doações")
            print("0 - Logout")
            opc = input("Escolha: ")
            if opc=='1':
                res = self.enviar_acao("LISTAR_CAMPANHAS")
                print(res[1])
            elif opc=='2':
                idc = input("ID campanha: ")
                tipo = input("Tipo item: ")
                qtd = input("Quantidade: ")
                valor = input("Valor monetário: ")
                res = self.enviar_acao("DOAR", idc, tipo, qtd, valor)
                print(res[1])
            elif opc=='3':
                res = self.enviar_acao("HISTORICO_DOACOES")
                print(res[1])
            elif opc=='0':
                self.logado=False
                self.papel=None
                self.user_id=None
                print("Logout efetuado.")
            else:
                print("Opção inválida.")

    def menu(self):
        while True:
            if not self.logado:
                print("\n=== MENU PRINCIPAL ===")
                print("1 - Login")
                print("2 - Registar")
                print("0 - Sair")
                opc = input("Escolha: ")
                if opc=='1':
                    self.login()
                elif opc=='2':
                    self.registar()
                elif opc=='0':
                    print("Adeus!")
                    break
                else:
                    print("Opção inválida.")
            else:
                if self.papel=='admin':
                    self.menu_admin()
                elif self.papel=='voluntario':
                    self.menu_voluntario()
                elif self.papel=='doador':
                    self.menu_doador()

if __name__=="__main__":
    menu = MenuCliente()
    menu.menu()
