"""Advanced Economy System for Historia Lite

Features:
- Bilateral trade agreements
- National debt and reserves
- Trade balance
- Economic sanctions effects
- Trade dependencies
"""
import logging
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Types of trade agreements"""
    STANDARD = "standard"           # Normal trade
    FREE_TRADE = "free_trade"       # FTA - reduced tariffs
    CUSTOMS_UNION = "customs_union" # Shared external tariffs
    EMBARGO = "embargo"             # No trade
    SANCTIONS = "sanctions"         # Limited trade


class TradeAgreement(BaseModel):
    """Bilateral trade agreement between two countries"""
    id: str
    country_a: str
    country_b: str
    trade_type: TradeType = TradeType.STANDARD
    volume: int = 50  # 0-100 (trade intensity)
    balance: int = 0  # -100 to +100 (negative = deficit for A)
    year_signed: int = 2025
    is_active: bool = True

    def get_partner(self, country_id: str) -> Optional[str]:
        """Get the other country in the agreement"""
        if country_id == self.country_a:
            return self.country_b
        elif country_id == self.country_b:
            return self.country_a
        return None


class DebtHolder(str, Enum):
    """Who holds the debt"""
    DOMESTIC = "domestic"
    FOREIGN = "foreign"
    IMF = "imf"
    WORLD_BANK = "world_bank"
    CHINA = "china"


class NationalDebt(BaseModel):
    """National debt status for a country"""
    country_id: str
    debt_to_gdp: int = 50  # Percentage (0-300)
    foreign_debt_share: int = 30  # % of debt held by foreigners
    debt_holders: Dict[str, int] = Field(default_factory=dict)  # Holder -> amount
    interest_rate: float = 3.0
    credit_rating: str = "A"  # AAA, AA, A, BBB, BB, B, CCC, CC, C, D
    is_in_default: bool = False
    default_year: Optional[int] = None


class ForeignReserves(BaseModel):
    """Foreign currency reserves"""
    country_id: str
    total_reserves: int = 50  # 0-100 (months of imports)
    usd_share: int = 60  # % in USD
    eur_share: int = 20  # % in EUR
    gold_share: int = 10  # % in gold
    cny_share: int = 5   # % in CNY
    other_share: int = 5


class EconomyManager:
    """Manages global economic interactions"""

    def __init__(self):
        self.trade_agreements: Dict[str, TradeAgreement] = {}
        self.national_debts: Dict[str, NationalDebt] = {}
        self.foreign_reserves: Dict[str, ForeignReserves] = {}

    def reset(self):
        """Reset economy state"""
        self.trade_agreements.clear()
        self.national_debts.clear()
        self.foreign_reserves.clear()

    # ==================== Trade Agreements ====================

    def create_trade_agreement(
        self,
        country_a: str,
        country_b: str,
        trade_type: TradeType,
        volume: int,
        year: int,
    ) -> TradeAgreement:
        """Create a new trade agreement"""
        agreement_id = f"{country_a}_{country_b}_trade"

        agreement = TradeAgreement(
            id=agreement_id,
            country_a=country_a,
            country_b=country_b,
            trade_type=trade_type,
            volume=volume,
            year_signed=year,
        )

        self.trade_agreements[agreement_id] = agreement
        logger.info(f"Trade agreement created: {country_a} <-> {country_b}")
        return agreement

    def get_trade_partners(self, country_id: str) -> List[Tuple[str, TradeAgreement]]:
        """Get all trade partners for a country"""
        partners = []
        for agreement in self.trade_agreements.values():
            if not agreement.is_active:
                continue
            partner = agreement.get_partner(country_id)
            if partner:
                partners.append((partner, agreement))
        return partners

    def get_trade_volume(self, country_id: str) -> int:
        """Get total trade volume for a country"""
        total = 0
        for partner, agreement in self.get_trade_partners(country_id):
            if agreement.trade_type != TradeType.EMBARGO:
                total += agreement.volume
        return total

    def get_trade_balance(self, country_id: str) -> int:
        """Get trade balance (positive = surplus, negative = deficit)"""
        balance = 0
        for partner, agreement in self.get_trade_partners(country_id):
            if country_id == agreement.country_a:
                balance += agreement.balance
            else:
                balance -= agreement.balance
        return balance

    def apply_sanctions(
        self,
        sanctioner: str,
        target: str,
        world: "World",
    ) -> Dict[str, int]:
        """Apply economic sanctions effects"""
        effects = {"target_economy": 0, "sanctioner_economy": 0}

        # Find existing trade agreement
        agreement_id = f"{sanctioner}_{target}_trade"
        alt_id = f"{target}_{sanctioner}_trade"

        agreement = self.trade_agreements.get(
            agreement_id, self.trade_agreements.get(alt_id)
        )

        if agreement and agreement.is_active:
            # Reduce trade volume
            old_volume = agreement.volume
            agreement.volume = max(0, agreement.volume - 30)
            agreement.trade_type = TradeType.SANCTIONS

            # Economic damage proportional to trade dependency
            target_country = world.get_country(target)
            if target_country:
                damage = min(10, old_volume // 10)
                effects["target_economy"] = -damage

            # Sanctioner also loses trade
            effects["sanctioner_economy"] = -max(1, old_volume // 20)

        return effects

    def process_trade_tick(self, world: "World") -> List[dict]:
        """Process trade effects for one tick"""
        events = []

        for country in world.get_all_countries():
            # Calculate trade benefits
            trade_volume = self.get_trade_volume(country.id)
            trade_balance = self.get_trade_balance(country.id)

            # Trade volume boosts economy
            if trade_volume > 50:
                economy_boost = min(3, trade_volume // 30)
                country.economy = min(100, country.economy + economy_boost)

            # Trade deficit hurts economy slightly
            if trade_balance < -30:
                country.economy = max(0, country.economy - 1)

            # Trade surplus boosts economy
            if trade_balance > 30:
                country.economy = min(100, country.economy + 1)

        return events

    # ==================== National Debt ====================

    def get_or_create_debt(self, country_id: str) -> NationalDebt:
        """Get or create debt record for a country"""
        if country_id not in self.national_debts:
            self.national_debts[country_id] = NationalDebt(country_id=country_id)
        return self.national_debts[country_id]

    def increase_debt(
        self,
        country_id: str,
        amount: int,
        holder: DebtHolder = DebtHolder.FOREIGN,
    ) -> NationalDebt:
        """Increase country's debt"""
        debt = self.get_or_create_debt(country_id)
        debt.debt_to_gdp = min(300, debt.debt_to_gdp + amount)

        # Update holders
        holder_name = holder.value
        current = debt.debt_holders.get(holder_name, 0)
        debt.debt_holders[holder_name] = current + amount

        # Update credit rating
        self._update_credit_rating(debt)

        logger.info(f"{country_id} debt increased by {amount}% to {debt.debt_to_gdp}%")
        return debt

    def pay_debt(self, country_id: str, amount: int) -> NationalDebt:
        """Pay down country's debt"""
        debt = self.get_or_create_debt(country_id)
        debt.debt_to_gdp = max(0, debt.debt_to_gdp - amount)

        self._update_credit_rating(debt)

        logger.info(f"{country_id} paid {amount}% debt, now at {debt.debt_to_gdp}%")
        return debt

    def _update_credit_rating(self, debt: NationalDebt):
        """Update credit rating based on debt level"""
        ratio = debt.debt_to_gdp

        if ratio < 30:
            debt.credit_rating = "AAA"
            debt.interest_rate = 2.0
        elif ratio < 50:
            debt.credit_rating = "AA"
            debt.interest_rate = 2.5
        elif ratio < 70:
            debt.credit_rating = "A"
            debt.interest_rate = 3.0
        elif ratio < 90:
            debt.credit_rating = "BBB"
            debt.interest_rate = 4.0
        elif ratio < 120:
            debt.credit_rating = "BB"
            debt.interest_rate = 5.5
        elif ratio < 150:
            debt.credit_rating = "B"
            debt.interest_rate = 7.0
        elif ratio < 200:
            debt.credit_rating = "CCC"
            debt.interest_rate = 10.0
        else:
            debt.credit_rating = "D"
            debt.interest_rate = 15.0
            debt.is_in_default = True

    def process_debt_tick(self, world: "World") -> List[dict]:
        """Process debt effects for one tick"""
        events = []

        for country in world.get_all_countries():
            debt = self.get_or_create_debt(country.id)

            # Interest payments affect economy
            if debt.debt_to_gdp > 100:
                interest_cost = int(debt.interest_rate / 2)
                country.economy = max(0, country.economy - interest_cost)

                if interest_cost > 2:
                    events.append({
                        "type": "debt_crisis",
                        "country": country.id,
                        "message_fr": f"{country.name_fr} souffre de sa dette ({debt.debt_to_gdp}% du PIB)",
                    })

            # High debt reduces stability
            if debt.debt_to_gdp > 150:
                country.stability = max(0, country.stability - 2)

            # Default consequences
            if debt.is_in_default:
                country.economy = max(0, country.economy - 5)
                country.stability = max(0, country.stability - 3)

        return events

    # ==================== Foreign Reserves ====================

    def get_or_create_reserves(self, country_id: str) -> ForeignReserves:
        """Get or create reserves record"""
        if country_id not in self.foreign_reserves:
            self.foreign_reserves[country_id] = ForeignReserves(country_id=country_id)
        return self.foreign_reserves[country_id]

    def add_reserves(self, country_id: str, amount: int):
        """Add to foreign reserves"""
        reserves = self.get_or_create_reserves(country_id)
        reserves.total_reserves = min(100, reserves.total_reserves + amount)

    def spend_reserves(self, country_id: str, amount: int) -> bool:
        """Spend foreign reserves (returns False if insufficient)"""
        reserves = self.get_or_create_reserves(country_id)
        if reserves.total_reserves >= amount:
            reserves.total_reserves -= amount
            return True
        return False

    def process_reserves_tick(self, world: "World") -> List[dict]:
        """Process reserve effects"""
        events = []

        for country in world.get_all_countries():
            reserves = self.get_or_create_reserves(country.id)

            # Trade surplus builds reserves
            balance = self.get_trade_balance(country.id)
            if balance > 20:
                reserves.total_reserves = min(100, reserves.total_reserves + 2)

            # Trade deficit depletes reserves
            if balance < -20:
                reserves.total_reserves = max(0, reserves.total_reserves - 2)

            # Low reserves = vulnerability
            if reserves.total_reserves < 20:
                country.stability = max(0, country.stability - 1)

                events.append({
                    "type": "low_reserves",
                    "country": country.id,
                    "message_fr": f"{country.name_fr} a des reserves faibles ({reserves.total_reserves} mois)",
                })

        return events

    # ==================== Economic Analysis ====================

    def get_economic_summary(self, country_id: str) -> Dict:
        """Get comprehensive economic summary"""
        debt = self.get_or_create_debt(country_id)
        reserves = self.get_or_create_reserves(country_id)

        partners = self.get_trade_partners(country_id)
        trade_volume = self.get_trade_volume(country_id)
        trade_balance = self.get_trade_balance(country_id)

        return {
            "country_id": country_id,
            "trade": {
                "partners": len(partners),
                "total_volume": trade_volume,
                "balance": trade_balance,
                "balance_status": "surplus" if trade_balance > 0 else "deficit" if trade_balance < 0 else "balanced",
            },
            "debt": {
                "debt_to_gdp": debt.debt_to_gdp,
                "credit_rating": debt.credit_rating,
                "interest_rate": debt.interest_rate,
                "is_in_default": debt.is_in_default,
            },
            "reserves": {
                "total_months": reserves.total_reserves,
                "usd_share": reserves.usd_share,
                "gold_share": reserves.gold_share,
            },
            "health": self._calculate_economic_health(debt, reserves, trade_balance),
        }

    def _calculate_economic_health(
        self,
        debt: NationalDebt,
        reserves: ForeignReserves,
        trade_balance: int,
    ) -> str:
        """Calculate overall economic health"""
        score = 100

        # Debt penalty
        if debt.debt_to_gdp > 60:
            score -= (debt.debt_to_gdp - 60) // 2

        # Default is critical
        if debt.is_in_default:
            score -= 30

        # Reserves bonus/penalty
        if reserves.total_reserves < 20:
            score -= 20
        elif reserves.total_reserves > 60:
            score += 10

        # Trade balance
        if trade_balance < -30:
            score -= 10
        elif trade_balance > 30:
            score += 10

        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "moderate"
        elif score >= 20:
            return "weak"
        else:
            return "critical"


# Global instance
economy_manager = EconomyManager()
