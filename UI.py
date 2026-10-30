from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
import shutil
from configuracoes import telaConfig
from previa import telaPrevia, montar_plano

class Interface:

    def __init__(self, master=None):
        self.master = master
        self.fontePadrao = ("Arial", "10")
        self.corFundo = "#1e1e2e"
        self.regras = []
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

        self.preencher_arvore(arvore, "", pasta)

        Button(self.telaPasta, text="Voltar", command=self.voltar, bg="#313244", fg="white", font=("Arial", "10")). pack(side=LEFT, padx=5, pady=5)
        Button(self.telaPasta, text="Regras de Organização", command=self.abrir_configuracoes, bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5, pady=5)
        Button(self.telaPasta, text="Pré-visualizar", command=lambda: self.previsualizar(pasta), bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5, pady=5)


    def preencher_arvore(self, arvore, pai, caminho):
        #lista de tudo q tem na pasta
        try:
            itens = sorted(os.listdir(caminho), key=lambda n: (not os.path.isdir(os.path.join(caminho, n)), n.lower()))
        except PermissionError:
                arvore.insert(pai, END, text="sem permissão", values=("Pasta", ""))
                return

        for Nome in itens:
            completo = os.path.join(caminho, Nome)
            if os.path.isdir(completo):
                no = arvore.insert(pai, END, text="📁", values=("Pasta", ""))
                self.preencher_arvore(arvore, no, completo)
            else:
                try:
                    tamanho = self.formatar_tamanho(os.path.getsize(completo))
                except OSError:
                    tamanho = ""
                extensao = os.path.splitext(Nome)[1].upper().replace(".", "") or "Arquivo"
                arvore.insert(pai, END, text="📄 " + Nome, values=(extensao, tamanho))

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
        if not self.regras:
            messagebox.showwarning("Sem regras", "Defina pelo menos uma regra antes de pré-visualizar.")
            self.abrir_configuracoes()
            return
        plano = montar_plano(pasta, self.regras)
        telaPrevia(self.master, pasta, plano, lambda p: self.organizar_arquivos(pasta, p))

    def organizar_arquivos(self, pasta, plano):
        movidos = []      # (nome, destino)
        erros = []        # (nome, motivo)
        ignorados = []    # (nome, motivo) conflitos que não foram movidos
        semregra = 0

        for item in plano:
            nome = item["nome"]

            if item["situacao"] == "semregra":
                semregra += 1
                continue
            if item["situacao"] == "conflito":
                ignorados.append((nome, item["detalhe"]))
                continue

            try:
                destino_final = item["caminho_destino"]
                os.makedirs(os.path.dirname(destino_final), exist_ok=True)

                # confere de novo: o arquivo pode ter aparecido depois da pré-visualização
                if os.path.exists(destino_final):
                    ignorados.append((nome, "Já existe um arquivo com este nome no destino"))
                    continue

                shutil.move(item["origem"], destino_final)
                movidos.append((nome, item["destino"]))
            except (OSError, shutil.Error) as e:
                erros.append((nome, str(e)))

        self.mostrar_conclusao(pasta, movidos, erros, ignorados, semregra)

    def mostrar_conclusao(self, pasta, movidos, erros, ignorados, semregra):
        # apaga a tela anterior (lista de arquivos) e monta a de conclusão
        self.telaPasta.destroy()
        self.centralizar(650, 450)

        self.telaConclusao = Frame(self.master, bg=self.corFundo)
        self.telaConclusao.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # resultado final
        if erros:
            texto, cor = (f"Concluído com {len(erros)} erro(s)", "#f9e2af") if movidos else ("Falha ao organizar", "#f38ba8")
        elif not movidos:
            texto, cor = "Nenhum arquivo foi movido", "#f9e2af"
        else:
            texto, cor = "Organização concluída com sucesso!", "#a6e3a1"

        # botões embaixo primeiro, para ficarem sempre visíveis
        botoes = Frame(self.telaConclusao, bg=self.corFundo)
        botoes.pack(side=BOTTOM, pady=(10, 0))
        Button(botoes, text="Organizar outra pasta", command=self.voltar_inicio, bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5)
        Button(botoes, text="Fechar", command=self.master.destroy, bg="#313244", fg="white", font=("Arial", "10"), width=10).pack(side=LEFT, padx=5)

        Label(self.telaConclusao, text=texto, bg=self.corFundo, fg=cor, font=("Arial", 15, "bold")).pack()
        Label(self.telaConclusao, text=pasta, bg=self.corFundo, fg="#a6adc8", font=("Arial", 9), wraplength=600).pack(pady=(2, 6))
        Label(self.telaConclusao,
              text=f"{len(movidos)} movidos  •  {len(erros)} erros  •  {len(ignorados)} ignorados (conflito)  •  {semregra} sem regra",
              bg=self.corFundo, fg="white", font=("Arial", 10, "bold")).pack(pady=(0, 8))

        # lista de resultados
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

        # erros primeiro, depois ignorados, depois movidos
        for nome, motivo in erros:
            arvore.insert("", END, values=(nome, "Erro", motivo), tags=("erro",))
        for nome, motivo in ignorados:
            arvore.insert("", END, values=(nome, "Ignorado", motivo), tags=("ignorado",))
        for nome, destino in movidos:
            arvore.insert("", END, values=(nome, "Movido", f"Movido para {destino}"), tags=("movido",))

    def voltar_inicio(self):
        # apaga a tela de conclusão e traz a inicial de volta
        self.telaConclusao.destroy()
        self.centralizar(400, 150)
        self.primeiroContainer.pack()
        self.segundoContainer.pack()
        self.terceiroContainer.pack()

    def abrir_configuracoes(self):
        telaConfig(self.master, self.regras, self.salvar_regras)

    def salvar_regras(self, regras):
        self.regras = regras

    def abrir_configuracoes(self):
        telaConfig(self.master)



#n mexe aqui pelo amor de Deus
ui = Tk()
ui.title("Organizador de Arquivos")
ui.config(bg="#1e1e2e")
Interface(ui)
ui.mainloop()
