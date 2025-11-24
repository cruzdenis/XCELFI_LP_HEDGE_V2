"""
UX Reorganization Script
Reorganizes app.py into cleaner tab structure with sub-tabs
"""

def reorganize_app():
    # Read current app.py
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Find sections
    sections = extract_sections(content)
    
    # Build new structure
    new_content = build_new_structure(sections)
    
    # Write new app.py
    with open('app_reorganized.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Reorganization complete!")
    print("📄 New file: app_reorganized.py")
    print("🔍 Review it before replacing app.py")

def extract_sections(content):
    """Extract all major sections from current app"""
    
    # Split by major markers
    parts = {}
    
    # Header (imports, config, etc.)
    header_end = content.find("# Main tabs")
    parts['header'] = content[:header_end]
    
    # Tab 1: Config (keep as is)
    tab1_start = content.find("# ==================== TAB 1: CONFIGURAÇÃO")
    tab1_end = content.find("# ==================== TAB 2: DASHBOARD")
    parts['tab1_config'] = content[tab1_start:tab1_end]
    
    # Tab 2: Dashboard - need to extract sections
    tab2_start = tab1_end
    tab2_end = content.find("with tab3:")
    dashboard_content = content[tab2_start:tab2_end]
    
    # Extract dashboard sections
    parts['dashboard_sync'] = extract_between(dashboard_content, 
        'with tab2:', 
        'st.subheader("💼 Alocação de Capital')
    
    parts['capital_allocation'] = extract_between(dashboard_content,
        'st.subheader("💼 Alocação de Capital',
        'st.subheader("📈 Evolução do Net Worth')
    
    parts['nav_chart'] = extract_between(dashboard_content,
        'st.subheader("📈 Evolução do Net Worth',
        'st.subheader("📈 Evolução da Cota')
    
    parts['quota_chart'] = extract_between(dashboard_content,
        'st.subheader("📈 Evolução da Cota',
        '# ==================== DELTA NEUTRAL ANALYSIS')
    
    parts['delta_neutral'] = extract_between(dashboard_content,
        '# ==================== DELTA NEUTRAL ANALYSIS',
        'with tab3:')
    
    # Tab 3: Positions
    tab3_start = tab2_end
    tab3_end = content.find("with tab4:")
    parts['tab3_positions'] = content[tab3_start:tab3_end]
    
    # Tab 4: History
    tab4_start = tab3_end
    tab4_end = content.find("with tab5:")
    parts['tab4_history'] = content[tab4_start:tab4_end]
    
    # Tab 5: Executions
    tab5_start = tab4_end
    tab5_end = content.find("# ==================== TAB 6:")
    parts['tab5_executions'] = content[tab5_start:tab5_end]
    
    # Tab 6: Reserves
    tab6_start = tab5_end
    tab6_end = content.find("# Footer")
    parts['tab6_reserves'] = content[tab6_start:tab6_end]
    
    # Footer
    parts['footer'] = content[tab6_end:]
    
    return parts

def extract_between(text, start_marker, end_marker):
    """Extract text between two markers"""
    start = text.find(start_marker)
    if start == -1:
        return ""
    end = text.find(end_marker, start)
    if end == -1:
        return text[start:]
    return text[start:end]

def build_new_structure(sections):
    """Build new app structure"""
    
    new_app = []
    
    # Header
    new_app.append(sections['header'])
    
    # New tab structure
    new_app.append("""
# Main tabs - NEW CLEAN STRUCTURE
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⚙️ Configuração", 
    "📊 Dashboard", 
    "💼 Análise",
    "📈 Performance", 
    "🏬 Posições",
    "📜 Histórico",
    "🔐 Prova de Reservas"
])

""")
    
    # TAB 1: Config (unchanged)
    new_app.append(sections['tab1_config'])
    
    # TAB 2: Dashboard (CLEAN - only essentials)
    new_app.append(build_clean_dashboard(sections))
    
    # TAB 3: Análise (NEW - with sub-tabs)
    new_app.append(build_analise_tab(sections))
    
    # TAB 4: Performance (NEW)
    new_app.append(build_performance_tab(sections))
    
    # TAB 5: Posições (consolidated)
    new_app.append(build_posicoes_tab(sections))
    
    # TAB 6: Histórico (consolidated)
    new_app.append(build_historico_tab(sections))
    
    # TAB 7: Prova de Reservas (unchanged)
    new_app.append(sections['tab6_reserves'])
    
    # Footer
    new_app.append(sections['footer'])
    
    return '\n'.join(new_app)

def build_clean_dashboard(sections):
    """Build clean dashboard with only essentials"""
    return """
# ==================== TAB 2: DASHBOARD (CLEAN) ====================
with tab2:
    st.subheader("📊 Dashboard")
    st.markdown("Visão geral rápida do seu portfolio")
    
    if 'portfolio_data' not in st.session_state:
        st.warning("⚠️ Configure a API Key e Wallet na aba **Configuração** primeiro")
    else:
        data = st.session_state.portfolio_data
        portfolio = data['portfolio']
        
        # Sync button
        col_sync1, col_sync2 = st.columns([3, 1])
        
        with col_sync1:
            if 'last_sync' in st.session_state:
                st.info(f"🕐 Última sincronização: {st.session_state.last_sync}")
        
        with col_sync2:
            if st.button("🔄 Sincronizar Agora", use_container_width=True, type="primary"):
                with st.spinner("Sincronizando dados..."):
                    # Sync logic (keep existing)
                    pass
        
        st.markdown("---")
        
        # Main metric - Networth
        networth = float(portfolio.get("networth", "0"))
        
        col_main = st.columns([1])[0]
        col_main.metric(
            "💰 Patrimônio Líquido Total",
            f"${networth:,.2f}",
            help="Valor total do portfolio (LPs + Hyperliquid + Wallet)"
        )
        
        st.markdown("---")
        
        # Quick status cards
        st.markdown("### 📊 Status Rápido")
        
        col1, col2, col3 = st.columns(3)
        
        # Capital allocation status
        with col1:
            # Calculate LP percentage
            assets_by_protocol = portfolio.get("assetByProtocols", {})
            total_lp = sum([float(p.get("value", 0)) for k, p in assets_by_protocol.items() if k not in ["wallet", "hyperliquid"]])
            lp_pct = (total_lp / networth * 100) if networth > 0 else 0
            
            status_emoji = "🟢" if 70 <= lp_pct <= 90 else "🟡" if lp_pct < 70 else "🔴"
            st.metric(
                "💼 Alocação de Capital",
                f"{status_emoji} {lp_pct:.1f}% em LPs",
                help="Percentual em LPs (ideal: 70-90%)"
            )
            if st.button("Ver Detalhes →", key="goto_allocation", use_container_width=True):
                st.info("💡 Vá para a aba **Análise** → **Alocação de Capital**")
        
        # Hedge status
        with col2:
            suggestions = data.get('suggestions', [])
            hedge_status = "🟢 Balanceado" if not suggestions else f"🟡 {len(suggestions)} ações"
            st.metric(
                "⚖️ Status de Hedge",
                hedge_status,
                help="Status do hedge delta-neutral"
            )
            if st.button("Ver Detalhes →", key="goto_hedge", use_container_width=True):
                st.info("💡 Vá para a aba **Análise** → **Delta-Neutral**")
        
        # Last sync
        with col3:
            if 'last_sync' in st.session_state:
                import datetime
                # Calculate time ago
                st.metric(
                    "🕐 Última Sincronização",
                    "Recente",
                    help=st.session_state.last_sync
                )
            else:
                st.metric("🕐 Última Sincronização", "Nunca")
        
        st.markdown("---")
        
        # Quick links
        st.markdown("### 🔗 Acesso Rápido")
        
        col_link1, col_link2, col_link3, col_link4 = st.columns(4)
        
        with col_link1:
            st.markdown("**💼 [Análise](#)**")
            st.caption("Alocação + Hedge")
        
        with col_link2:
            st.markdown("**📈 [Performance](#)**")
            st.caption("NAV + Rentabilidade")
        
        with col_link3:
            st.markdown("**🏬 [Posições](#)**")
            st.caption("LPs + Shorts")
        
        with col_link4:
            st.markdown("**🔐 [Reservas](#)**")
            st.caption("Prova de Reservas")

"""

def build_analise_tab(sections):
    """Build Análise tab with sub-tabs"""
    return f"""
# ==================== TAB 3: ANÁLISE ====================
with tab3:
    st.subheader("💼 Análise de Portfolio")
    
    # Sub-tabs
    subtab1, subtab2 = st.tabs(["💼 Alocação de Capital", "⚖️ Delta-Neutral Hedge"])
    
    # Sub-tab 1: Capital Allocation
    with subtab1:
{sections['capital_allocation']}
    
    # Sub-tab 2: Delta-Neutral
    with subtab2:
{sections['delta_neutral']}

"""

def build_performance_tab(sections):
    """Build Performance tab"""
    return f"""
# ==================== TAB 4: PERFORMANCE ====================
with tab4:
    st.subheader("📈 Performance do Portfolio")
    
{sections['nav_chart']}
    
    st.markdown("---")
    
{sections['quota_chart']}

"""

def build_posicoes_tab(sections):
    """Build consolidated Posições tab"""
    # Extract LP and Short sections from tab3
    return f"""
# ==================== TAB 5: POSIÇÕES ====================
with tab5:
    st.subheader("🏬 Posições")
    
    # Sub-tabs
    subtab1, subtab2 = st.tabs(["🏬 Posições LP", "📉 Posições Short"])
    
    # Sub-tab 1: LP Positions
    with subtab1:
{sections['tab3_positions']}
    
    # Sub-tab 2: Short Positions (extracted from tab3)
    with subtab2:
        if 'portfolio_data' not in st.session_state:
            st.info("ℹ️ Sincronize os dados na aba **Dashboard** primeiro")
        else:
            data = st.session_state.portfolio_data
            perp_positions = data.get('perp_positions', [])
            
            if not perp_positions:
                st.info("ℹ️ Nenhuma posição short encontrada")
            else:
                st.markdown("### 📉 Posições Short (Hyperliquid)")
                
                for pos in perp_positions:
                    if pos.size < 0:  # Short position
                        with st.expander(f"🔻 {pos.symbol} Short - Size: {abs(pos.size):.6f}"):
                            col1, col2, col3, col4 = st.columns(4)
                            
                            col1.metric("Size", f"{abs(pos.size):.6f}")
                            col2.metric("Entry Price", f"${pos.entry_price:,.2f}")
                            col3.metric("Mark Price", f"${pos.mark_price:,.2f}")
                            col4.metric("PnL", f"${pos.open_pnl:,.2f}")
                            
                            st.markdown(f"**Position Value:** ${pos.position_value:,.2f}")
                            st.markdown(f"**Margin Used:** ${pos.margin_used:,.2f}")
                            st.markdown(f"**Leverage:** {pos.leverage}")
                            st.markdown(f"**Funding (All-Time):** ${pos.funding_all_time:,.2f}")

"""

def build_historico_tab(sections):
    """Build consolidated Histórico tab"""
    return f"""
# ==================== TAB 6: HISTÓRICO ====================
with tab6:
    st.subheader("📜 Histórico")
    
    # Sub-tabs
    subtab1, subtab2 = st.tabs(["📜 Sincronizações", "📈 Execuções"])
    
    # Sub-tab 1: Sync History
    with subtab1:
{sections['tab4_history']}
    
    # Sub-tab 2: Execution History
    with subtab2:
{sections['tab5_executions']}

"""

if __name__ == "__main__":
    reorganize_app()
