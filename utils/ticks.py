"""
Utility functions for Uniswap V3 tick calculations.
"""
import math


def price_to_tick(price: float) -> int:
    """
    Convert price to tick.
    
    Args:
        price: Price (token1/token0)
        
    Returns:
        Tick value
    """
    return int(math.floor(math.log(price, 1.0001)))


def tick_to_price(tick: int) -> float:
    """
    Convert tick to price.
    
    Args:
        tick: Tick value
        
    Returns:
        Price (token1/token0)
    """
    return 1.0001 ** tick


def get_tick_at_sqrt_ratio(sqrt_price_x96: int) -> int:
    """
    Get tick from sqrtPriceX96.
    
    Args:
        sqrt_price_x96: Square root price in Q64.96 format
        
    Returns:
        Tick value
    """
    # Convert sqrtPriceX96 to price
    price = (sqrt_price_x96 / (2 ** 96)) ** 2
    return price_to_tick(price)


def get_sqrt_ratio_at_tick(tick: int) -> int:
    """
    Get sqrtPriceX96 from tick.
    
    Args:
        tick: Tick value
        
    Returns:
        Square root price in Q64.96 format
    """
    price = tick_to_price(tick)
    sqrt_price = math.sqrt(price)
    return int(sqrt_price * (2 ** 96))
