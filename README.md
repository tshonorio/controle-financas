# 💰 Controle de Gastos, Compras e Parcelamentos (Mobile & Desktop)

Este é um sistema desenvolvido em **Python** utilizando **Flet** (baseado em Flutter) e **SQLite**. Ele funciona como um aplicativo desktop nativo para computadores (Windows, macOS, Linux) e pode ser compilado diretamente em um arquivo **APK** para celulares Android!

O app conta com uma interface moderna em modo escuro, gráficos animados e navegação responsiva em abas.

---

## 🚀 Como Executar o Projeto Localmente (Computador)

Siga os passos abaixo para rodar o projeto no seu computador:

### 1. Criar e Ativar o Ambiente Virtual

Abra o seu terminal (Powershell ou Prompt de Comando) na pasta deste projeto e execute:

```bash
# Criar o ambiente virtual (venv)
python -m venv venv

# Ativar o ambiente virtual
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Windows (CMD):
.\venv\Scripts\activate.bat
```

### 2. Instalar as Dependências

Com o ambiente virtual ativado, instale o Flet:

```bash
pip install -r requirements.txt
```

### 3. Rodar a Aplicação

Inicie o programa:

```bash
python main.py
```

Uma janela desktop do aplicativo se abrirá no seu computador, simulando a visualização móvel!

---

## 📱 Como Gerar o APK para Celular Android

O **Flet** possui um utilitário integrado que converte o código Python diretamente em um app Flutter nativo.

Para gerar o APK na sua máquina, você precisa ter instalado:
1. **Flutter SDK** (instalado e configurado no PATH).
2. **Android Studio** com o **Android SDK** e **NDK** configurados.
3. **Java Development Kit (JDK)** versão 17 ou superior.

### Passo Único de Compilação:

Com as ferramentas configuradas, abra o terminal e execute na pasta do projeto:

```bash
flet build apk
```

O Flet vai compilar a aplicação e o arquivo `.apk` final será gerado dentro da pasta `build/apk/`. Você poderá enviar esse arquivo para o seu celular e instalá-lo!

> 💡 **Dica**: Caso você não tenha o Flutter e o Android SDK configurados no Windows (o que é comum e complexo de configurar do zero), você pode utilizar uma máquina virtual Linux (como Ubuntu) ou compilar utilizando Docker.

---

## 🎨 Funcionalidades do Aplicativo

1. **Dashboard (Painel)**:
   - Indicadores Rápidos: *Total do Mês*, *Pago*, *Pendente* e despesas futuras (*Comprometido*).
   - Seletor de período interativo (Mês/Ano).
   - Gráfico de pizza animado (**PieChart** nativo) com a distribuição percentual das despesas.
   - Painel de **Contas Próximas** a vencer.

2. **Lançamentos**:
   - Cadastro de despesas com descrição, valor total, data da compra e categoria.
   - **Máscara de Moeda**: Formatação em tempo real no padrão brasileiro (`R$ 0,00`).
   - Seletor de data integrado.
   - **Parcelamento no Crédito**: Ao selecionar "Crédito", o app abre campos adicionais para definir quantidade de parcelas e a data do 1º vencimento. Ele calcula a divisão e faz a distribuição automática dos centavos na última parcela.

3. **Extrato**:
   - Consulta detalhada de parcelas por mês.
   - Filtros de **Status** (Todos, Pagos, Abertos) e **Categoria**.
   - Atualização de pagamento rápida (clique no círculo de status da conta).
   - Confirmação de exclusão total de compras e suas respectivas parcelas.

---

## 📁 Estrutura de Arquivos

- `main.py`: Código-fonte completo em Flet contendo layout, banco de dados SQLite e regras de negócio.
- `requirements.txt`: Dependência do projeto (`flet`).
- `README.md`: Instruções de uso e compilação do APK.
