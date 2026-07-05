"""
Script para extrair dados do Clinicys - Extrato de Atendimentos
Extrai pacientes atendidos por médico em um período específico
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

class ClinicysExtractor:
    def __init__(self):
        """Inicializar o extrator do Clinicys"""
        self.url = os.getenv('CLINICYS_URL', 'https://sistema.clinicys.com.br/Fertgroup/menu.php')
        self.username = os.getenv('CLINICYS_USERNAME')
        self.password = os.getenv('CLINICYS_PASSWORD')
        self.driver = None
        
        if not self.username or not self.password:
            raise ValueError("CLINICYS_USERNAME e CLINICYS_PASSWORD não configuradas no .env")
        
        logger.info("ClinicysExtractor inicializado")

    def setup_browser(self):
        """Configurar o navegador Selenium"""
        chrome_options = Options()
        
        # Descomente a linha abaixo para modo headless (sem interface gráfica)
        # chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Navegador configurado")

    def login(self):
        """Fazer login no Clinicys"""
        try:
            logger.info(f"Acessando {self.url}")
            self.driver.get(self.url)
            
            # Aguardar o carregamento da página
            time.sleep(2)
            
            # Preencher username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "user"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            logger.info("Username preenchido")
            
            # Preencher password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("Password preenchido")
            
            # Clicar no botão de login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(3)
            logger.info("Login realizado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao fazer login: {str(e)}")
            raise

    def navigate_to_report(self):
        """Navegar até Relatórios > Extrato de Atendimentos"""
        try:
            # Clicar em Relatórios
            relatorios_menu = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Relatórios"))
            )
            relatorios_menu.click()
            time.sleep(1)
            logger.info("Menu Relatórios clicado")
            
            # Clicar em "Extrato de Atendimentos"
            extrato_menu = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Extrato de Atendimentos"))
            )
            extrato_menu.click()
            time.sleep(2)
            logger.info("Relatório 'Extrato de Atendimentos' aberto")
            
        except Exception as e:
            logger.error(f"Erro ao navegar: {str(e)}")
            raise

    def set_filters(self, doctor_name, start_date, end_date):
        """
        Definir filtros no relatório
        
        Args:
            doctor_name: Nome do médico (ex: "Dra. Sara")
            start_date: Data inicial (formato: "01/07/2026")
            end_date: Data final (formato: "31/07/2026")
        """
        try:
            # Clicar no dropdown de médico
            doctor_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//select[@name='medico'] | //select[@id='medico']"))
            )
            
            select = Select(doctor_dropdown)
            select.select_by_visible_text(doctor_name)
            logger.info(f"Médico '{doctor_name}' selecionado")
            
            # Preencher data inicial
            start_date_field = self.driver.find_element(By.XPATH, "//input[@placeholder='dd/mm/aaaa']")
            start_date_field.clear()
            start_date_field.send_keys(start_date)
            logger.info(f"Data inicial '{start_date}' preenchida")
            
            # Preencher data final (pode ser outro campo)
            date_fields = self.driver.find_elements(By.XPATH, "//input[@placeholder='dd/mm/aaaa']")
            if len(date_fields) > 1:
                date_fields[1].clear()
                date_fields[1].send_keys(end_date)
                logger.info(f"Data final '{end_date}' preenchida")
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erro ao definir filtros: {str(e)}")
            raise

    def apply_report(self):
        """Clicar no botão 'Atualizar relatório'"""
        try:
            atualizar_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Atualizar')]"))
            )
            atualizar_button.click()
            time.sleep(3)
            logger.info("Relatório atualizado")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar relatório: {str(e)}")
            raise

    def extract_table_data(self, doctor_name):
        """
        Extrair dados da tabela do relatório
        
        Returns:
            DataFrame com os dados extraídos
        """
        try:
            # Aguardar a tabela carregar
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table"))
            )
            
            # Extrair headers
            headers = []
            header_cells = table.find_elements(By.XPATH, ".//thead//th")
            for cell in header_cells:
                headers.append(cell.text.strip())
            
            # Extrair linhas
            rows = []
            body_rows = table.find_elements(By.XPATH, ".//tbody//tr")
            
            for row in body_rows:
                cells = row.find_elements(By.XPATH, ".//td")
                row_data = [cell.text.strip() for cell in cells]
                
                if row_data:  # Ignorar linhas vazias
                    rows.append(row_data)
            
            # Criar DataFrame
            if headers and rows:
                df = pd.DataFrame(rows, columns=headers)
                df['Médico'] = doctor_name
                
                logger.info(f"Extraídos {len(df)} registros para {doctor_name}")
                return df
            else:
                logger.warning("Nenhum dado extraído da tabela")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da tabela: {str(e)}")
            raise

    def extract_multiple_doctors(self, doctors, start_date, end_date):
        """
        Extrair dados para múltiplos médicos
        
        Args:
            doctors: Lista de nomes de médicos
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            DataFrame consolidado
        """
        all_data = pd.DataFrame()
        
        for doctor in doctors:
            try:
                logger.info(f"Extraindo dados para {doctor}...")
                
                self.set_filters(doctor, start_date, end_date)
                self.apply_report()
                
                df = self.extract_table_data(doctor)
                all_data = pd.concat([all_data, df], ignore_index=True)
                
            except Exception as e:
                logger.error(f"Erro ao processar {doctor}: {str(e)}")
                continue
        
        return all_data

    def close(self):
        """Fechar o navegador"""
        if self.driver:
            self.driver.quit()
            logger.info("Navegador fechado")

    def run(self, doctors, start_date, end_date):
        """
        Executar extração completa
        
        Args:
            doctors: Lista de nomes de médicos
            start_date: Data inicial (formato: "01/07/2026")
            end_date: Data final (formato: "31/07/2026")
            
        Returns:
            DataFrame com os dados extraídos
        """
        try:
            self.setup_browser()
            self.login()
            self.navigate_to_report()
            
            data = self.extract_multiple_doctors(doctors, start_date, end_date)
            
            logger.info(f"Extração concluída: {len(data)} registros")
            return data
            
        finally:
            self.close()


# Exemplo de uso
if __name__ == "__main__":
    # Data do mês atual
    hoje = datetime.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = (primeiro_dia + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    start_date = primeiro_dia.strftime("%d/%m/%Y")
    end_date = ultimo_dia.strftime("%d/%m/%Y")
    
    # Médicos a extrair
    doctors = ["Dra. Sara", "Dr. André"]
    
    # Executar extração
    extrator = ClinicysExtractor()
    df = extrator.run(doctors, start_date, end_date)
    
    # Salvar em CSV para análise
    df.to_csv("dados_clinicys.csv", index=False, encoding="utf-8-sig")
    print(f"Dados salvos em 'dados_clinicys.csv'")
    print(df.head())
