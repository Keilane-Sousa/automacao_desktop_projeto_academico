from tkinter import *
from tkinter import ttk
from queue import Empty, Queue
from threading import Thread
import organizador_logica as logica

PRIORIDADE = {"conflito": 0, "erro": 1, "previsto": 2, "sem_regra": 3}


class telaPrevia:
    def __init__(self, master, pasta, plano, ao_confirmar):
        self.corFundo = "#1e1e2e"
        self.corCaixa = "#313244"
        self.plano = plano
        self.ao_confirmar = ao_confirmar

        self.janela = Toplevel(master)
        self.janela.title("Pré-visualização")
        self.janela.configure(bg=self.corFundo)
        self.janela.transient(master)
        self.janela.grab_set()

        contagem = logica.resumir_resultados(plano["itens"])
        movem = contagem["previsto"]

        Label(self.janela, text="Pré-visualização", bg=self.corFundo, fg="white",
              font=("Arial", 15, "bold")).pack(pady=(15, 2))
        Label(self.janela, text=pasta, bg=self.corFundo, fg="#a6adc8",
              font=("Arial", 9), wraplength=650).pack()
        Label(self.janela,
              text=f"{movem} serão movidos  •  {contagem['erro']} erros  •  "
                   f"{contagem['conflito']} conflitos  •  {contagem['sem_regra']} sem regra",
              bg=self.corFundo, fg="white", font=("Arial", 10, "bold")).pack(pady=8)

        botoes = Frame(self.janela, bg=self.corFundo)
        botoes.pack(side=BOTTOM, pady=12)
        Button(botoes, text="Voltar", command=self.janela.destroy, bg=self.corCaixa,
               fg="white", font=("Arial", 10), width=10).pack(side=LEFT, padx=5)
        self.botaoOrganizar = Button(botoes, text="Organizar", command=self.confirmar,
                                     bg="#89b4fa", fg="black", font=("Arial", 10), width=10,
                                     state=NORMAL if movem else DISABLED)
        self.botaoOrganizar.pack(side=LEFT, padx=5)

        if contagem["conflito"]:
            Label(self.janela, text="Arquivos com conflito serão ignorados.",
                  bg=self.corFundo, fg="#f38ba8", font=("Arial", 9)).pack(side=BOTTOM)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", background=self.corCaixa, fieldbackground=self.corCaixa,
                         foreground="white", rowheight=25, borderwidth=0)
        estilo.configure("Treeview.Heading", background="#45475a", foreground="white")
        estilo.map("Treeview", background=[("selected", "#89b4fa")], foreground=[("selected", "black")])

        area = Frame(self.janela, bg=self.corFundo)
        area.pack(fill=BOTH, expand=True, padx=20, pady=5)

        arvore = ttk.Treeview(area, columns=("arquivo", "destino", "situacao"), show="headings")
        arvore.heading("arquivo", text="Arquivo", anchor=W)
        arvore.heading("destino", text="Destino", anchor=W)
        arvore.heading("situacao", text="Situação", anchor=W)
        arvore.column("arquivo", width=220)
        arvore.column("destino", width=120)
        arvore.column("situacao", width=300)

        barra = ttk.Scrollbar(area, orient=VERTICAL, command=arvore.yview)
        arvore.configure(yscrollcommand=barra.set)
        barra.pack(side=RIGHT, fill=Y)
        arvore.pack(side=LEFT, fill=BOTH, expand=True)

        arvore.tag_configure("previsto", foreground="#a6e3a1")
        arvore.tag_configure("erro", foreground="#f9e2af")
        arvore.tag_configure("conflito", foreground="#f38ba8")
        arvore.tag_configure("sem_regra", foreground="#6c7086")

        self.arvore = arvore
        for item in sorted(plano["itens"], key=lambda i: (PRIORIDADE[i["status"]], i["arquivo"].lower())):
            arvore.insert("", END, values=(item["arquivo"], item["destino"] or "—", item["mensagem"]),
                          tags=(item["status"],))

        self.centralizar(720, 500)

    def confirmar(self):
        self.botaoOrganizar.configure(state=DISABLED)
        self.confirmacao = telaConfirmacao(self.janela, self.plano, self.executar, self.voltar_previa)

    def voltar_previa(self):
        self.botaoOrganizar.configure(state=NORMAL)
        self.janela.grab_set()

    def executar(self):
        self.janela.destroy()
        self.ao_confirmar(self.plano)

    def centralizar(self, largura, altura):
        centralizar_janela(self.janela, largura, altura)


def centralizar_janela(janela, largura, altura):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - largura) // 2
    y = (janela.winfo_screenheight() - altura) // 2
    janela.geometry(f"{largura}x{altura}+{x}+{y}")


class telaConfirmacao:
    def __init__(self, master, plano, ao_confirmar, ao_cancelar):
        self.janela = Toplevel(master)
        self.janela.title("Confirmar organização")
        self.janela.configure(bg="#1e1e2e")
        self.janela.resizable(False, False)
        self.janela.transient(master)
        self.janela.grab_set()
        Label(self.janela, text="Confirmar organização", bg="#1e1e2e", fg="white",
              font=("Arial", 16, "bold")).pack(anchor=W, padx=24, pady=(22, 6))
        Label(self.janela, text="Confira a prévia antes de continuar.", bg="#1e1e2e",
              fg="#a6adc8", font=("Arial", 10)).pack(anchor=W, padx=24)
        resumo = logica.resumir_resultados(plano['itens'])
        cartao = Frame(self.janela, bg="#313244", padx=16, pady=14)
        cartao.pack(fill=X, padx=24, pady=16)
        Label(cartao, text=f"{resumo['previsto']} arquivo(s) serão movidos", bg="#313244",
              fg="#89b4fa", font=("Arial", 13, "bold")).pack(anchor=W)
        Label(cartao, text=plano['pasta_principal'], bg="#313244", fg="white",
              font=("Arial", 9), wraplength=440, justify=LEFT).pack(anchor=W, pady=(6, 0))
        Label(self.janela, text="Arquivos com conflito ou erro serão mantidos onde estão.",
              bg="#1e1e2e", fg="#a6adc8", font=("Arial", 9)).pack(anchor=W, padx=24)
        botoes = Frame(self.janela, bg="#1e1e2e")
        botoes.pack(side=BOTTOM, fill=X, padx=24, pady=20)

        def cancelar():
            self.janela.destroy()
            ao_cancelar()

        def confirmar():
            self.botaoConfirmar.configure(state=DISABLED)
            self.janela.destroy()
            ao_confirmar()

        self.botaoVoltar = Button(botoes, text="Voltar à prévia", command=cancelar,
                                  bg="#313244", fg="white", font=("Arial", 10), relief=FLAT,
                                  padx=12, pady=8)
        self.botaoVoltar.pack(side=LEFT)
        self.botaoConfirmar = Button(botoes, text="Confirmar e organizar", command=confirmar,
                                     bg="#89b4fa", fg="#1e1e2e", font=("Arial", 10, "bold"),
                                     activebackground="#b4befe", relief=FLAT, padx=12, pady=8)
        self.botaoConfirmar.pack(side=RIGHT)
        self.janela.protocol("WM_DELETE_WINDOW", cancelar)
        self.janela.bind('<Escape>', lambda evento: cancelar())
        centralizar_janela(self.janela, 540, 330)


class telaCarregamento:
    def __init__(self, master, plano, ao_concluir, ao_erro):
        self.master = master
        self.plano = plano
        self.ao_concluir = ao_concluir
        self.ao_erro = ao_erro
        self.fila = Queue(maxsize=1)
        self.janela = Toplevel(master)
        self.janela.title("Organizando arquivos")
        self.janela.configure(bg="#1e1e2e")
        self.janela.resizable(False, False)
        self.janela.transient(master)
        self.janela.grab_set()
        self.janela.protocol("WM_DELETE_WINDOW", lambda: None)
        self.fechar_anterior = master.protocol("WM_DELETE_WINDOW")
        master.protocol("WM_DELETE_WINDOW", lambda: None)
        Label(self.janela, text="Organizando seus arquivos", bg="#1e1e2e", fg="white",
              font=("Arial", 16, "bold")).pack(pady=(28, 10))
        Label(self.janela, text="Aguarde enquanto as movimentações são concluídas.",
              bg="#1e1e2e", fg="#a6adc8", font=("Arial", 10)).pack()
        estilo = ttk.Style(self.janela)
        estilo.configure('Organizador.Horizontal.TProgressbar', background='#89b4fa',
                         troughcolor='#313244', borderwidth=0, thickness=8)
        self.barra = ttk.Progressbar(self.janela, mode='indeterminate',
                                     style='Organizador.Horizontal.TProgressbar')
        self.barra.pack(fill=X, padx=32, pady=22)
        self.barra.start(12)
        Label(self.janela, text=plano['pasta_principal'], bg="#1e1e2e", fg="#a6adc8",
              font=("Arial", 9), wraplength=440, justify=CENTER).pack(padx=24)
        centralizar_janela(self.janela, 500, 240)
        Thread(target=self.executar, daemon=True).start()
        self.janela.after(50, self.verificar)

    def executar(self):
        try:
            self.fila.put((logica.executar_movimentacoes(self.plano), None))
        except Exception as erro:
            self.fila.put((None, erro))

    def verificar(self):
        try:
            resultado, erro = self.fila.get_nowait()
        except Empty:
            self.janela.after(50, self.verificar)
            return
        self.barra.stop()
        self.master.protocol("WM_DELETE_WINDOW", self.fechar_anterior)
        self.janela.destroy()
        if erro is not None:
            self.ao_erro(erro)
        else:
            self.ao_concluir(resultado)
