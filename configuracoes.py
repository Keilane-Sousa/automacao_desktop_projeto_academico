from tkinter import *
from tkinter import ttk

class telaConfig:
    def __init__(self, master=None, regras=None, ao_fechar=None):
        self.ao_fechar = ao_fechar
        self.corFundo = "#1e1e2e"
        self.corCaixa = "#313244"
        self.corEntrada = "#45475a"    
        self.corBorda = "#89b4fa"
        self.fonte = ("Arial", 10)
        self.pastasSugeridas = ["Documentos", "Imagens", "Textos", "Videos", "Musicas"]
        self.regras = []  

        self.janela = Toplevel(master)
        self.janela.title("Definir Regras")
        self.janela.configure(bg=self.corFundo)
        self.janela.transient(master)
        self.janela.grab_set()

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TCombobox", fieldbackground=self.corEntrada, background=self.corCaixa,
                         foreground="white", arrowcolor="white", borderwidth=0)
        estilo.map("TCombobox", fieldbackground=[("readonly", self.corEntrada)])
        estilo.configure("Vertical.TScrollbar", background=self.corCaixa, troughcolor=self.corFundo,
                         arrowcolor="white", borderwidth=0)
        self.janela.option_add("*TCombobox*Listbox.background", self.corCaixa)
        self.janela.option_add("*TCombobox*Listbox.foreground", "white")

        Button(self.janela, text="Voltar", command=self.fechar, bg=self.corCaixa,
               fg="white", font=self.fonte, width=10).pack(side=BOTTOM, anchor=W, padx=30, pady=(5, 15))

        Button(self.janela, text="Salvar", command=self.salvarconf, bg=self.corCaixa,
               fg="white", font=self.fonte, width=10).pack(side=BOTTOM, anchor=W, padx=30, pady=(5, 15))

        Button(self.janela, text="+ Adicionar Regra", command=self.adicionar_regra,
               bg=self.corCaixa, fg="white", font=self.fonte).pack(side=BOTTOM, padx=20, pady=10, anchor=W)

        Label(self.janela, text="Definir Regras", bg=self.corFundo, fg="white",
              font=("Arial", 15, "bold")).pack(pady=(15, 2))
        Label(self.janela, text="Associe os tipos de arquivo às pastas de destino.",
              bg=self.corFundo, fg="#a6adc8", font=("Arial", 9)).pack(pady=(0, 10))

        # títulos das colunas
        cabecalho = Frame(self.janela, bg=self.corFundo)
        cabecalho.pack(padx=20, anchor=W)
        Label(cabecalho, text="Extensões", width=18, anchor=W, bg=self.corFundo, fg="#a6adc8", font=self.fonte).pack(side=LEFT)
        Label(cabecalho, text="", width=4, bg=self.corFundo).pack(side=LEFT)
        Label(cabecalho, text="Pasta de destino", width=18, anchor=W, bg=self.corFundo, fg="#a6adc8", font=self.fonte).pack(side=LEFT)

        area = Frame(self.janela, bg=self.corFundo)
        area.pack(fill=BOTH, expand=True, padx=(20, 10), pady=5)

        self.canvas = Canvas(area, bg=self.corFundo, highlightthickness=0)
        self.barra = ttk.Scrollbar(area, orient=VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.barra.set)
        self.barra.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.listaRegras = Frame(self.canvas, bg=self.corFundo)
        self.janelaCanvas = self.canvas.create_window((0, 0), window=self.listaRegras, anchor="nw")

        self.listaRegras.bind("<Configure>",
                              lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self.janelaCanvas, width=e.width))

        self.janela.bind("<MouseWheel>", self.rolar)
        self.janela.bind("<Button-4>", self.rolar)
        self.janela.bind("<Button-5>", self.rolar)

        if regras:
            for ext, pasta in regras:
                self.adicionar_regra(ext, pasta)
            else:
                self.adicionar_regra()
            self.janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self.centralizar(520, 460)

    def rolar(self, evento):

        if self.canvas.yview() == (0.0, 1.0):
            return
        if evento.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif evento.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-evento.delta / 120), "units")

    # faça sua magica
    def salvarconf(self):
        return

    def adicionar_regra(self, texto_ext="", texto_pasta=""):
        linha = Frame(self.listaRegras, bg=self.corFundo)
        linha.pack(fill=X, pady=4)

        extensao = Entry(linha, width=16, bg=self.corEntrada, fg="white",
                         insertbackground="white", relief=FLAT, font=("Arial", 11),
                         highlightthickness=1, highlightbackground=self.corBorda,
                         highlightcolor="#cdd6f4")
        extensao.pack(side=LEFT, ipady=5)
        extensao.insert(0, texto_ext)

        Label(linha, text="→", bg=self.corFundo, fg="white", font=self.fonte).pack(side=LEFT, padx=10)

        pasta = ttk.Combobox(linha, values=self.pastasSugeridas, width=18, font=self.fonte)
        pasta.pack(side=LEFT, ipady=3)
        pasta.set(texto_pasta)
        pasta.bind("<MouseWheel>", lambda e: (self.rolar(e), "break")[1])

        Button(linha, text="🗑", command=lambda: self.remover_regra(linha),
               bg=self.corCaixa, fg="#f38ba8", font=self.fonte).pack(side=LEFT, padx=(10, 0))

        self.regras.append((linha, extensao, pasta))

        if not texto_ext:
            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1)
            extensao.focus_set()

    def remover_regra(self, linha):
        self.regras = [r for r in self.regras if r[0] is not linha]
        linha.destroy()

    def obter_regras(self):
        # devolve uma lista como [(".pdf, .docx", "Documentos"), (".txt", "Textos")]
        return [(e.get().strip(), p.get().strip())
                for _, e, p in self.regras if e.get().strip() and p.get().strip()]

    def fechar(self):
        if self.ao_fechar:
            self.ao_fechar(self.obter_regras())
        self.janela.destroy()

    def centralizar(self, largura, altura):
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - largura) // 2
        y = (self.janela.winfo_screenheight() - altura) // 2
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
