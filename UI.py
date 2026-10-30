from tkinter import *
from tkinter import ttk, filedialog, messagebox
import organizador_logica as logica
from pathlib import Path
from configuracoes import telaConfig
from previa import telaPrevia, telaCarregamento

class Interface:

    def __init__(self, master=None):
        self.master = master
        self.pasta_principal = None
        self.regras = {}
        self.pendentes = {}
        self.corFundo = "#1e1e2e"
# aqui e os containers n acho q seja nessesario mexer
        self.primeiroContainer = Frame(master, bg=self.corFundo)
        self.primeiroContainer["pady"] = 10
        self.primeiroContainer.pack()

        self.segundoContainer = Frame(master, bg=self.corFundo)
        self.segundoContainer["padx"] = 20
        self.segundoContainer.pack()

        self.terceiroContainer = Frame(master, bg=self.corFundo)
        self.terceiroContainer["padx"] = 20
        self.terceiroContainer.pack()

#aqui e onde funciona os botões e labels, pode mexer
        self.titulo = Label(self.primeiroContainer, text="Organizador de Arquivos", bg=self.corFundo, fg="white")
        self.titulo["font"] = ("Arial", "15", "bold")
        self.titulo.pack()

        self.button = Button(self.segundoContainer, text="Selecionar Pasta", command=self.selecionar_pasta, bg="#313244", fg="white")
        self.button["font"] = ("Arial", "10")
        self.button.pack(pady=10)

        self.creditos = Label(self.terceiroContainer, text="Desenvolvido por Ygor, Matheus, Keilane, Allan e Max", bg=self.corFundo, fg="white")
        self.creditos["font"] = ("Arial", "8")
        self.creditos.pack(pady=10)

        self.centralizar(400, 150)

    def centralizar(self, largura, altura):
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() - largura) // 2
        y = (self.master.winfo_screenheight() - altura) // 2
        self.master.geometry(f"{largura}x{altura}+{x}+{y}")

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione uma pasta")
        if pasta:
            self.processar_pasta(pasta)

    def processar_pasta(self, pasta):
        try:
            logica.listar_arquivos(pasta)
            logica.listar_subpastas(pasta)
        except (OSError, ValueError) as erro:
            messagebox.showerror("Selecionar pasta", str(erro), parent=self.master)
            return
        self.pasta_principal = pasta
        self.regras.clear()
        self.pendentes.clear()
        #aqui e para esconder a tela, n vejo motivos para mexer aqui
        for container in (self.primeiroContainer, self.segundoContainer, self.terceiroContainer):
            container.pack_forget()

        self.centralizar(650, 400)

        #aqui e a nova tela, pode conter coisas q vc queira usar
        self.telaPasta = Frame(self.master, bg=self.corFundo)
        self.telaPasta.pack(fill=BOTH, expand=True, padx=20, pady=20)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", background="#313244", fieldbackground="#313244", foreground="white", rowheight=25, borderwidth=0)
        estilo.configure("Treeview.Heading", background="#45475a", foreground="white")
        estilo.map("Treeview", background=[("selected", "#89b4fa")], foreground=[("selected", "black")])

        #aqui e a lista de arquivos
        areaLista = Frame(self.telaPasta, bg=self.corFundo)
        areaLista.pack(fill=BOTH, expand=True)

        arvore = ttk.Treeview(areaLista, columns=("tipo", "tamanho"))
        arvore.heading("#0", text="Nome", anchor=W)
        arvore.heading("tipo", text="Tipo", anchor=W)
        arvore.heading("tamanho", text="Tamanho", anchor=W)
        arvore.column("#0", width=350)
        arvore.column("tipo", width=100)
        arvore.column("tamanho", width=100)

        barra = ttk.Scrollbar(areaLista, orient=VERTICAL, command=arvore.yview)
        arvore.configure(yscrollcommand=barra.set)
        barra.pack(side=RIGHT, fill=Y)
        arvore.pack(side=LEFT, fill=BOTH, expand=True)

        self.arvore = arvore
        self.preencher_arvore(arvore, "", pasta)

        Button(self.telaPasta, text="Voltar", command=self.voltar, bg="#313244", fg="white", font=("Arial", "10")). pack(side=LEFT, padx=5, pady=5)
        Button(self.telaPasta, text="Regras de Organização", command=self.abrir_configuracoes, bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5, pady=5)
        Button(self.telaPasta, text="Pré-visualizar", command=lambda: self.previsualizar(pasta), bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5, pady=5)


    def preencher_arvore(self, arvore, pai, caminho):
        caminho = Path(caminho)
        try:
            if caminho.is_symlink() or caminho.is_junction():
                return
            itens = sorted(caminho.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as erro:
            arvore.insert(pai, END, text=f"Erro ao listar: {erro}", values=("Erro", ""))
            return

        for arquivo in itens:
            try:
                if arquivo.is_symlink() or arquivo.is_junction():
                    continue
                if arquivo.is_dir():
                    no = arvore.insert(pai, END, text="📁 " + arquivo.name, values=("Pasta", ""))
                    self.preencher_arvore(arvore, no, arquivo)
                else:
                    tamanho = self.formatar_tamanho(arquivo.stat().st_size)
                    extensao = arquivo.suffix.upper().lstrip(".") or "Arquivo"
                    arvore.insert(pai, END, text="📄 " + arquivo.name, values=(extensao, tamanho))
            except OSError as erro:
                arvore.insert(pai, END, text=f"{arquivo.name}: {erro}", values=("Erro", ""))

    def formatar_tamanho(self, bytes_):
        for unidade in ("B", "KB", "MB", "GB", "TB"):
            if bytes_ < 1024:
                return f"{bytes_:.0f} {unidade}" if unidade == "B" else f"{bytes_:.1f} {unidade}"
            bytes_ /= 1024
        return f"{bytes_:.1f} TB"

    def voltar(self):
        self.telaPasta.destroy()
        self.centralizar(400, 250)
        self.primeiroContainer.pack()
        self.segundoContainer.pack()
        self.terceiroContainer.pack()

    def previsualizar(self, pasta):
        try:
            plano = logica.gerar_previsualizacao(pasta, self.regras, self.pendentes)
            self.previa = telaPrevia(self.master, pasta, plano,
                                     lambda p: self.organizar_arquivos(pasta, p))
        except (OSError, ValueError) as erro:
            messagebox.showerror("Pré-visualização", str(erro), parent=self.master)

    def organizar_arquivos(self, pasta, plano=None):
        if plano is None:
            self.previsualizar(pasta)
            return
        if getattr(self, 'carregamento', None) and self.carregamento.janela.winfo_exists():
            return
        self.carregamento = telaCarregamento(
            self.master, plano, lambda resultado: self.finalizar_organizacao(pasta, resultado),
            lambda erro: messagebox.showerror("Organização", str(erro), parent=self.master)
        )

    def finalizar_organizacao(self, pasta, resultado):
        self.resultado = resultado
        itens = resultado['itens']
        movidos = [(i['arquivo'], i['destino']) for i in itens if i['status'] == 'movido']
        erros = [(i['arquivo'], i['mensagem']) for i in itens if i['status'] == 'erro']
        conflitos = [(i['arquivo'], i['mensagem']) for i in itens if i['status'] == 'conflito']
        self.mostrar_conclusao(pasta, movidos, erros, conflitos, resultado['resumo']['sem_regra'])

    def mostrar_conclusao(self, pasta, movidos, erros, ignorados, semregra):
        self.telaPasta.destroy()
        self.centralizar(650, 450)

        self.telaConclusao = Frame(self.master, bg=self.corFundo)
        self.telaConclusao.pack(fill=BOTH, expand=True, padx=20, pady=20)

        if erros:
            texto, cor = (f"Concluído com {len(erros)} erro(s)", "#f9e2af") if movidos else ("Falha ao organizar", "#f38ba8")
        elif ignorados:
            texto = (f"Concluído com {len(ignorados)} conflito(s)" if movidos
                     else "Nenhum arquivo movido: há conflitos")
            cor = "#f9e2af"
        elif not movidos:
            texto, cor = "Nenhum arquivo foi movido", "#f9e2af"
        else:
            texto, cor = "Organização concluída com sucesso!", "#a6e3a1"

        botoes = Frame(self.telaConclusao, bg=self.corFundo)
        botoes.pack(side=BOTTOM, pady=(10, 0))
        Button(botoes, text="Organizar outra pasta", command=self.voltar_inicio, bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5)
        Button(botoes, text="Fechar", command=self.master.destroy, bg="#313244", fg="white", font=("Arial", "10"), width=10).pack(side=LEFT, padx=5)

        Label(self.telaConclusao, text=texto, bg=self.corFundo, fg=cor, font=("Arial", 15, "bold")).pack()
        Label(self.telaConclusao, text=pasta, bg=self.corFundo, fg="#a6adc8", font=("Arial", 9), wraplength=600).pack(pady=(2, 6))
        Label(self.telaConclusao,
              text=f"{len(movidos)} movidos  •  {len(erros)} erros  •  {len(ignorados)} ignorados (conflito)  •  {semregra} sem regra",
              bg=self.corFundo, fg="white", font=("Arial", 10, "bold")).pack(pady=(0, 8))

        area = Frame(self.telaConclusao, bg=self.corFundo)
        area.pack(fill=BOTH, expand=True)

        estilo = ttk.Style()
        estilo.configure("Treeview", background="#313244", fieldbackground="#313244", foreground="white", rowheight=25, borderwidth=0)

        arvore = ttk.Treeview(area, columns=("arquivo", "resultado", "detalhe"), show="headings")
        arvore.heading("arquivo", text="Arquivo", anchor=W)
        arvore.heading("resultado", text="Resultado", anchor=W)
        arvore.heading("detalhe", text="Detalhe", anchor=W)
        arvore.column("arquivo", width=220)
        arvore.column("resultado", width=90)
        arvore.column("detalhe", width=280)

        barra = ttk.Scrollbar(area, orient=VERTICAL, command=arvore.yview)
        arvore.configure(yscrollcommand=barra.set)
        barra.pack(side=RIGHT, fill=Y)
        arvore.pack(side=LEFT, fill=BOTH, expand=True)

        arvore.tag_configure("erro", foreground="#f38ba8")
        arvore.tag_configure("ignorado", foreground="#f9e2af")
        arvore.tag_configure("movido", foreground="#a6e3a1")

        for nome, motivo in erros:
            arvore.insert("", END, values=(nome, "Erro", motivo), tags=("erro",))
        for nome, motivo in ignorados:
            arvore.insert("", END, values=(nome, "Ignorado", motivo), tags=("ignorado",))
        for nome, destino in movidos:
            arvore.insert("", END, values=(nome, "Movido", f"Movido para {destino}"), tags=("movido",))

    def voltar_inicio(self):
        self.pasta_principal = None
        self.regras.clear()
        self.pendentes.clear()
        self.telaConclusao.destroy()
        self.centralizar(400, 150)
        self.primeiroContainer.pack()
        self.segundoContainer.pack()
        self.terceiroContainer.pack()


    def abrir_configuracoes(self):
        try:
            telaConfig(self.master, self.pasta_principal, self.regras, self.pendentes)
        except (OSError, ValueError) as erro:
            messagebox.showerror("Configuração", str(erro), parent=self.master)


if __name__ == '__main__':
    ui = Tk()
    ui.title("Organizador de Arquivos")
    ui.config(bg="#1e1e2e")
    Interface(ui)
    ui.mainloop()
