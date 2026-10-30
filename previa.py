import os
from tkinter import *
from tkinter import ttk

CARACTERES_INVALIDOS = '<>:"/\\|?*'
PRIORIDADE = {"conflito": 0, "aviso": 1, "ok": 2, "semregra": 3}


def normalizar_extensoes(texto):
    # ".pdf, .docx" ou "pdf docx" -> [".pdf", ".docx"]
    partes = texto.replace(";", ",").replace(" ", ",").split(",")
    extensoes = []
    for p in partes:
        p = p.strip().lower()
        if not p:
            continue
        if not p.startswith("."):
            p = "." + p
        extensoes.append(p)
    return extensoes


def montar_plano(pasta, regras):
    mapa = {}
    for texto, destino in regras:
        for ext in normalizar_extensoes(texto):
            if destino not in mapa.setdefault(ext, []):
                mapa[ext].append(destino)

    try:
        nomes = os.listdir(pasta)
    except OSError:
        return []

    plano = []
    for nome in nomes:
        origem = os.path.join(pasta, nome)
        if not os.path.isfile(origem):
            continue   # so arquivos do primeiro nivel; subpastas são ignoradas

        ext = os.path.splitext(nome)[1].lower()
        destinos = mapa.get(ext)

        if not destinos:
            plano.append({"nome": nome, "origem": origem, "destino": "-",
                          "situacao": "semregra", "detalhe": "Nenhuma regra para esta extensão"})
            continue

        destino = destinos[0]
        caminho_destino = os.path.join(pasta, destino)
        situacao, detalhe = "ok", "Pronto para mover"

        if any(c in destino for c in CARACTERES_INVALIDOS) or destino.strip(". ") == "":
            situacao, detalhe = "conflito", "Nome de pasta inválido"
        elif os.path.isfile(caminho_destino):
            situacao, detalhe = "conflito", "Já existe um arquivo com o nome da pasta de destino"
        elif os.path.exists(os.path.join(caminho_destino, nome)):
            situacao, detalhe = "conflito", "Já existe um arquivo com este nome no destino"
        elif len(destinos) > 1:
            situacao, detalhe = "aviso", f"Extensão em várias regras ({', '.join(destinos)}); usa a primeira"
        elif not os.path.isdir(caminho_destino):
            detalhe = "Pronto (a pasta será criada)"

        plano.append({"nome": nome, "origem": origem, "destino": destino,
                      "situacao": situacao, "detalhe": detalhe,
                      "caminho_destino": os.path.join(caminho_destino, nome)})

    plano.sort(key=lambda i: (PRIORIDADE[i["situacao"]], i["nome"].lower()))
    return plano


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

        contagem = {k: sum(1 for i in plano if i["situacao"] == k) for k in PRIORIDADE}
        movem = contagem["ok"] + contagem["aviso"]

        Label(self.janela, text="Pré-visualização", bg=self.corFundo, fg="white",
              font=("Arial", 15, "bold")).pack(pady=(15, 2))
        Label(self.janela, text=pasta, bg=self.corFundo, fg="#a6adc8",
              font=("Arial", 9), wraplength=650).pack()
        Label(self.janela,
              text=f"{movem} serão movidos  •  {contagem['aviso']} avisos  •  "
                   f"{contagem['conflito']} conflitos  •  {contagem['semregra']} sem regra",
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

        # parte para ficar bonita (eu odeio essa parte)
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

        arvore.tag_configure("ok", foreground="#a6e3a1")
        arvore.tag_configure("aviso", foreground="#f9e2af")
        arvore.tag_configure("conflito", foreground="#f38ba8")
        arvore.tag_configure("semregra", foreground="#6c7086")

        for item in plano:
            arvore.insert("", END, values=(item["nome"], item["destino"], item["detalhe"]),
                          tags=(item["situacao"],))

        self.centralizar(720, 500)

    def confirmar(self):
        self.janela.destroy()
        self.ao_confirmar(self.plano)

    def centralizar(self, largura, altura):
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - largura) // 2
        y = (self.janela.winfo_screenheight() - altura) // 2
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
