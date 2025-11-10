"""
Uniswap V3 Integration - Busca posições LP via Subgraph
Suporta múltiplas redes (Base, Arbitrum, Ethereum, Optimism, Polygon)
Usa The Graph Gateway para redes que requerem API key
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


# Subgraph IDs para The Graph Gateway (redes que requerem API key)
GATEWAY_SUBGRAPH_IDS = {
    "arbitrum": "FQ6JYszEKApsBpAmiHesRsd9Ygc6mzmpNRANeVQFYoVX",
    "optimism": "Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj",
    "polygon": "3hCPRGf4z88VC5rsBKU5AA9FBBq5nF3jbKJG7VZCbhjm",
}

# Endpoints públicos que não requerem API key
PUBLIC_SUBGRAPHS = {
    "base": "https://api.studio.thegraph.com/query/48211/uniswap-v3-base/version/latest",
    "ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
    "celo": "https://api.thegraph.com/subgraphs/name/jesse-sawa/uniswap-celo",
    "bsc": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-bsc"
}


@dataclass
class UniswapPosition:
    """Representa uma posição LP no Uniswap V3"""
    id: str
    token0_symbol: str
    token1_symbol: str
    token0_amount: float
    token1_amount: float
    liquidity: float
    fees_token0: float
    fees_token1: float
    pool_address: str
    fee_tier: float
    in_range: bool
    network: str  # Rede onde a posição está


class UniswapClient:
    """Cliente para interagir com Uniswap V3 via Subgraph em múltiplas redes"""
    
    def __init__(self, wallet_address: str, networks: List[str] = None, graph_api_key: str = None):
        """
        Inicializa o cliente Uniswap
        
        Args:
            wallet_address: Endereço da wallet para buscar posições
            networks: Lista de redes para buscar (default: todas disponíveis)
            graph_api_key: API key do The Graph Gateway (necessária para Arbitrum, Optimism, Polygon)
        """
        self.wallet_address = wallet_address.lower()
        self.graph_api_key = graph_api_key
        
        # Todas as redes disponíveis
        all_networks = list(PUBLIC_SUBGRAPHS.keys()) + list(GATEWAY_SUBGRAPH_IDS.keys())
        self.networks = networks or all_networks
    
    def get_positions(self) -> List[UniswapPosition]:
        """
        Busca todas as posições LP da wallet em todas as redes configuradas
        
        Returns:
            Lista de posições Uniswap de todas as redes
        """
        all_positions = []
        
        for network in self.networks:
            try:
                network_positions = self._get_positions_from_network(network)
                all_positions.extend(network_positions)
            except Exception as e:
                print(f"Erro ao buscar posições de {network}: {e}")
                continue
        
        return all_positions
    
    def _get_subgraph_url(self, network: str) -> Optional[str]:
        """
        Retorna a URL do subgraph para uma rede específica
        
        Args:
            network: Nome da rede
            
        Returns:
            URL do subgraph ou None se não disponível
        """
        # Verifica se é uma rede pública
        if network in PUBLIC_SUBGRAPHS:
            return PUBLIC_SUBGRAPHS[network]
        
        # Verifica se é uma rede que requer Gateway
        if network in GATEWAY_SUBGRAPH_IDS:
            if not self.graph_api_key:
                print(f"⚠️ {network.capitalize()} requer The Graph API key. Configure nas configurações.")
                return None
            
            subgraph_id = GATEWAY_SUBGRAPH_IDS[network]
            return f"https://gateway.thegraph.com/api/{self.graph_api_key}/subgraphs/id/{subgraph_id}"
        
        print(f"Rede '{network}' não suportada")
        return None
    
    def _get_positions_from_network(self, network: str) -> List[UniswapPosition]:
        """
        Busca posições LP de uma rede específica
        
        Args:
            network: Nome da rede (base, arbitrum, ethereum, etc)
            
        Returns:
            Lista de posições da rede especificada
        """
        subgraph_url = self._get_subgraph_url(network)
        if not subgraph_url:
            return []
        
        query = """
        query ($owner: String!) {
          positions(where: {owner: $owner, liquidity_gt: "0"}) {
            id
            liquidity
            depositedToken0
            depositedToken1
            withdrawnToken0
            withdrawnToken1
            collectedFeesToken0
            collectedFeesToken1
            pool {
              id
              token0 {
                id
                symbol
                decimals
              }
              token1 {
                id
                symbol
                decimals
              }
              feeTier
              sqrtPrice
              tick
            }
            tickLower {
              tickIdx
            }
            tickUpper {
              tickIdx
            }
          }
        }
        """
        
        try:
            response = requests.post(
                subgraph_url,
                json={
                    "query": query,
                    "variables": {"owner": self.wallet_address}
                },
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"Erro HTTP {response.status_code} ao consultar {network}")
                return []
            
            data = response.json()
            
            if "errors" in data:
                print(f"Erros GraphQL de {network}: {data['errors']}")
                return []
            
            positions_data = data.get("data", {}).get("positions", [])
            
            positions = []
            for pos in positions_data:
                try:
                    pool = pos["pool"]
                    token0 = pool["token0"]
                    token1 = pool["token1"]
                    
                    # Calcular amounts (valores depositados menos retirados)
                    token0_amount = (
                        float(pos["depositedToken0"]) - float(pos["withdrawnToken0"])
                    ) / (10 ** int(token0["decimals"]))
                    
                    token1_amount = (
                        float(pos["depositedToken1"]) - float(pos["withdrawnToken1"])
                    ) / (10 ** int(token1["decimals"]))
                    
                    # Fees coletadas
                    fees_token0 = float(pos["collectedFeesToken0"]) / (10 ** int(token0["decimals"]))
                    fees_token1 = float(pos["collectedFeesToken1"]) / (10 ** int(token1["decimals"]))
                    
                    # Verificar se está in range
                    current_tick = int(pool["tick"])
                    tick_lower = int(pos["tickLower"]["tickIdx"])
                    tick_upper = int(pos["tickUpper"]["tickIdx"])
                    in_range = tick_lower <= current_tick <= tick_upper
                    
                    position = UniswapPosition(
                        id=pos["id"],
                        token0_symbol=token0["symbol"],
                        token1_symbol=token1["symbol"],
                        token0_amount=token0_amount,
                        token1_amount=token1_amount,
                        liquidity=float(pos["liquidity"]),
                        fees_token0=fees_token0,
                        fees_token1=fees_token1,
                        pool_address=pool["id"],
                        fee_tier=int(pool["feeTier"]) / 10000,  # Convert to percentage
                        in_range=in_range,
                        network=network.capitalize()
                    )
                    
                    positions.append(position)
                    
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Erro ao processar posição de {network}: {e}")
                    continue
            
            return positions
            
        except Exception as e:
            print(f"Erro de rede ao consultar {network}: {e}")
            return []
    
    def get_total_value_usd(self, positions: List[UniswapPosition], token_prices: Dict[str, float]) -> float:
        """
        Calcula o valor total em USD das posições
        
        Args:
            positions: Lista de posições
            token_prices: Dict com preços dos tokens {symbol: price_usd}
            
        Returns:
            Valor total em USD
        """
        total = 0.0
        
        for pos in positions:
            token0_value = pos.token0_amount * token_prices.get(pos.token0_symbol, 0)
            token1_value = pos.token1_amount * token_prices.get(pos.token1_symbol, 0)
            total += token0_value + token1_value
        
        return total
