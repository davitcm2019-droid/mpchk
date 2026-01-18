# checker_base.py - Modelo Global
import sys
import json
import random
import hashlib
import time
from typing import Dict, List, Optional, Tuple
import threading
from queue import Queue

class CheckerBase:
    def __init__(self, config: Dict):
        self.config = config
        self.results = []
        self.live_cards = []
        self.stats = {
            'tested': 0,
            'live': 0,
            'dead': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    def validate_luhn(self, card_number: str) -> bool:
        """Validação do algoritmo de Luhn"""
        digits = [int(d) for d in str(card_number)]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        return checksum % 10 == 0
    
    def generate_card(self, bin_prefix: str, length: int = 16) -> str:
        """Gera número de cartão válido (Luhn)"""
        while True:
            # Gera número aleatório
            random_part = ''.join([str(random.randint(0, 9)) 
                                 for _ in range(length - len(bin_prefix) - 1)])
            card_without_check = bin_prefix + random_part
            
            # Calcula dígito verificador
            total = 0
            reverse_digits = card_without_check[::-1]
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 0:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
            
            check_digit = (10 - (total % 10)) % 10
            card_number = card_without_check + str(check_digit)
            
            if self.validate_luhn(card_number):
                return card_number
    
    def parse_checkout_info(self, checkout_data: Dict) -> Dict:
        """Extrai informações do checkout para template"""
        template = {
            'api_endpoint': checkout_data.get('endpoint'),
            'headers': checkout_data.get('headers', {}),
            'payload_template': checkout_data.get('payload_template'),
            'method': checkout_data.get('method', 'POST'),
            'success_indicators': checkout_data.get('success_indicators', []),
            'error_indicators': checkout_data.get('error_indicators', []),
            'validation_rules': checkout_data.get('validation_rules', {})
        }
        return template
    
    def create_payload(self, card_data: Dict, template: Dict) -> Dict:
        """Cria payload específico para cada gateway"""
        # Template deve conter placeholders como {card_number}, {exp_month}, etc.
        payload = template.copy()
        
        # Substitui placeholders
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, str):
                    payload[key] = value.format(**card_data)
        
        return payload
    
    def test_card(self, card_data: Dict, gateway_config: Dict) -> Dict:
        """Método abstrato - deve ser implementado por cada checker específico"""
        raise NotImplementedError("Implemente este método na classe filha")