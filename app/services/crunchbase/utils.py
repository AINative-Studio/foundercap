"""Utility functions for working with the Crunchbase API."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .models import Company, FundingRound, Investor
from .exceptions import CrunchbaseAPIError

logger = logging.getLogger(__name__)

async def normalize_company_data(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize company data from Crunchbase to our internal format.
    
    Args:
        company_data: Raw company data from Crunchbase API
        
    Returns:
        Normalized company data
    """
    try:
        # Extract basic company info
        normalized = {
            "crunchbase_id": company_data.get("uuid"),
            "name": company_data.get("name"),
            "description": company_data.get("short_description") or company_data.get("description", ""),
            "website": company_data.get("website_url") or company_data.get("homepage_url"),
            "founded_date": company_data.get("founded_on"),
            "total_funding_usd": company_data.get("total_funding_usd"),
            "last_funding_type": company_data.get("last_funding_type"),
            "last_funding_date": company_data.get("last_funding_at"),
            "crunchbase_url": f"https://www.crunchbase.com/organization/{company_data.get('permalink')}" 
                             if company_data.get("permalink") else None,
            "metadata": {
                "crunchbase": company_data,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        # Handle categories/industries if available
        if "category_groups" in company_data:
            normalized["categories"] = [
                cat["name"] 
                for group in company_data["category_groups"] 
                for cat in group.get("categories", [])
            ]
            
        # Handle locations if available
        if "headquarters_address" in company_data:
            addr = company_data["headquarters_address"]
            normalized["location"] = {
                "city": addr.get("city"),
                "region": addr.get("region"),
                "country": addr.get("country"),
                "postal_code": addr.get("postal_code"),
            }
            
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing company data: {e}", exc_info=True)
        raise CrunchbaseAPIError(f"Failed to normalize company data: {e}")

async def normalize_funding_rounds(rounds_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize funding rounds data from Crunchbase.
    
    Args:
        rounds_data: List of funding round data from Crunchbase
        
    Returns:
        List of normalized funding rounds
    """
    normalized_rounds = []
    
    for round_data in rounds_data:
        try:
            # Map Crunchbase round types to our internal format
            round_type = {
                "seed": "seed",
                "series_a": "series_a",
                "series_b": "series_b",
                "series_c": "series_c",
                "series_d": "series_d",
                "series_e": "series_e",
                "series_f": "series_f",
                "series_g": "series_g",
                "series_h": "series_h",
                "series_i": "series_i",
                "series_j": "series_j",
                "series_unknown": "other",
                "angel": "angel",
                "convertible_note": "convertible_note",
                "corporate_round": "corporate_round",
                "debt_financing": "debt",
                "equity_crowdfunding": "equity_crowdfunding",
                "grant": "grant",
                "initial_coin_offering": "ico",
                "non_equity_assistance": "grant",
                "post_ipo_debt": "debt",
                "post_ipo_equity": "post_ipo_equity",
                "post_ipo_secondary": "secondary",
                "pre_seed": "pre_seed",
                "private_equity": "private_equity",
                "secondary_market": "secondary",
                "seed_round": "seed",
            }.get(round_data.get("investment_type", "").lower(), "other")
            
            normalized = {
                "crunchbase_id": round_data.get("uuid"),
                "name": round_data.get("name"),
                "round_type": round_type,
                "announced_date": round_data.get("announced_on"),
                "raised_amount": round_data.get("money_raised"),
                "raised_currency": round_data.get("money_raised_currency"),
                "investor_count": round_data.get("investor_count"),
                "source_url": round_data.get("source_url"),
                "investors": [],
                "metadata": {
                    "crunchbase": round_data,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            
            # Add investors if available
            if "investors" in round_data:
                normalized["investors"] = [
                    {
                        "crunchbase_id": inv.get("uuid"),
                        "name": inv.get("name"),
                        "type": inv.get("type"),
                        "is_lead": inv.get("is_lead_investor", False),
                    }
                    for inv in round_data["investors"]
                ]
                
            normalized_rounds.append(normalized)
            
        except Exception as e:
            logger.error(f"Error normalizing funding round: {e}", exc_info=True)
            continue
            
    return normalized_rounds

async def get_company_with_funding(domain: str) -> Dict[str, Any]:
    """Get complete company data including funding information.
    
    Args:
        domain: Company domain (e.g., 'airbnb.com')
        
    Returns:
        Dictionary with company and funding information
    """
    from . import get_crunchbase_client
    
    client = get_crunchbase_client()
    try:
        # Get company data
        company = await client.get_company_by_domain(domain)
        if not company:
            return {"error": "Company not found on Crunchbase"}
            
        # Get funding rounds
        rounds = await client.get_company_funding_rounds(company.uuid)
        
        # Normalize data
        normalized_company = await normalize_company_data(company.dict())
        normalized_rounds = await normalize_funding_rounds([r.dict() for r in rounds])
        
        return {
            "company": normalized_company,
            "funding_rounds": normalized_rounds,
            "total_funding_rounds": len(normalized_rounds),
            "last_funding_round": max(
                (r for r in normalized_rounds if r.get("announced_date")), 
                key=lambda x: x["announced_date"],
                default=None
            )
        }
        
    except Exception as e:
        logger.error(f"Error fetching company data: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        await client.close()
