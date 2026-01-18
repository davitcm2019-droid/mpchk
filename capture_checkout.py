# capture_checkout.py
"""
Script para capturar automaticamente informações do checkout
usando Selenium WebDriver
"""

import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# Ensure utils folder is importable when the script runs directly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(BASE_DIR, 'utils')
if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)

class CheckoutCapture:
    def __init__(self, url):
        self.url = url
        self.network_logs = []
        self.setup_driver()
    
    def setup_driver(self):
        """Configura Chrome com logging de rede"""
        options = webdriver.ChromeOptions()
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--headless')  # Executa em background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=options)
    
    def capture_checkout_flow(self):
        """Captura fluxo completo do checkout"""
        print(f"Acessando: {self.url}")
        self.driver.get(self.url)
        
        # Aguarda página carregar
        time.sleep(3)
        
        # Tenta encontrar formulário de checkout
        try:
            # Procura campos de cartão
            card_fields = self.driver.find_elements(By.XPATH, 
                "//input[contains(@name, 'card') or contains(@placeholder, 'card')]")
            
            if card_fields:
                print(f"Encontrados {len(card_fields)} campos de cartão")
                
                # Preenche com dados de teste
                test_data = {
                    'card_number': '4242424242424242',
                    'exp_month': '12',
                    'exp_year': '2028',
                    'cvv': '123'
                }
                
                for field in card_fields:
                    field_name = field.get_attribute('name') or field.get_attribute('id') or ''
                    field_name_lower = field_name.lower()
                    
                    if 'number' in field_name_lower:
                        field.send_keys(test_data['card_number'])
                    elif 'month' in field_name_lower or 'exp' in field_name_lower:
                        field.send_keys(test_data['exp_month'])
                    elif 'year' in field_name_lower:
                        field.send_keys(test_data['exp_year'])
                    elif 'cvv' in field_name_lower or 'cvc' in field_name_lower:
                        field.send_keys(test_data['cvv'])
                
                # Captura logs de rede antes do submit
                self.capture_network_logs()
                
                # Tenta encontrar botão de submit
                submit_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Pagar') or contains(text(), 'Pay') or contains(@type, 'submit')]")
                
                if submit_buttons:
                    print("Clicando no botão de pagamento...")
                    submit_buttons[0].click()
                    
                    # Aguarda e captura mais logs
                    time.sleep(5)
                    self.capture_network_logs()
                    
        except Exception as e:
            print(f"Erro durante captura: {e}")
        
        finally:
            self.driver.quit()
        
        return self.analyze_captured_data()
    
    def capture_network_logs(self):
        """Captura logs de rede do Chrome"""
        logs = self.driver.get_log('performance')
        self.network_logs.extend(logs)
    
    def analyze_captured_data(self):
        """Analisa dados capturados e gera template"""
        from template_generator import CheckoutAnalyzer
        
        analyzer = CheckoutAnalyzer()
        
        # Converte logs para formato analisável
        formatted_logs = []
        for log in self.network_logs:
            try:
                message = json.loads(log['message'])['message']
                if message['method'] == 'Network.requestWillBeSent':
                    request = message['params']['request']
                    formatted_logs.append({
                        'request': {
                            'url': request.get('url'),
                            'method': request.get('method'),
                            'headers': request.get('headers', {}),
                            'postData': request.get('postData')
                        }
                    })
            except:
                continue
        
        # Analisa logs
        analysis = analyzer.capture_network_traffic(formatted_logs)
        
        # Gera template
        template = analyzer.generate_checker_template(analysis)
        
        return template
    
    def save_template(self, template, filename='checkout_template.json'):
        """Salva template em arquivo"""
        with open(filename, 'w') as f:
            json.dump(template, f, indent=2)
        print(f"Template salvo em: {filename}")
        return filename

# Uso:
if __name__ == '__main__':
    # URL do checkout para capturar
    checkout_url = input("Digite a URL do checkout: ").strip()
    
    if checkout_url:
        capture = CheckoutCapture(checkout_url)
        template = capture.capture_checkout_flow()
        
        if template:
            filename = capture.save_template(template)
            print(f"\nTemplate gerado com sucesso!")
            print(f"Arquivo: {filename}")
            print(f"Gateway detectado: {template.get('gateway', 'Desconhecido')}")
        else:
            print("Não foi possível gerar template.")
    else:
        print("URL não fornecida.")
