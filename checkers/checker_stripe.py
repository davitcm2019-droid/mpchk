import requests
import time

class StripeChecker(CheckerBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.session = requests.Session()
        self.api_key = config.get('api_key', '')
        self.endpoint = 'https://api.stripe.com/v1/payment_methods'
        
    def test_card(self, card_data: Dict, gateway_config: Dict) -> Dict:
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Stripe-Version': '2023-10-16'
            }
            
            payload = {
                'type': 'card',
                'card[number]': card_data['card_number'],
                'card[exp_month]': card_data['exp_month'],
                'card[exp_year]': card_data['exp_year'],
                'card[cvc]': card_data['cvv']
            }
            
            response = self.session.post(
                self.endpoint,
                headers=headers,
                data=payload,
                timeout=10
            )
            
            result = {
                'card': card_data['card_number'],
                'status': 'unknown',
                'response_code': response.status_code,
                'response_text': response.text[:200],
                'gateway': 'stripe'
            }
            
            if response.status_code == 200:
                result['status'] = 'live'
                self.live_cards.append(card_data)
            elif response.status_code == 402:
                result['status'] = 'dead'
            else:
                result['status'] = 'error'
            
            return result
            
        except Exception as e:
            return {
                'card': card_data.get('card_number', ''),
                'status': 'error',
                'error': str(e),
                'gateway': 'stripe'
            }