import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# CONFIGURAÇÕES
# ============================================================

FORM_URL = (
    "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?"
    "id=4r_bEbiJSUW-EM7DZOWVUbXaMDi2fDZMkIn0cRzdzYxUQlFJTzRTSlhDMEcxTjFMNFIwOVVHSFNGUS4u"
)


# Conversão da sigla do estado para o nome completo
ESTADOS = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}


# ============================================================
# CONSULTA CEP - VIA CEP
# ============================================================

def consultar_cep(cep):
    """
    Consulta o endereço através da API ViaCEP.
    """

    # Remove caracteres como hífen e espaços
    cep = cep.strip().replace("-", "").replace(".", "")

    # Validação do CEP
    if not cep.isdigit() or len(cep) != 8:
        raise ValueError("CEP inválido. Digite um CEP com 8 números.")

    print("\nConsultando ViaCEP...")

    url = f"https://viacep.com.br/ws/{cep}/json/"

    resposta = requests.get(url, timeout=10)

    # Verifica se a requisição foi realizada corretamente
    resposta.raise_for_status()

    dados = resposta.json()

    # ViaCEP retorna "erro": true quando o CEP não existe
    if dados.get("erro"):
        raise ValueError("CEP não encontrado.")

    uf = dados.get("uf")

    # Converte a UF para o nome completo do estado
    estado = ESTADOS.get(uf, uf)

    endereco = {
        "logradouro": dados.get("logradouro", ""),
        "bairro": dados.get("bairro", ""),
        "localidade": dados.get("localidade", ""),
        "estado": estado,
    }

    return endereco


# ============================================================
# PREENCHIMENTO DO MICROSOFT FORMS
# ============================================================

def preencher_forms(nome, cep, endereco):
    """
    Abre o Microsoft Forms, preenche os campos e envia o formulário.
    """

    print("\nAbrindo Microsoft Forms...")

    # Configuração do Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    try:
        # Abre o formulário
        driver.get(FORM_URL)

        wait = WebDriverWait(driver, 30)

        # Localiza todos os campos de texto do formulário
        campos = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '[data-automation-id="textInput"]')
            )
        )

        # O formulário possui 6 campos
        if len(campos) < 6:
            raise Exception(
                f"Esperados 6 campos, mas foram encontrados {len(campos)}."
            )

        # Valores que serão preenchidos
        valores = [
            nome,
            cep,
            endereco["logradouro"],
            endereco["bairro"],
            endereco["localidade"],
            endereco["estado"],
        ]

        nomes_campos = [
            "Nome do Cliente",
            "CEP",
            "Logradouro",
            "Bairro",
            "Localidade",
            "Estado",
        ]

        print("\nPreenchendo formulário:\n")

        # Preenche os campos
        for campo, valor, nome_campo in zip(
            campos[:6],
            valores,
            nomes_campos
        ):
            campo.clear()
            campo.send_keys(valor)

            print(f"[OK] {nome_campo}: {valor}")

        print("\nTodos os campos foram preenchidos.")

        # ====================================================
        # ENVIO DO FORMULÁRIO
        # ====================================================

        botao = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-automation-id="submitButton"]')
            )
        )

        print("\nEnviando formulário...")

        botao.click()

        # ====================================================
        # CONFIRMAÇÃO REAL DO MICROSOFT FORMS
        # ====================================================

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(text(), 'Your response was submitted')]"
                    )
                )
            )

            print("[OK] Formulário enviado com sucesso!")

            print("\n============================================================")
            print("CADASTRO CONCLUÍDO!")
            print("============================================================")

        except Exception:
            print("[ERRO] Não foi possível confirmar o envio.")
            print(
                "O Microsoft Forms não apresentou a confirmação "
                "'Your response was submitted'."
            )

            raise Exception(
                "O envio do formulário não pôde ser confirmado."
            )

    finally:
        # Fecha o Chrome automaticamente após o processo
        driver.quit()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("============================================================")
    print("AUTOMAÇÃO DE CADASTRO DE CLIENTE")
    print("============================================================")

    # Entrada dos dados pelo usuário
    nome = input("\nDigite o nome do cliente: ").strip()
    cep = input("Digite o CEP: ").strip()

    # Validação do nome
    if not nome:
        print("\n[ERRO] O nome do cliente não pode ficar vazio.")
        return

    try:

        # Consulta o endereço através do CEP
        endereco = consultar_cep(cep)

        # Mostra os dados encontrados
        print("\nDados encontrados:")
        print(f"  Logradouro : {endereco['logradouro']}")
        print(f"  Bairro     : {endereco['bairro']}")
        print(f"  Localidade : {endereco['localidade']}")
        print(f"  Estado     : {endereco['estado']}")

        # Preenche e envia o Microsoft Forms
        preencher_forms(nome, cep.replace("-", ""), endereco)

    except requests.RequestException as erro:

        print("\n[ERRO] Não foi possível acessar o ViaCEP.")
        print(f"Detalhes: {erro}")

    except ValueError as erro:

        print(f"\n[ERRO] {erro}")

    except Exception as erro:

        print(f"\n[ERRO] A automação não pôde ser concluída.")
        print(f"Detalhes: {erro}")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()