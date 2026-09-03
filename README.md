<div align="center">

<!-- Altere o nome do arquivo abaixo para o nome real da imagem quando salvar no repositório -->
<img src="watermarked_img_3014784686175417446.jpg" alt="Logo Projeto Equiplex SSL Guard" width="250">

<br />

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![CustomTkinter](https://img.shields.io/badge/CustomTkinter-Dark_Mode-212121?style=for-the-badge&logo=python&logoColor=blue)]()
[![Status](https://img.shields.io/badge/Status-Dev_Build-10B981?style=for-the-badge)]()

</div>

<br />

O **Projeto-Equiplex-SSL-Guard-dev-build**[cite: 3] é uma aplicação desktop com interface gráfica focada no monitoramento do vencimento de certificados SSL de múltiplos domínios simultaneamente[cite: 2, 5].

---

## 🚀 Funcionalidades

* **Monitoramento Visual Contínuo:** O dashboard renderiza a lista de sites e exibe o status de segurança de cada domínio.
* **Indicadores de Risco por Cores:** O sistema de badges utiliza um esquema de cores para facilitar o monitoramento:
  * **Seguro (Verde / `#10B981`):** Certificados com mais de 30 dias restantes[cite: 2].
  * **Atenção (Laranja / `#F59E0B`):** Certificados que expiram entre 7 e 30 dias[cite: 2].
  * **CRÍTICO! (Vermelho / `#EF4444`):** Certificados com menos de 7 dias para expirar[cite: 2].
  * **ERRO DE CONEXÃO (Cinza / `#555555`):** Retornado (código `-999`) quando o site está offline, apresenta falha na porta 443 ou timeout de 5 segundos[cite: 2, 5].
* **Popups de Alerta:** Emite janelas (TopLevel) sobrepostas à tela e destacadas em vermelho para domínios que estão prestes a vencer ou já expiraram[cite: 2].
* **Tratamento Inteligente de URLs:** Caso o usuário cole URLs completas, o sistema remove automaticamente prefixos como `http://` ou `https://`, extraindo apenas o host principal para a consulta[cite: 2, 5].
* **Persistência de Dados Automática:** Salva domínios rastreados (como `www.google.com` ou `equiplex.com.br`[cite: 1]) no disco para que os dados persistam após fechar a aplicação.

## 🛠️ Arquitetura e Tecnologias

* **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** Framework utilizado para desenhar toda a GUI moderna do aplicativo na resolução 680x520, rodando nativamente em modo Escuro (`dark`) com realces na cor azul[cite: 2].
* **Módulos `ssl` e `socket`:** Bibliotecas padrão do Python utilizadas para abrir comunicação de rede na porta 443, envelopar o socket em um contexto seguro e capturar os dados brutos (`notAfter`) do certificado TLS/SSL da máquina remota.
* **Módulo `datetime`:** Realiza o cálculo temporal (`data_expiracao - datetime.utcnow()`) convertendo o formato string do certificado para dias exatos restantes[cite: 5].
* **Módulo `json` / `os`:** Responsáveis pela função de salvar e carregar os dados persistentes no arquivo `dados.json` estruturado e com indentação para fácil leitura[cite: 4].

## ⚙️ Como Executar

```bash
# 1. Certifique-se de ter o Python 3 instalado na sua máquina.

# 2. Instale a dependência gráfica
$ pip install customtkinter

# 3. Clone e acesse o diretório do projeto, depois execute:
$ python main.py