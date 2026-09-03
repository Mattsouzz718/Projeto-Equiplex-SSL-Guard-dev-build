<div align="center">

<img src="logo.jpg" alt="Logo Projeto Equiplex SSL Guard" width="250">

<br />

<img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/CustomTkinter-Dark_Mode-212121?style=for-the-badge&logo=python&logoColor=blue" alt="CustomTkinter" />
<img src="https://img.shields.io/badge/Status-Dev_Build-10B981?style=for-the-badge" alt="Status" />

</div>

<br />

O **Projeto-Equiplex-SSL-Guard-dev-build** é uma aplicação desktop com interface gráfica focada no monitoramento do vencimento de certificados SSL de múltiplos domínios simultaneamente.

---

## 🚀 Funcionalidades

* **Monitoramento Visual Contínuo:** O dashboard renderiza a lista de sites e exibe o status de segurança de cada domínio.
* **Indicadores de Risco por Cores:** O sistema de badges utiliza um esquema de cores para facilitar o monitoramento:
  * **Seguro (Verde / `#10B981`):** Certificados com mais de 30 dias restantes.
  * **Atenção (Laranja / `#F59E0B`):** Certificados que expiram entre 7 e 30 dias.
  * **CRÍTICO! (Vermelho / `#EF4444`):** Certificados com menos de 7 dias para expirar.
  * **ERRO DE CONEXÃO (Cinza / `#555555`):** Retornado (código `-999`) quando o site está offline, apresenta falha na porta 443 ou timeout de 5 segundos.
* **Popups de Alerta:** Emite janelas (TopLevel) sobrepostas à tela e destacadas em vermelho para domínios que estão prestes a vencer ou já expiraram.
* **Tratamento Inteligente de URLs:** Caso o usuário cole URLs completas, o sistema remove automaticamente prefixos como `http://` ou `https://`, extraindo apenas o host principal para a consulta.
* **Persistência de Dados Automática:** Salva domínios rastreados (como `www.google.com` ou `equiplex.com.br`) no disco para que os dados persistam após fechar a aplicação.

## 🛠️ Arquitetura e Tecnologias

* **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** Framework utilizado para desenhar toda a GUI moderna do aplicativo na resolução 680x520, rodando nativamente em modo Escuro (`dark`) com realces na cor azul.
* **Módulos `ssl` e `socket`:** Bibliotecas padrão do Python utilizadas para abrir comunicação de rede na porta 443, envelopar o socket em um contexto seguro e capturar os dados brutos (`notAfter`) do certificado TLS/SSL da máquina remota.
* **Módulo `datetime`:** Realiza o cálculo temporal (`data_expiracao - datetime.utcnow()`) convertendo o formato string do certificado para dias exatos restantes.
* **Módulo `json` / `os`:** Responsáveis pela função de salvar e carregar os dados persistentes no arquivo `dados.json` estruturado e com indentação para fácil leitura.

## ⚙️ Como Executar

```bash
# 1. Certifique-se de ter o Python 3 instalado na sua máquina.

# 2. Instale a dependência gráfica
$ pip install customtkinter

# 3. Clone e acesse o diretório do projeto, depois execute:
$ python main.py