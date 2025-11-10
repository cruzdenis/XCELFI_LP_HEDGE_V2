"""
Uniswap V3 Integration - Busca posições LP via Subgraph
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


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
    fee_tier: int
    in_range: bool


class UniswapClient:
    """Cliente para interagir com Uniswap V3 via Subgraph"""
    
    def __init__(self, subgraph_url: str, wallet_address: str):
        """
        Inicializa o cliente Uniswap
        
        Args:
            subgraph_url: URL do subgraph (Base ou Mainnet)
            wallet_address: Endereço da wallet para buscar posições
        """
        self.subgraph_url = subgraph_url
        self.wallet_address = wallet_address.lower()
    
    def get_positions(self) -> List[UniswapPosition]:
        """
        Busca todas as posições LP da wallet
        
        Returns:
            Lista de posições Uniswap
        """
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
                self.subgraph_url,
                json={
                    "query": query,
                    "variables": {"owner": self.wallet_address}
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            if "errors" in data:
                return []
            
            positions_data = data.get("data", {}).get("positions", [])
            
            positions = []
            for pos in positions_data:
                try:
                    pool = pos["pool"]
                    token0 = pool["token0"]
                    token1 = pool["token1"]
                    
                    # Calcular amounts (simplificado - valores depositados menos retirados)
                    token0_amount = (
                        float(pos["depositedToken0"]) - float(pos["withdrawnToken0"])
                    ) / (10 ** int(token0["decimals"]))
                    
                    token1_amount = (
                        float(pos["depositedToken1"]) - float(pos["withdrawnToken1"])
                    ) / (10 ** int(token1["decimals"]))
                    
                    # Fees coletadas
                    fees_token0 = float(pos["collectedFeesToken0"]) / (10 ** int(token0["decimals"]))
                    fees_token1 = float(pos["collectedFeesToken1"]) / (10 ** int(token1["decimals"]))
                    
                    # Verificar se está in range (simplificado)
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
                        in_range=in_range
                    )
                    
                    positions.append(position)
                    
                except (KeyError, ValueError, TypeError):
                    continue
            
            return positions
            
        except Exception:
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
