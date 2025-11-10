# Simple fix: just remove the has_data check and st.stop()
# This will allow the Settings tab to always be accessible

with open('app.py', 'r') as f:
    content = f.read()

# Remove the has_data check block (lines 173-192)
# Replace with just a comment
old_block = """        # Check if we have any real data
        has_data = lp_position is not None or len(hl_positions) > 0 or len(balances) > 0
        
        if not has_data:
            st.warning("⚠️ **Nenhuma posição encontrada**")
            st.info(\"\"\"
            **Como configurar:**
            
            1. Vá para a aba **⚙️ Configurações**
            2. Na seção **🔐 Credenciais**, configure:
               - Endereço público da sua wallet
               - Endereços dos contratos Aerodrome (Pool, Router)
               - Base RPC URL
            3. Certifique-se de que sua wallet possui:
               - Posições LP ativas na Aerodrome (pool ETH/BTC)
               - Posições short na Hyperliquid
            
            **Nota:** O sistema está em modo somente leitura. Configure suas credenciais para ver suas posições reais.
            \"\"\")
        else:"""

new_block = """        # Check if we have any real data
        has_data = lp_position is not None or len(hl_positions) > 0 or len(balances) > 0
        
        if not has_data:
            st.warning("⚠️ **Nenhuma posição encontrada**")
            st.info(\"\"\"
            **Como configurar:**
            
            1. Vá para a aba **⚙️ Configurações**
            2. Na seção **🔐 Credenciais**, configure:
               - Endereço público da sua wallet
               - Endereços dos contratos Aerodrome (Pool, Router)
               - Base RPC URL
            3. Certifique-se de que sua wallet possui:
               - Posições LP ativas na Aerodrome (pool ETH/BTC)
               - Posições short na Hyperliquid
            
            **Nota:** O sistema está em modo somente leitura. Configure suas credenciais para ver suas posições reais.
            \"\"\")
        
        if has_data:"""

content = content.replace(old_block, new_block)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed!")
