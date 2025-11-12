"""
Demo Test with Simulated Data
Demonstrates delta-neutral analysis without requiring Octav.fi API key
"""

from delta_neutral_analyzer import DeltaNeutralAnalyzer


def main():
    """Main demo function with simulated data"""
    
    print("=" * 80)
    print("XCELFI LP HEDGE V3 - DEMO COM DADOS SIMULADOS")
    print("=" * 80)
    print()
    
    # Simulated data based on actual Octav.fi observations
    print("📍 Wallet Address: 0xc1E18438Fed146D814418364134fE28cC8622B5C")
    print("💰 Net Worth: $102.70 (simulado)")
    print()
    
    # LP Positions (from Revert Finance on Arbitrum)
    print("-" * 80)
    print("🏦 POSIÇÕES LP (Liquidity Provider)")
    print("-" * 80)
    print()
    print("   Revert Finance (Arbitrum):")
    print("      WBTC/WETH Pool:")
    print("         WBTC: 0.0004 @ $103,188.39 = $41.28")
    print("         WETH: 0.0125 @ $3,445.93 = $43.07")
    print()
    
    lp_balances = {
        "BTC": 0.0004,
        "ETH": 0.0125
    }
    
    print("   📊 Balanços Agregados LP:")
    for token, balance in sorted(lp_balances.items()):
        print(f"      {token}: {balance:.6f}")
    print()
    
    # Short Positions (from Hyperliquid)
    print("-" * 80)
    print("📉 POSIÇÕES SHORT (Hyperliquid)")
    print("-" * 80)
    print()
    print("   BTC SHORT:")
    print("      Size: -0.0004")
    print("      Mark Price: $103,159.00")
    print("      Position Value: $40.23")
    print("      Leverage: 40x")
    print("      Open P&L: $3.72")
    print()
    print("   ETH SHORT:")
    print("      Size: -0.0133")
    print("      Mark Price: $3,439.20")
    print("      Position Value: $45.74")
    print("      Leverage: 20x")
    print("      Open P&L: $8.93")
    print()
    
    short_balances = {
        "BTC": 0.0004,
        "ETH": 0.0133
    }
    
    print("   📊 Balanços Agregados Short:")
    for token, balance in sorted(short_balances.items()):
        print(f"      {token}: {balance:.6f}")
    print()
    
    # Perform delta-neutral analysis
    print("-" * 80)
    print("🎯 ANÁLISE DELTA NEUTRAL")
    print("-" * 80)
    print()
    
    analyzer = DeltaNeutralAnalyzer(tolerance_pct=5.0)
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
            print("   🔺 AUMENTAR SHORT:")
            for token, amount in actions["increase_short"].items():
                print(f"      • {token}: +{amount:.6f}")
            print()
        
        if actions["decrease_short"]:
            print("   🔻 DIMINUIR SHORT:")
            for token, amount in actions["decrease_short"].items():
                print(f"      • {token}: -{amount:.6f}")
            print()
        
        print("   ⚠️  NOTA: Execução via Hyperliquid API requer:")
        print("      - API Key da Hyperliquid")
        print("      - API Secret da Hyperliquid")
        print("      - Implementação do cliente Hyperliquid")
        print()
    
    # Additional analysis
    print("-" * 80)
    print("📊 ANÁLISE DETALHADA")
    print("-" * 80)
    print()
    
    for s in suggestions:
        print(f"   {s.token}:")
        print(f"      Status: {s.status.upper()}")
        print(f"      LP Balance: {s.lp_balance:.6f}")
        print(f"      Short Balance: {s.short_balance:.6f}")
        print(f"      Diferença Absoluta: {s.difference:+.6f}")
        print(f"      Diferença Percentual: {s.difference_pct:.2f}%")
        
        if s.action != "none":
            print(f"      Ação Recomendada: {s.action.upper()}")
            print(f"      Quantidade de Ajuste: {s.adjustment_amount:.6f}")
        else:
            print(f"      ✅ Nenhuma ação necessária")
        print()
    
    print("=" * 80)
    print("✅ DEMO CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print()
    print("📝 PRÓXIMOS PASSOS:")
    print()
    print("   1. Obter API Key do Octav.fi em: https://data.octav.fi")
    print("   2. Configurar: export OCTAV_API_KEY='sua_chave'")
    print("   3. Executar: python test_app.py")
    print()
    print("   Para execução de trades:")
    print("   4. Obter API Keys da Hyperliquid")
    print("   5. Implementar cliente Hyperliquid para execução")
    print("   6. Testar com valores pequenos primeiro!")
    print()


if __name__ == "__main__":
    main()
