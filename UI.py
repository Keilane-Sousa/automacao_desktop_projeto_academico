from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os

class Interface:

    def __init__(self, master=None):
        self.master = master
        self.fontePadrao = ("Arial", "10")
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

        self.button2 = Button(self.terceiroContainer, text="Configurações", command=self.abrir_configuracoes, bg="#313244", fg="white")
        self.button2["font"] = ("Arial", "10")
        self.button2.pack(pady=10)

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
        Button(self.telaPasta, text="Organizar", command=lambda: self.organizar_arquivos(pasta), bg="#313244", fg="white", font=("Arial", "10")).pack(side=LEFT, padx=5, pady=5)


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

    def organizar_arquivos(self, pasta):
        #aqui e para organizar os arquivos, n sei oq vc quer fazer entao deixei para vc fazer
        print(f"Organizando arquivos em: {pasta}")

    def abrir_configuracoes(self):
        #n faço ideia do oq vc vai colocar para configurar então vou deixar para vc fazer aqui, se precisar eu posso fazer uma tela depois
        print("Abrindo configurações...")



#n mexe aqui pelo amor de Deus
ui = Tk()
ui.title("Organizador de Arquivos")
ui.config(bg="#1e1e2e")
Interface(ui)
ui.mainloop()
