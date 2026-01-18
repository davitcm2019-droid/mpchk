# run_checker.py
#!/usr/bin/env python3
"""
Sistema Global de Checker de Cartões
Uso: python run_checker.py [opções]
"""

import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='Sistema de Checker de Cartões')
    
    parser.add_argument('--template', '-t', required=True,
                       help='Arquivo de template do checkout (JSON)')
    parser.add_argument('--bins', '-b', required=True,
                       help='Lista de BINs (ex: 456735,515735 ou arquivo .txt)')
    parser.add_argument('--quantity', '-q', type=int, default=100,
                       help='Quantidade por BIN (padrão: 100)')
    parser.add_argument('--threads', '-th', type=int, default=50,
                       help='Threads simultâneas (padrão: 50)')
    parser.add_argument('--proxies', '-p', 
                       help='Arquivo com lista de proxies (opcional)')
    parser.add_argument('--output', '-o', default='results',
                       help='Prefixo para arquivos de saída')
    
    args = parser.parse_args()
    
    # Verifica se template existe
    if not os.path.exists(args.template):
        print(f"Erro: Template {args.template} não encontrado!")
        sys.exit(1)
    
    # Carrega BINs
    if os.path.exists(args.bins):
        # Lê de arquivo
        with open(args.bins, 'r') as f:
            bins = [line.strip() for line in f if line.strip()]
    else:
        # Assume que é lista separada por vírgulas
        bins = [b.strip() for b in args.bins.split(',')]
    
    if not bins:
        print("Erro: Nenhum BIN fornecido!")
        sys.exit(1)
    
    print(f"""
    ╔══════════════════════════════════════╗
    ║    SISTEMA DE CHECKER DE CARTÕES     ║
    ╚══════════════════════════════════════╝
    
    Configuração:
    • Template: {args.template}
    • BINs: {len(bins)} encontrados
    • Cartões por BIN: {args.quantity}
    • Total de cartões: {len(bins) * args.quantity}
    • Threads: {args.threads}
    • Proxies: {'Sim' if args.proxies else 'Não'}
    """)
    
    # Inicializa sistema
    from main_checker import CardCheckerSystem
    
    checker = CardCheckerSystem()
    
    # Carrega proxies se fornecido
    if args.proxies:
        checker.load_proxies(args.proxies)
    
    # Carrega template
    template = checker.load_checkout_template(args.template)
    
    if not template:
        print("Erro: Não foi possível carregar o template!")
        sys.exit(1)
    
    # Configura checker
    checker.setup_checker(template['config'])
    
    # Gera lista de cartões
    print("\nGerando cartões...")
    cards = checker.generate_card_list(bins, args.quantity)
    
    # Executa verificação
    print(f"\nIniciando verificação de {len(cards)} cartões...")
    results = checker.run_check(cards, template['config'])
    
    # Mostra resultados
    print(f"""
    ╔══════════════════════════════════════╗
    ║           RESULTADOS FINAIS          ║
    ╚══════════════════════════════════════╝
    
    • Cartões testados: {results['total_tested']}
    • Cartões LIVE: {results['live_count']}
    • Taxa de sucesso: {results['success_rate']:.2f}%
    
    Arquivos salvos:
    • results_*.json - Todos os resultados
    • lives_*.txt - Apenas cartões LIVE
    
    {results['live_count']} cartões válidos encontrados!
    """)

if __name__ == '__main__':
    main()