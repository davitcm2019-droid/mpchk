# template_generator.py
import re
import json
from urllib.parse import urlparse, parse_qs

class CheckoutAnalyzer:
    def __init__(self):
        self.common_gateways = {
            'stripe': {
                'patterns': ['stripe.com', 'js.stripe.com'],
                'endpoints': [
                    'api.stripe.com/v1/payment_methods',
                    'api.stripe.com/v1/payment_intents',
                    'api.stripe.com/v1/tokens'
                ]
            },
            'braintree': {
                'patterns': ['braintreegateway.com', 'paypal.com/braintree'],
                'endpoints': [
                    'payments.braintree-api.com/graphql',
                    'client-analytics.braintreegateway.com'
                ]
            },
            'adyen': {
                'patterns': ['adyen.com', 'checkoutshopper-'],
                'endpoints': [
                    'checkout-test.adyen.com/v69/payments',
                    'pal-adyen.com/pal/servlet/Payment/v68'
                ]
            },
            'square': {
                'patterns': ['squareup.com', 'connect.squareup.com'],
                'endpoints': [
                    'connect.squareup.com/v2/payments',
                    'js.squareup.com/v2/paymentform'
                ]
            },
            'pagarme': {
                'patterns': ['pagarme.com', 'api.pagar.me'],
                'endpoints': [
                    'api.pagar.me/1/transactions',
                    'api.pagar.me/core/v5/orders'
                ]
            },
            'mercadopago': {
                'patterns': ['mercadopago.com', 'mercadolibre.com'],
                'endpoints': [
                    'api.mercadopago.com/v1/payments',
                    'api.mercadopago.com/card_tokens'
                ]
            }
        }
    
    def capture_network_traffic(self, browser_logs: List) -> Dict:
        """Analisa logs de rede do navegador"""
        endpoints_found = []
        payloads_found = []
        
        for log in browser_logs:
            if 'request' in log:
                url = log['request'].get('url', '')
                method = log['request'].get('method', '')
                headers = log['request'].get('headers', {})
                post_data = log['request'].get('postData', '')
                
                # Identifica gateway
                gateway = self.identify_gateway(url, headers)
                
                if gateway and method in ['POST', 'PUT']:
                    endpoint_info = {
                        'url': url,
                        'method': method,
                        'headers': headers,
                        'payload': post_data,
                        'gateway': gateway
                    }
                    endpoints_found.append(endpoint_info)
                    
                    # Tenta extrair template do payload
                    if post_data:
                        template = self.extract_payload_template(post_data)
                        if template:
                            payloads_found.append({
                                'gateway': gateway,
                                'template': template,
                                'sample': post_data[:500]
                            })
        
        return {
            'endpoints': endpoints_found,
            'payload_templates': payloads_found,
            'primary_gateway': self.detect_primary_gateway(endpoints_found)
        }
    
    def identify_gateway(self, url: str, headers: Dict) -> Optional[str]:
        """Identifica o gateway de pagamento pela URL e headers"""
        url_lower = url.lower()
        
        for gateway, info in self.common_gateways.items():
            # Verifica padrões na URL
            for pattern in info['patterns']:
                if pattern in url_lower:
                    return gateway
            
            # Verifica endpoints específicos
            for endpoint in info['endpoints']:
                if endpoint in url_lower:
                    return gateway
        
        # Verifica headers específicos
        for header_name, header_value in headers.items():
            header_lower = str(header_value).lower()
            for gateway, info in self.common_gateways.items():
                if gateway in header_lower:
                    return gateway
        
        return None
    
    def extract_payload_template(self, post_data: str) -> Optional[Dict]:
        """Extrai template do payload de checkout"""
        try:
            # Tenta parsear como JSON
            if post_data.strip().startswith('{'):
                data = json.loads(post_data)
                template = {}
                
                for key, value in data.items():
                    if self.is_card_field(key, value):
                        # Substitui valor real por placeholder
                        template[key] = self.get_field_placeholder(key)
                    else:
                        # Mantém valor fixo
                        template[key] = value
                
                return template
            
            # Tenta parsear como form data
            elif '=' in post_data:
                params = parse_qs(post_data)
                template = {}
                
                for key, values in params.items():
                    if values and self.is_card_field(key, values[0]):
                        template[key] = self.get_field_placeholder(key)
                    else:
                        template[key] = values[0] if values else ''
                
                return template
                
        except:
            pass
        
        return None
    
    def is_card_field(self, field_name: str, field_value: str) -> bool:
        """Identifica se o campo é relacionado a cartão"""
        card_patterns = [
            r'card', r'credit', r'debit', r'number', r'num',
            r'exp', r'expiry', r'valid', r'month', r'year',
            r'cvv', r'cvc', r'security', r'ccv'
        ]
        
        value_patterns = [
            r'^\d{13,19}$',  # Número de cartão
            r'^\d{3,4}$',    # CVV
            r'^\d{1,2}$',    # Mês
            r'^\d{2,4}$'     # Ano
        ]
        
        field_lower = field_name.lower()
        
        # Verifica nome do campo
        for pattern in card_patterns:
            if re.search(pattern, field_lower):
                return True
        
        # Verifica valor do campo
        if isinstance(field_value, str):
            for pattern in value_patterns:
                if re.fullmatch(pattern, field_value.strip()):
                    return True
        
        return False
    
    def get_field_placeholder(self, field_name: str) -> str:
        """Retorna placeholder baseado no nome do campo"""
        field_lower = field_name.lower()
        
        if 'number' in field_lower or 'num' in field_lower or 'card' in field_lower:
            return '{card_number}'
        elif 'month' in field_lower or 'exp_month' in field_lower:
            return '{exp_month}'
        elif 'year' in field_lower or 'exp_year' in field_lower:
            return '{exp_year}'
        elif 'cvv' in field_lower or 'cvc' in field_lower:
            return '{cvv}'
        else:
            return '{' + field_name + '}'
    
    def detect_primary_gateway(self, endpoints: List) -> Optional[str]:
        """Identifica o gateway principal baseado na frequência"""
        gateway_counts = {}
        
        for endpoint in endpoints:
            gateway = endpoint.get('gateway')
            if gateway:
                gateway_counts[gateway] = gateway_counts.get(gateway, 0) + 1
        
        if gateway_counts:
            return max(gateway_counts, key=gateway_counts.get)
        
        return None
    
    def generate_checker_template(self, analysis_result: Dict) -> Dict:
        """Gera template completo para checker"""
        primary = analysis_result.get('primary_gateway')
        templates = analysis_result.get('payload_templates', [])
        
        checker_template = {
            'gateway': primary,
            'config': {
                'base_url': self.get_base_url(primary),
                'endpoints': [],
                'headers': {},
                'payload_templates': [],
                'validation': {
                    'success_codes': [200, 201],
                    'error_patterns': [],
                    'live_indicators': []
                }
            }
        }
        
        # Adiciona endpoints encontrados
        for endpoint in analysis_result.get('endpoints', []):
            if endpoint.get('gateway') == primary:
                checker_template['config']['endpoints'].append({
                    'url': endpoint['url'],
                    'method': endpoint['method']
                })
                
                # Captura headers de autenticação
                headers = endpoint.get('headers', {})
                auth_headers = {k: v for k, v in headers.items() 
                              if any(x in k.lower() for x in ['auth', 'token', 'key', 'secret'])}
                checker_template['config']['headers'].update(auth_headers)
        
        # Adiciona templates de payload
        for template_info in templates:
            if template_info.get('gateway') == primary:
                checker_template['config']['payload_templates'].append(
                    template_info['template']
                )
        
        return checker_template
    
    def get_base_url(self, gateway: str) -> str:
        """Retorna URL base para cada gateway"""
        base_urls = {
            'stripe': 'https://api.stripe.com/v1/',
            'braintree': 'https://payments.braintree-api.com/',
            'adyen': 'https://checkout-test.adyen.com/v69/',
            'square': 'https://connect.squareup.com/v2/',
            'pagarme': 'https://api.pagar.me/',
            'mercadopago': 'https://api.mercadopago.com/v1/'
        }
        return base_urls.get(gateway, '')