<div align="center">

<img src="logo.png" alt="Logo do Equiplex SSL Guard" width="380">

# Equiplex SSL Guard

**Aplicativo desktop para acompanhar a validade de certificados HTTPS no Windows 11.**

Consulta o certificado, estima a localização do IP conectado e avisa quando um certificado está perto de vencer ou já expirou.

</div>

## Conteúdo

- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação e execução pelo VS Code](#instalação-e-execução-pelo-vs-code)
- [Como usar](#como-usar)
- [Monitoramento em segundo plano](#monitoramento-em-segundo-plano)
- [Como funcionam os alertas](#como-funcionam-os-alertas)
- [Localização do servidor](#localização-do-servidor)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Limitações e observações de segurança](#limitações-e-observações-de-segurança)
- [Solução de problemas](#solução-de-problemas)

## Funcionalidades

- **Painel visual:** apresenta os domínios monitorados, o prazo restante do certificado, o IP conectado, a data de expiração e a localização estimada.
- **Cadastro de domínios:** aceita tanto `exemplo.com` quanto uma URL completa, como `https://exemplo.com/pagina`.
- **Verificação em segundo plano:** realiza uma varredura ao iniciar e repete a consulta automaticamente a cada **15 minutos**. As consultas de rede acontecem fora da thread gráfica para manter a janela responsiva.
- **Ícones e estados no painel:** mostra se o certificado está dentro do prazo, próximo do vencimento, expirado ou se houve erro na consulta.
- **Alertas de vencimento:** gera um alerta quando faltam **7 dias ou menos** para o vencimento e outro quando identifica um certificado expirado. O mesmo estágio de alerta não é repetido em todas as varreduras.
- **Notificações no Windows:** envia notificações nativas do Windows 10/11 para certificados próximos do vencimento ou expirados. O aplicativo não abre pop-ups próprios; a aparência da notificação é controlada pelo Windows.
- **Bandeja do sistema:** utiliza o ícone azul de escudo e cadeado em `icone_bandeja.png`. Fechar a janela normalmente esconde o aplicativo perto do relógio, mantendo a verificação ativa. O menu do ícone oferece opções para abrir o painel, verificar agora e encerrar o aplicativo.
- **Dados persistentes:** guarda a lista de domínios e o estágio do último alerta em `dados.json`.
- **Localização em cache:** guarda temporariamente os dados de geolocalização por IP para reduzir consultas repetidas ao serviço de localização.
- **Execução manual:** não há script `iniciar.bat` e o aplicativo não foi configurado para iniciar junto com o Windows. Ele começa somente quando você executa `main.py` pelo VS Code ou pelo Python.

## Requisitos

- Windows 11 recomendado. O painel também usa bibliotecas multiplataforma, mas a notificação nativa é específica do Windows.
- Python **3.10 ou superior**.
- Visual Studio Code.
- Extensão **Python**, publicada pela Microsoft, instalada no VS Code.
- Acesso à internet para consultar os sites HTTPS e o serviço de localização `ipapi.co`.

As bibliotecas necessárias estão listadas em `requirements.txt`. A instalação inclui CustomTkinter, Requests, Cryptography, pystray, Pillow e Winotify (no Windows).

## Instalação e execução pelo VS Code

1. Extraia o arquivo ZIP para uma pasta.
2. Abra o VS Code e selecione **Arquivo → Abrir Pasta...**. Escolha a pasta `Projeto-Equiplex-SSL-Guard-main`, aquela que contém `main.py` e `requirements.txt`.
3. Abra o terminal integrado pelo menu **Terminal → Novo Terminal**.
4. Instale as dependências. No Windows, tente:

   ```powershell
   py -m pip install -r requirements.txt
   ```

   Se o comando `py` não existir no computador, use:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Abra `main.py` e clique em **Run Python File** no canto superior direito. Como alternativa, abra **Run and Debug**, escolha **Equiplex SSL Guard (main.py)** e pressione **F5**.

A instalação das dependências precisa ser feita apenas uma vez para o ambiente Python selecionado. Depois disso, para iniciar o aplicativo basta executar `main.py`. **Não é necessário usar arquivo `.bat`.**

> Dica: se o VS Code pedir para selecionar um interpretador Python, escolha o mesmo Python no qual você instalou as dependências.

## Como usar

1. Inicie o aplicativo executando `main.py`.
2. Digite um domínio, por exemplo `exemplo.com`, ou cole uma URL completa. Clique em **+ Monitorar** ou pressione Enter.
3. O domínio será salvo e a verificação será solicitada. Quando a consulta terminar, o cartão mostrará o prazo do certificado, o IP conectado e a localização estimada.
4. Use **Verificar agora** para solicitar uma nova varredura sem esperar o próximo intervalo automático.
5. Clique no botão `✕` de um cartão para remover aquele domínio da lista.
6. Para fechar a janela sem parar o monitoramento, use o botão de fechar da janela. O aplicativo ficará na bandeja do sistema, perto do relógio do Windows.
7. Para reabrir o painel, clique com o botão direito no ícone da bandeja e selecione **Abrir Equiplex SSL Guard**. Para finalizar completamente, escolha **Encerrar**.

## Monitoramento em segundo plano

O monitor começa automaticamente **depois que você executa o aplicativo**. Ele verifica todos os domínios salvos assim que inicia e repete as verificações em intervalos de 15 minutos. O botão **Verificar agora** pede que a próxima varredura aconteça antes desse intervalo.

Fechar a janela não encerra o processo: com a bandeja disponível, a janela é escondida e o monitor continua ativo. Para parar o monitoramento, selecione **Encerrar** no menu da bandeja ou finalize o processo. Desligar o computador também interrompe o programa.

**Importante:** o aplicativo não roda como serviço do Windows, não inicia automaticamente quando o computador liga e não monitora quando o processo está encerrado. Para iniciar o monitoramento, abra o projeto no VS Code e execute `main.py`.

Se a bandeja do sistema não puder ser iniciada, o aplicativo informa o problema no terminal e usa a minimização para a barra de tarefas como alternativa. Nesse caso, não encerre a execução do Python se quiser continuar monitorando.

## Como funcionam os alertas

- **Mais de 30 dias restantes:** estado verde, prazo OK.
- **De 8 a 30 dias restantes:** estado laranja, atenção.
- **De 0 a 7 dias restantes:** estado vermelho e alerta de certificado próximo do vencimento.
- **Certificado expirado:** o domínio fica sinalizado em vermelho no painel e o app envia uma notificação nativa do Windows.
- **Erro de consulta:** o cartão indica erro de conexão ou de leitura. A falha de uma consulta não deve encerrar o monitoramento dos outros domínios.

O estágio de alerta é registrado em `dados.json`. Assim, a mesma notificação não é disparada em cada varredura para um certificado que continua no mesmo estágio. Quando o certificado passa de próximo do vencimento para expirado, o app pode emitir o alerta de expiração.

O aplicativo não exibe mais aquele pop-up vermelho próprio. Ele envia somente notificações nativas do Windows. A aparência, a cor e o posicionamento dessas notificações são controlados pelo Windows e não podem ser definidos livremente pelo app.

Para receber as notificações, deixe-as habilitadas em **Configurações do Windows → Sistema → Notificações** e permita notificações para o ambiente de execução. O aplicativo precisa continuar em execução para detectar mudanças e enviar alertas.

## Localização do servidor

O aplicativo consulta o IP que foi efetivamente usado na conexão HTTPS e envia esse IP ao serviço público `ipapi.co`. Quando o serviço responde, o painel pode exibir cidade, região, país e organização/provedor. A resposta de localização é armazenada em cache por até 24 horas.

A localização é **uma estimativa baseada no IP**, não uma leitura de GPS nem uma medição da posição física exata do equipamento que hospeda o site. Sites com CDN, proxy, balanceamento de carga ou serviços como Cloudflare podem apresentar um IP de infraestrutura intermediária. Se o serviço de geolocalização estiver indisponível, o certificado ainda pode ser verificado, mas os campos de localização podem ficar vazios.

## Estrutura do projeto

```text
Projeto-Equiplex-SSL-Guard-main/
├── main.py                    # Interface, painel e rotina do monitor
├── dados.json                 # Domínios salvos e estágios de alerta
├── requirements.txt            # Dependências Python
├── logo.png                    # Logo principal do projeto
├── icone_bandeja.png           # Ícone transparente da bandeja e das notificações
├── README.md                   # Este guia
├── .vscode/
│   └── launch.json             # Configuração para executar com F5
└── modulos/
    ├── ssl_checker.py          # Consulta SSL, validade, IP e localização
    ├── notificacoes.py         # Notificações nativas do Windows
    └── persistencia.py         # Leitura e gravação de dados.json
```

## Limitações e observações de segurança

- **Validade não é uma auditoria TLS completa.** Para ler a data de certificados já vencidos, a consulta extrai o certificado sem validar a cadeia de confiança TLS. Portanto, o estado exibido se refere principalmente à data de expiração e não garante que o certificado seja confiável, que o domínio corresponda ao certificado ou que toda a configuração HTTPS esteja segura.
- **A disponibilidade não é garantida.** Uma falha de DNS, conexão, bloqueio de rede ou limitação de consultas pode impedir uma varredura. O app não prevê se um servidor realmente vai cair; ele monitora a data de validade do certificado.
- **O IP pode variar.** Um domínio pode resolver para endereços diferentes conforme a rede, o DNS, o balanceamento de carga e a infraestrutura do site.
- **Serviço externo de geolocalização.** Para mostrar a localização, o IP conectado é consultado no serviço `ipapi.co`. Sem internet, com limite de requisições ou com falha do serviço, a localização pode não aparecer.
- **Notificações nativas.** O Windows pode ocultar ou agrupar notificações conforme suas próprias configurações. O aplicativo usa somente notificações nativas, sem exibir pop-ups próprios.

## Solução de problemas

### O comando `py` ou `python` não funciona

Verifique se o Python está instalado e disponível no PATH. No VS Code, use **Ctrl+Shift+P → Python: Select Interpreter** e selecione a instalação correta.

### Não foi possível importar uma biblioteca

Abra o terminal integrado na pasta que contém `requirements.txt` e execute novamente:

```powershell
py -m pip install -r requirements.txt
```

Confira se o terminal está usando o mesmo interpretador selecionado no VS Code.

### A localização não aparece

Verifique a conexão com a internet. A localização depende de uma resposta do `ipapi.co` e pode não estar disponível para todos os IPs.

### A notificação não apareceu

Confira **Configurações do Windows → Sistema → Notificações** e permita notificações para o ambiente de execução. Os alertas nativos são enviados quando a varredura detecta uma mudança de estágio; eles não são repetidos a cada 15 minutos sem necessidade.

### O monitor parou depois de fechar o VS Code

Isso acontece porque o aplicativo é um processo Python iniciado manualmente. Mantenha a execução de `main.py` ativa para que o monitor continue funcionando. O projeto não foi configurado para rodar como serviço nem para iniciar com o Windows.
