import customtkinter as ctk
from modulos.persistencia import carregar_dados, salvar_dados
from modulos.ssl_checker import verificar_ssl

# Configuração visual dark mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Equiplex SSL Guard")
        self.geometry("680x520")
        self.configure(fg_color="#121212")

        self.sites = carregar_dados()

        # --- BARRA DE CADASTRO (TOP) ---
        self.frame_top = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.frame_top.pack(pady=15, padx=15, fill="x")

        self.entry_dominio = ctk.CTkEntry(
            self.frame_top, 
            placeholder_text="Digite o domínio (ex: equiplex.com.br)", 
            height=42,
            font=("Helvetica", 13),
            border_width=1,
            corner_radius=8
        )
        self.entry_dominio.pack(side="left", padx=(12, 8), pady=12, fill="x", expand=True)

        self.btn_add = ctk.CTkButton(
            self.frame_top, 
            text="+ Monitorar", 
            height=42,
            font=("Helvetica", 13, "bold"),
            corner_radius=8,
            command=self.adicionar_site
        )
        self.btn_add.pack(side="right", padx=(0, 12), pady=12)

        # --- DASHBOARD (SITES) ---
        self.frame_lista = ctk.CTkScrollableFrame(
            self, 
            label_text="DASHBOARD DE MONITORAMENTO", 
            label_font=("Helvetica", 11, "bold"),
            fg_color="#181818",
            corner_radius=12
        )
        self.frame_lista.pack(pady=(0, 15), padx=15, fill="both", expand=True)

        self.atualizar_dashboard()

    def adicionar_site(self):
        dominio = self.entry_dominio.get().strip()
        if dominio:
            # Limpa prefixos chatos de URL se o usuário colar direto do navegador
            dominio = dominio.replace("https://", "").replace("http://", "").split('/')[0]
            
            novo_site = {"dominio": dominio}
            self.sites.append(novo_site)
            salvar_dados(self.sites)
            
            self.entry_dominio.delete(0, 'end')
            self.atualizar_dashboard()

    def remover_site(self, site):
        if site in self.sites:
            self.sites.remove(site)
            salvar_dados(self.sites)
            self.atualizar_dashboard()

    def atualizar_dashboard(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        for site in self.sites:
            dom = site['dominio']
            dias = verificar_ssl(dom)

            # Define cor da badge e do texto baseado no risco
            if dias == -999:
                cor_badge = "#555555"
                texto_status = "ERRO DE CONEXÃO"
            elif dias > 30:
                cor_badge = "#10B981" # Verde
                texto_status = f"{dias} dias (Seguro)"
            elif 7 < dias <= 30:
                cor_badge = "#F59E0B" # Amarelo / Laranja
                texto_status = f"{dias} dias (Atenção)"
            else:
                cor_badge = "#EF4444" # Vermelho
                texto_status = f"{dias} dias (CRÍTICO!)"
                self.alerta_popup(dom, dias)

            # Card da linha
            card = ctk.CTkFrame(self.frame_lista, fg_color="#242424", corner_radius=10)
            card.pack(fill="x", pady=4, padx=2)

            # Nome do domínio
            lbl_dom = ctk.CTkLabel(
                card, 
                text=f"🌐  {dom}", 
                font=("Helvetica", 13, "bold"), 
                text_color="#FFFFFF"
            )
            lbl_dom.pack(side="left", padx=15, pady=10)

            # Botão de Lixeira (Lado direito)
            btn_del = ctk.CTkButton(
                card, 
                text="🗑️", 
                width=36, 
                height=32,
                fg_color="#3A1C1C", 
                hover_color="#5C2626",
                text_color="#EF4444",
                corner_radius=6,
                command=lambda s=site: self.remover_site(s)
            )
            btn_del.pack(side="right", padx=(5, 10), pady=8)

            # Badge de Status (Pill style)
            badge = ctk.CTkLabel(
                card, 
                text=texto_status, 
                fg_color=cor_badge, 
                text_color="#FFFFFF", 
                corner_radius=6, 
                font=("Helvetica", 11, "bold"),
                width=150,
                height=30
            )
            badge.pack(side="right", padx=5, pady=8)

    def alerta_popup(self, dominio, dias):
        popup = ctk.CTkToplevel(self)
        popup.title("⚠️ ALERTA DE SSL")
        popup.geometry("320x160")
        popup.attributes("-topmost", True)
        
        msg = f"Atenção!\n\nO SSL de {dominio}\nvence em {dias} dias!"
        if dias < 0:
             msg = f"EXPIRADO!\n\nO SSL de {dominio}\nexpirou há {abs(dias)} dias!"
             
        ctk.CTkLabel(popup, text=msg, text_color="#EF4444", font=("Helvetica", 14, "bold")).pack(pady=30)

if __name__ == "__main__":
    app = App()
    app.mainloop()
    