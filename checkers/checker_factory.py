from .stripe_checker import StripeChecker
from .braintree_checker import BraintreeChecker
from .generic_checker import GenericChecker

class CheckerFactory:
    @staticmethod
    def create_checker(gateway: str, config: Dict) -> CheckerBase:
        """Factory para criar checker específico"""
        checkers = {
            'stripe': StripeChecker,
            'braintree': BraintreeChecker,
            'adyen': GenericChecker,
            'square': GenericChecker,
            'pagarme': GenericChecker,
            'mercadopago': GenericChecker
        }
        
        checker_class = checkers.get(gateway.lower(), GenericChecker)
        return checker_class(config)