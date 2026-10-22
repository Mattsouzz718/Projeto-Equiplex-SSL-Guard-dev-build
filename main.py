import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import customtkinter as ctk

from modulos.notificacoes import enviar_notificacao_windows
from modulos.persistencia import carregar_dados, salvar_dados
from modulos.ssl_checker import normalizar_dominio, verificar_dominio


# Varreduras periódicas: o app permanece ativo na bandeja do sistema ao fechar.
INTERVALO_MONITORAMENTO = 15 * 60  # segundos
DIAS_ALERTA_VENCIMENTO = 7
PASTA_PROJETO = Path(__file__).resolve().parent

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Equiplex SSL Guard")
        self.geometry("900x640")
        self.minsize(760, 540)
        self.configure(fg_color="#121212")

        self.sites = carregar_dados()
        # Preserva compatibilidade com o formato antigo, só com o domínio.
        self.sites = [
            site for site in self.sites
            if isinstance(site, dict) and normalizar_dominio(site.get("dominio", ""))
        ]
        for site in self.sites:
            site["dominio"] = normalizar_dominio(site["dominio"])
            site.setdefault("ultimo_alerta", None)

        self.resultados = {}
        self.fila_resultados = queue.Queue()
        self.lock_sites = threading.Lock()
        self.parar_monitoramento = threading.Event()
        self.solicitar_verificacao = threading.Event()
        self.thread_monitor = None
        self.tray_icon = None
        self.tray_disponivel = False
        self.encerrando = False
        self.alertas_visuais = []

        self.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)

        # Barra de cadastro e ações.
        self.frame_top = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.frame_top.pack(pady=(14, 10), padx=14, fill="x")

        self.entry_dominio = ctk.CTkEntry(
            self.frame_top,
            placeholder_text="Domínio ou URL (ex.: equiplex.com.br)",
            height=42,
            font=("Segoe UI", 13),
            border_width=1,
            corner_radius=8,
        )
        self.entry_dominio.pack(side="left", padx=(12, 8), pady=12, fill="x", expand=True)
        self.entry_dominio.bind("<Return>", lambda _event: self.adicionar_site())

        self.btn_add = ctk.CTkButton(
            self.frame_top,
            text="+ Monitorar",
            height=42,
            width=125,
            font=("Segoe UI", 13, "bold"),
            corner_radius=8,
            command=self.adicionar_site,
        )
        self.btn_add.pack(side="left", padx=(0, 8), pady=12)

        self.btn_verificar = ctk.CTkButton(
            self.frame_top,
            text="↻ Verificar agora",
            height=42,
            width=145,
            fg_color="#303C55",
            hover_color="#3A4D70",
            font=("Segoe UI", 12, "bold"),
            corner_radius=8,
            command=self.verificar_agora,
        )
        self.btn_verificar.pack(side="right", padx=(0, 12), pady=12)

        # Aviso persistente do estado do monitoramento.
        self.lbl_monitor = ctk.CTkLabel(
            self,
            text="● Preparando monitoramento automático...",
            text_color="#A7B5CC",
            font=("Segoe UI", 11),
            anchor="w",
        )
        self.lbl_monitor.pack(fill="x", padx=20, pady=(0, 9))

        self.frame_lista = ctk.CTkScrollableFrame(
            self,
            label_text="DASHBOARD DE MONITORAMENTO",
            label_font=("Segoe UI", 11, "bold"),
            fg_color="#181818",
            corner_radius=12,
        )
        self.frame_lista.pack(pady=(0, 14), padx=14, fill="both", expand=True)

        self.atualizar_dashboard()
        self._configurar_bandeja()
        self.after(250, self._iniciar_monitoramento)
        self.after(400, self._processar_fila_resultados)

    def adicionar_site(self):
        dominio = normalizar_dominio(self.entry_dominio.get())
        if not dominio:
            self.lbl_monitor.configure(text="Digite um domínio válido para começar.", text_color="#F59E0B")
            return

        with self.lock_sites:
            if any(site["dominio"].lower() == dominio.lower() for site in self.sites):
                self.lbl_monitor.configure(text=f"{dominio} já está na lista de monitoramento.", text_color="#F59E0B")
                return
            self.sites.append({"dominio": dominio, "ultimo_alerta": None})
            salvar_dados(self.sites)

        self.entry_dominio.delete(0, "end")
        self.atualizar_dashboard()
        self.lbl_monitor.configure(text=f"{dominio} adicionado. Consultando certificado e localização...", text_color="#A7B5CC")
        self.verificar_agora()

    def remover_site(self, site):
        with self.lock_sites:
            if site in self.sites:
                self.sites.remove(site)
                salvar_dados(self.sites)
        self.resultados.pop(site["dominio"], None)
        self.atualizar_dashboard()

    def _iniciar_monitoramento(self):
        if self.encerrando:
            return
        if self.thread_monitor and self.thread_monitor.is_alive():
            return
        self.thread_monitor = threading.Thread(
            target=self._rotina_monitoramento,
            name="EquiplexSSLMonitor",
            daemon=True,
        )
        self.thread_monitor.start()
        self.lbl_monitor.configure(
            text="● Monitoramento ativo: verificação a cada 15 minutos. Fechar a janela envia o app para a bandeja.",
            text_color="#10B981",
        )

    def _rotina_monitoramento(self):
        """Executa toda a rede fora da thread gráfica para não travar a interface."""
        while not self.parar_monitoramento.is_set():
            with self.lock_sites:
                dominios = [site["dominio"] for site in self.sites]

            for dominio in dominios:
                if self.parar_monitoramento.is_set():
                    break
                try:
                    resultado = verificar_dominio(dominio)
                except Exception as erro:
                    # Uma falha inesperada em um domínio não encerra o monitor.
                    resultado = {
                        "dominio": dominio,
                        "dias": -999,
                        "expiracao": None,
                        "ip": None,
                        "cidade": None,
                        "regiao": None,
                        "pais": None,
                        "provedor": None,
                        "erro": f"Falha inesperada na consulta: {erro}",
                    }
                self.fila_resultados.put((dominio, resultado))

            # Um clique em Verificar agora acorda o monitor antes dos 15 minutos.
            proxima_varredura = time.monotonic() + INTERVALO_MONITORAMENTO
            while not self.parar_monitoramento.is_set():
                restante = proxima_varredura - time.monotonic()
                if restante <= 0:
                    break
                if self.solicitar_verificacao.wait(timeout=min(1, restante)):
                    self.solicitar_verificacao.clear()
                    break

    def verificar_agora(self):
        if self.thread_monitor and self.thread_monitor.is_alive():
            self.solicitar_verificacao.set()
            self.lbl_monitor.configure(text="Verificação solicitada. Ela será executada pelo monitor em segundo plano...", text_color="#A7B5CC")
        else:
            self._iniciar_monitoramento()

    def _processar_fila_resultados(self):
        alterou = False
        while True:
            try:
                dominio, resultado = self.fila_resultados.get_nowait()
            except queue.Empty:
                break

            self.resultados[dominio] = resultado
            alterou = True
            self._avaliar_alerta(dominio, resultado)

        if alterou:
            self.atualizar_dashboard()
            self.lbl_monitor.configure(
                text=f"● Monitoramento ativo • Última atualização: {datetime.now().strftime('%H:%M:%S')} • Próxima varredura automática em até 15 min.",
                text_color="#10B981",
            )

        if not self.encerrando:
            self.after(400, self._processar_fila_resultados)

    def _avaliar_alerta(self, dominio, resultado):
        dias = resultado.get("dias", -999)
        if dias == -999:
            return

        if dias < 0:
            etapa = "expirado"
        elif dias <= DIAS_ALERTA_VENCIMENTO:
            etapa = "proximo"
        else:
            etapa = None

        with self.lock_sites:
            site = next((s for s in self.sites if s["dominio"] == dominio), None)
            if site is None:
                return
            etapa_anterior = site.get("ultimo_alerta")
            if etapa is None:
                if etapa_anterior is not None:
                    site["ultimo_alerta"] = None
                    salvar_dados(self.sites)
                return
            if etapa == etapa_anterior:
                return
            site["ultimo_alerta"] = etapa
            salvar_dados(self.sites)

        expiracao = resultado.get("expiracao")
        data_texto = (
            expiracao.strftime("%d/%m/%Y %H:%M UTC")
            if expiracao else "data não disponível"
        )
        if etapa == "expirado":
            titulo = "🔴 CERTIFICADO SSL EXPIRADO"
            mensagem = f"{dominio}: o certificado venceu em {data_texto}. Renove-o o quanto antes."
        else:
            titulo = "⚠️ CERTIFICADO SSL PRÓXIMO DO VENCIMENTO"
            mensagem = f"{dominio}: restam {dias} dia(s). Vencimento: {data_texto}."

        # A aparência da notificação nativa é controlada pelo Windows.
        enviar_notificacao_windows(titulo, mensagem)

    def atualizar_dashboard(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        with self.lock_sites:
            sites = [dict(site) for site in self.sites]

        if not sites:
            ctk.CTkLabel(
                self.frame_lista,
                text="Nenhum domínio monitorado ainda. Adicione um site acima.",
                text_color="#8B8B8B",
                font=("Segoe UI", 13),
            ).pack(pady=30)
            return

        for site in sites:
            dominio = site["dominio"]
            resultado = self.resultados.get(dominio)
            dias = resultado.get("dias", -999) if resultado else None

            if resultado is None:
                cor_badge, texto_status = "#555555", "VERIFICANDO..."
            elif dias == -999:
                cor_badge, texto_status = "#555555", "ERRO DE CONEXÃO"
            elif dias < 0:
                cor_badge, texto_status = "#EF4444", f"EXPIRADO há {abs(dias)}d"
            elif dias <= DIAS_ALERTA_VENCIMENTO:
                cor_badge, texto_status = "#EF4444", f"Vence em {dias}d"
            elif dias <= 30:
                cor_badge, texto_status = "#F59E0B", f"Atenção • {dias}d"
            else:
                cor_badge, texto_status = "#10B981", f"Prazo OK • {dias}d"

            card = ctk.CTkFrame(self.frame_lista, fg_color="#242424", corner_radius=10)
            card.pack(fill="x", pady=4, padx=2)

            frame_info = ctk.CTkFrame(card, fg_color="transparent")
            frame_info.pack(side="left", fill="x", expand=True, padx=(13, 4), pady=8)

            ctk.CTkLabel(
                frame_info,
                text=f"🌐  {dominio}",
                font=("Segoe UI", 13, "bold"),
                text_color="#FFFFFF",
                anchor="w",
            ).pack(fill="x")

            if resultado is None:
                detalhes = "Consultando certificado, IP e localização aproximada..."
            elif resultado.get("erro") and dias == -999:
                detalhes = f"{resultado['erro'][:105]}"
            else:
                ip = resultado.get("ip") or "IP indisponível"
                cidade = resultado.get("cidade")
                regiao = resultado.get("regiao")
                pais = resultado.get("pais")
                lugar = ", ".join(str(p) for p in (cidade, regiao, pais) if p) or "Localização indisponível"
                provedor = resultado.get("provedor") or "Provedor desconhecido"
                detalhes = f"IP: {ip}  •  Localização estimada: {lugar}  •  {provedor}"
                expiracao = resultado.get("expiracao")
                if expiracao:
                    detalhes += f"  •  Vence: {expiracao.strftime('%d/%m/%Y')} UTC"

            ctk.CTkLabel(
                frame_info,
                text=detalhes,
                font=("Segoe UI", 10),
                text_color="#A7A7A7",
                anchor="w",
                justify="left",
                wraplength=510,
            ).pack(fill="x", pady=(3, 0))

            badge = ctk.CTkLabel(
                card,
                text=texto_status,
                fg_color=cor_badge,
                text_color="#FFFFFF",
                corner_radius=6,
                font=("Segoe UI", 10, "bold"),
                width=155,
                height=32,
            )
            badge.pack(side="right", padx=(5, 10), pady=8)

            btn_del = ctk.CTkButton(
                card,
                text="✕",
                width=30,
                height=30,
                fg_color="#3A1C1C",
                hover_color="#5C2626",
                text_color="#EF4444",
                corner_radius=6,
                command=lambda s=site: self.remover_site(s),
            )
            btn_del.pack(side="right", padx=(4, 0), pady=8)

    def _configurar_bandeja(self):
        try:
            import pystray
            from PIL import Image

            caminho_icone = PASTA_PROJETO / "icone_bandeja.png"
            imagem = Image.open(caminho_icone).convert("RGBA")
            imagem.thumbnail((64, 64))
            menu = pystray.Menu(
                pystray.MenuItem("Abrir Equiplex SSL Guard", self._acao_abrir_bandeja, default=True),
                pystray.MenuItem("Verificar agora", self._acao_verificar_bandeja),
                pystray.MenuItem("Encerrar", self._acao_encerrar_bandeja),
            )
            self.tray_icon = pystray.Icon(
                "equiplex_ssl_guard", imagem, "Equiplex SSL Guard", menu
            )
            self.tray_icon.run_detached()
            self.tray_disponivel = True
        except Exception as erro:
            # Não impede o uso; fechar a janela minimizará para a barra de tarefas.
            print(f"Aviso: não foi possível iniciar a bandeja do sistema: {erro}")

    def _acao_abrir_bandeja(self, _icone=None, _item=None):
        try:
            self.after(0, self._mostrar_janela)
        except RuntimeError:
            pass

    def _acao_verificar_bandeja(self, _icone=None, _item=None):
        self.solicitar_verificacao.set()

    def _acao_encerrar_bandeja(self, _icone=None, _item=None):
        try:
            self.after(0, self._encerrar)
        except RuntimeError:
            pass

    def _mostrar_janela(self):
        if self.encerrando:
            return
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()

    def ao_fechar_janela(self):
        if self.tray_disponivel:
            self.withdraw()
            enviar_notificacao_windows(
                "Equiplex SSL Guard continua ativo",
                "O monitoramento continua na bandeja do sistema. Use o ícone perto do relógio para abrir ou encerrar o app.",
            )
        else:
            self.iconify()
            self.lbl_monitor.configure(
                text="O aplicativo foi minimizado para a barra de tarefas; monitoramento continua ativo.",
                text_color="#A7B5CC",
            )

    def _encerrar(self):
        if self.encerrando:
            return
        self.encerrando = True
        self.parar_monitoramento.set()
        self.solicitar_verificacao.set()
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
