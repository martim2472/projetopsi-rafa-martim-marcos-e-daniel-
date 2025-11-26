import struct
import socket

SEPARADOR = '|'

class Protocolo:
    @staticmethod
    def codificar(acao, dados):
        """Transforma ação e dados em bytes simples"""
        return f"{acao}|{dados}".encode('utf-8')

    @staticmethod
    def decodificar(mensagem):
        """Transforma bytes em ação e dados"""
        mensagem = mensagem.decode('utf-8')
        acao, dados = mensagem.split('|', 1)
        return acao, dados

    @staticmethod
    def enviar_mensagem(sock: socket.socket, mensagem: str):
        """Envia mensagem com prefixo de tamanho"""
        dados = mensagem.encode('utf-8')
        comprimento = struct.pack('>I', len(dados))
        sock.sendall(comprimento + dados)

    @staticmethod
    def receber_tudo(sock: socket.socket, n: int):
        """Recebe exatamente n bytes"""
        dados = b''
        while len(dados) < n:
            pacote = sock.recv(n - len(dados))
            if not pacote:
                return None
            dados += pacote
        return dados

    @staticmethod
    def receber_mensagem(sock: socket.socket):
        """Recebe uma mensagem completa"""
        cabecalho = Protocolo.receber_tudo(sock, 4)
        if not cabecalho:
            return None
        comprimento = struct.unpack('>I', cabecalho)[0]
        dados = Protocolo.receber_tudo(sock, comprimento)
        if dados is None:
            return None
        return dados.decode('utf-8')

    @staticmethod
    def escapar_campo(campo: str):
        """Escapar caracteres especiais"""
        return campo.replace('\\', '\\\\').replace(SEPARADOR, '\\' + SEPARADOR)

    @staticmethod
    def desescapar_campo(campo: str):
        """Desescapar caracteres especiais"""
        campo = campo.replace('\\\\', '\\')
        return campo.replace('\\' + SEPARADOR, SEPARADOR)

    @staticmethod
    def empacotar_comando(comando: str, *campos):
        """Empacota comando com campos escapados"""
        campos_esc = [Protocolo.escapar_campo(str(c)) for c in campos]
        if campos_esc:
            return comando + SEPARADOR + SEPARADOR.join(campos_esc)
        return comando

    @staticmethod
    def desempacotar_comando(payload: str):
        """Desempacota comando, tratando caracteres escapados"""
        partes = []
        atual = ''
        i = 0
        while i < len(payload):
            ch = payload[i]
            if ch == '\\':
                if i+1 < len(payload):
                    atual += payload[i+1]
                    i += 2
                    continue
            if ch == SEPARADOR:
                partes.append(atual)
                atual = ''
                i += 1
                continue
            atual += ch
            i += 1
        partes.append(atual)
        return partes

