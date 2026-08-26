import customtkinter as ctk
from modulos.persistencia import carregar_dados, salvar_dados
from modulos.ssl_checker import verificar_ssl

# Configuração básica do CTk pra ficar pique dark mode bolado[cite: 3]
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Equiplex SSL Guard")
        self.geometry("700x500")
        
        # Carrega os dados do JSON[cite: 3]
        self.sites = carregar_dados()

        # --- ÁREA DE CADASTRO ---
        self.frame_cadastro = ctk.CTkFrame(self)
        self.frame_cadastro.pack(pady=10, padx=10, fill="x")

        # Entradas exigidas no escopo[cite: 1]
        self.entry_dominio = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Domínio (ex: equiplex.com.br)", width=200)
        self.entry_dominio.pack(side="left", padx=5)
        
        self.entry_categoria = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Categoria", width=120)
        self.entry_categoria.pack(side="left", padx=5)

        self.entry_email = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Email do TI", width=150)
        self.entry_email.pack(side="left", padx=5)

        self.btn_add = ctk.CTkButton(self.frame_cadastro, text="Monitorar", command=self.adicionar_site)
        self.btn_add.pack(side="left", padx=5)

        # --- DASHBOARD ---
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Dashboard de SSL")
        self.frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        self.atualizar_dashboard()

    def adicionar_site(self):
        dominio = self.entry_dominio.get()
        categoria = self.entry_categoria.get()
        email = self.entry_email.get()

        if dominio and email: # Validação básica pra não bugar
            novo_site = {"dominio": dominio, "categoria": categoria, "email": email}
            self.sites.append(novo_site)
            salvar_dados(self.sites)
            
            # Limpa os campos
            self.entry_dominio.delete(0, 'end')
            self.entry_categoria.delete(0, 'end')
            self.entry_email.delete(0, 'end')
            
            self.atualizar_dashboard()

    def atualizar_dashboard(self):
        # Limpa o frame antes de atualizar
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        for site in self.sites:
            dias = verificar_ssl(site['dominio'])
            
            # Classificação de Risco (Verde/Amarelo/Vermelho)[cite: 1]
            if dias == -999:
                cor = "gray"
                status = "ERRO DE CONEXÃO"
            elif dias > 30:
                cor = "green"
                status = f"{dias} dias (Seguro)"
            elif 7 < dias <= 30:
                cor = "#D4AC0D" # Amarelo escuro pra não cegar a gente
                status = f"{dias} dias (Atenção)"
            else:
                cor = "red"
                status = f"{dias} dias (CRÍTICO!)"
                self.alerta_popup(site['dominio'], dias) # Dispara o alerta[cite: 1]

            # Cria um cardzinho pra cada site
            card = ctk.CTkLabel(self.frame_lista, text=f"🌐 {site['dominio']} | {site['categoria']} | TI: {site['email']} | STATUS: {status}", 
                                fg_color=cor, text_color="white", corner_radius=8, pady=5)
            card.pack(fill="x", pady=2)

    def alerta_popup(self, dominio, dias):
        # Janela de popup sinistra se o bagulho tiver expirando[cite: 1]
        popup = ctk.CTkToplevel(self)
        popup.title("⚠️ ALERTA DE SSL")
        popup.geometry("300x150")
        popup.attributes("-topmost", True) # Fica na frente de tudo
        
        msg = f"Corre pro abraço, mermão!\n\nO SSL de {dominio}\nvence em {dias} dias!"
        if dias < 0:
             msg = f"DEU MERDA!\n\nO SSL de {dominio}\nexpirou há {abs(dias)} dias!"
             
        ctk.CTkLabel(popup, text=msg, text_color="red", font=("Arial", 16, "bold")).pack(pady=30)

if __name__ == "__main__":
    app = App()
    app.mainloop()








