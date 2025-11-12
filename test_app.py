"""
Test Application for XCELFI LP Hedge V3
Tests Octav.fi API integration and delta-neutral analysis
"""

import os
import sys
from octav_client import OctavClient
from delta_neutral_analyzer import DeltaNeutralAnalyzer


def main():
    """Main test function"""
    
    print("=" * 80)
    print("XCELFI LP HEDGE V3 - TEST APPLICATION")
    print("=" * 80)
    print()
    
    # Configuration
    WALLET_ADDRESS = "0xc1E18438Fed146D814418364134fE28cC8622B5C"
    OCTAV_API_KEY = os.getenv("OCTAV_API_KEY", "")
    
    if not OCTAV_API_KEY:
        print("❌ ERRO: OCTAV_API_KEY não configurada!")
        print("   Configure a variável de ambiente OCTAV_API_KEY com sua chave da API do Octav.fi")
        print()
        print("   Exemplo:")
        print("   export OCTAV_API_KEY='sua_chave_aqui'")
        print()
        return
    
    print(f"📍 Wallet Address: {WALLET_ADDRESS}")
    print(f"🔑 Octav API Key: {OCTAV_API_KEY[:10]}...")
    print()
    
    # Initialize clients
    print("🔄 Inicializando Octav.fi client...")
    octav_client = OctavClient(OCTAV_API_KEY)
    
    print("🔄 Inicializando Delta Neutral Analyzer...")
    analyzer = DeltaNeutralAnalyzer(tolerance_pct=5.0)
    print()
    
    # Fetch portfolio data
    print("-" * 80)
    print("📊 BUSCANDO DADOS DO PORTFÓLIO...")
    print("-" * 80)
    print()
    
    portfolio = octav_client.get_portfolio(WALLET_ADDRESS)
    
    if not portfolio:
        print("❌ Erro ao buscar dados do portfólio!")
        return
    
    # Display basic portfolio info
    networth = portfolio.get("networth", "0")
    print(f"💰 Net Worth: ${networth}")
    print()
    
    # Extract LP positions
    print("-" * 80)
    print("🏦 POSIÇÕES LP (Liquidity Provider)")
    print("-" * 80)
    print()
    
    lp_positions = octav_client.extract_lp_positions(portfolio)
    
    if lp_positions:
        for pos in lp_positions:
            print(f"   {pos.protocol} ({pos.chain}):")
            print(f"      {pos.token_symbol}: {pos.balance:.6f} @ ${pos.price:.2f} = ${pos.value:.2f}")
        print()
    else:
        print("   Nenhuma posição LP encontrada.")
        print()
    
    # Get aggregated LP token balances
    lp_balances = octav_client.get_lp_token_balances(WALLET_ADDRESS)
    
    print("   📊 Balanços Agregados LP:")
    for token, balance in sorted(lp_balances.items()):
        print(f"      {token}: {balance:.6f}")
    print()
    
    # Extract perpetual positions
    print("-" * 80)
    print("📉 POSIÇÕES SHORT (Hyperliquid)")
    print("-" * 80)
    print()
    
    perp_positions = octav_client.extract_perp_positions(portfolio)
    
    if perp_positions:
        for pos in perp_positions:
            direction = "SHORT" if pos.size < 0 else "LONG"
            print(f"   {pos.symbol} {direction}:")
            print(f"      Size: {pos.size:.6f}")
            print(f"      Mark Price: ${pos.mark_price:.2f}")
            print(f"      Position Value: ${pos.position_value:.2f}")
        print()
    else:
        print("   Nenhuma posição perpétua encontrada.")
        print()
    
    # Get aggregated short balances
    short_balances = octav_client.get_short_balances(WALLET_ADDRESS)
    
    print("   📊 Balanços Agregados Short:")
    for token, balance in sorted(short_balances.items()):
        print(f"      {token}: {balance:.6f}")
    print()
    
    # Perform delta-neutral analysis
    print("-" * 80)
    print("🎯 ANÁLISE DELTA NEUTRAL")
    print("-" * 80)
    print()
    
    suggestions = analyzer.compare_positions(lp_balances, short_balances)
    
    # Print formatted suggestions
    report = analyzer.format_suggestions(suggestions)
    print(report)
    print()
    
    # Get action summary
    actions = analyzer.get_action_summary(suggestions)
    
    if actions["increase_short"] or actions["decrease_short"]:
        print("-" * 80)
        print("📋 RESUMO DE AÇÕES PARA HYPERLIQUID API")
        print("-" * 80)
        print()
        
        if actions["increase_short"]:
            print("   AUMENTAR SHORT:")
            for token, amount in actions["increase_short"].items():
                print(f"      • {token}: +{amount:.6f}")
        
        if actions["decrease_short"]:
            print("   DIMINUIR SHORT:")
            for token, amount in actions["decrease_short"].items():
                print(f"      • {token}: -{amount:.6f}")
        
        print()
        print("   ⚠️  NOTA: Execução via Hyperliquid API requer configuração adicional")
        print()
    
    print("=" * 80)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
