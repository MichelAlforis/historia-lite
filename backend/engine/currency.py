"""Currency and monetary system management

Handles:
- Currency zones (USD, EUR, CFA franc, etc.)
- Currency dependency/dollarization
- Crypto adoption (Bitcoin, CBDC)
- Monetary sovereignty effects
- Currency crises and devaluations
"""
import json
import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.country import Country
    from engine.world import World

logger = logging.getLogger(__name__)


class CurrencyType(str, Enum):
    """Types of currency arrangements"""
    RESERVE = "reserve"       # Major reserve currency (USD, EUR, etc.)
    MAJOR = "major"           # Important but not dominant
    REGIONAL = "regional"     # Regional importance
    PEGGED = "pegged"         # Fixed exchange rate to another currency
    CRYPTO = "crypto"         # Cryptocurrency
    CBDC = "cbdc"             # Central Bank Digital Currency
    COMMODITY = "commodity"   # Gold standard or commodity-backed
    DOLLARIZED = "dollarized" # Uses another country's currency


class CurrencyDependency(str, Enum):
    """Level of monetary dependency"""
    SOVEREIGN = "sovereign"           # Full monetary sovereignty
    SOFT_PEG = "soft_peg"             # Managed float, informal peg
    HARD_PEG = "hard_peg"             # Currency board or fixed peg
    CURRENCY_UNION = "currency_union" # Shared currency (Eurozone)
    DOLLARIZED = "dollarized"         # Uses foreign currency
    CRYPTO_LEGAL = "crypto_legal"     # Crypto as legal tender


class Currency(BaseModel):
    """A currency definition"""
    id: str
    name: str
    name_fr: str
    symbol: str
    type: CurrencyType
    controller: Optional[str] = None  # Country or bloc that controls it

    # Reserve status
    is_reserve_currency: bool = False
    global_share: int = 0  # Percentage of global reserves

    # Stability
    stability: int = 50  # 0-100
    inflation_base: int = 2  # Base inflation rate
    volatility: int = 10  # Price volatility

    # Pegged currencies
    pegged_to: Optional[str] = None
    peg_rate: Optional[float] = None

    # Zone members (for shared currencies)
    members: List[str] = Field(default_factory=list)

    # Crypto specific
    adoption_countries: List[str] = Field(default_factory=list)

    description_fr: str = ""


class MonetaryStatus(BaseModel):
    """A country's monetary situation"""
    country_id: str
    currency_id: str
    dependency: CurrencyDependency = CurrencyDependency.SOVEREIGN

    # Economic effects
    inflation_rate: float = 2.0
    exchange_rate_vs_usd: float = 1.0

    # Reserves
    foreign_reserves: int = 50  # 0-100 (months of imports)
    gold_reserves: int = 0  # Tons

    # Crypto adoption
    crypto_adoption: int = 0  # 0-100
    has_cbdc: bool = False

    # Sovereignty score
    monetary_sovereignty: int = 100  # 0-100


class CurrencyCrisis(BaseModel):
    """A currency crisis event"""
    id: str
    country_id: str
    currency_id: str
    year: int
    severity: int  # 1-10
    cause: str
    effects: Dict = Field(default_factory=dict)
    resolved: bool = False


class PetroCurrencyAgreement(BaseModel):
    """Agreement to trade oil in a specific currency"""
    id: str
    oil_exporter: str  # Country that exports oil
    currency_id: str   # Currency used for oil trade
    controller: str    # Country that controls the currency
    year_signed: int
    is_active: bool = True
    effects: Dict = Field(default_factory=dict)


class CurrencyManager:
    """Manages global currency system"""

    def __init__(self):
        self.currencies: Dict[str, Currency] = {}
        self.country_status: Dict[str, MonetaryStatus] = {}
        self.active_crises: List[CurrencyCrisis] = []
        self.petro_agreements: Dict[str, PetroCurrencyAgreement] = {}
        self._load_currencies()

    def _load_currencies(self):
        """Load currencies from JSON"""
        data_path = Path(__file__).parent.parent / "data" / "currencies.json"
        if not data_path.exists():
            logger.warning("currencies.json not found")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            currencies_data = json.load(f)

        for curr_data in currencies_data:
            currency = Currency(**curr_data)
            self.currencies[currency.id] = currency

        logger.info(f"Loaded {len(self.currencies)} currencies")

    def get_currency(self, currency_id: str) -> Optional[Currency]:
        """Get a currency by ID"""
        return self.currencies.get(currency_id)

    def get_country_currency(self, country_id: str) -> Optional[str]:
        """Get the currency a country uses"""
        status = self.country_status.get(country_id)
        if status:
            return status.currency_id

        # Check if country is in a currency zone
        for currency in self.currencies.values():
            if country_id in currency.members:
                return currency.id
            if country_id in currency.adoption_countries:
                return currency.id

        return None

    def initialize_country_status(
        self,
        country_id: str,
        currency_id: str,
        dependency: CurrencyDependency = CurrencyDependency.SOVEREIGN
    ) -> MonetaryStatus:
        """Initialize monetary status for a country"""
        currency = self.currencies.get(currency_id)

        # Calculate monetary sovereignty
        sovereignty = self._calculate_sovereignty(dependency, currency)

        status = MonetaryStatus(
            country_id=country_id,
            currency_id=currency_id,
            dependency=dependency,
            monetary_sovereignty=sovereignty,
            inflation_rate=currency.inflation_base if currency else 2.0,
        )

        self.country_status[country_id] = status
        return status

    def _calculate_sovereignty(
        self,
        dependency: CurrencyDependency,
        currency: Optional[Currency]
    ) -> int:
        """Calculate monetary sovereignty score"""
        base_sovereignty = {
            CurrencyDependency.SOVEREIGN: 100,
            CurrencyDependency.SOFT_PEG: 70,
            CurrencyDependency.HARD_PEG: 40,
            CurrencyDependency.CURRENCY_UNION: 30,
            CurrencyDependency.DOLLARIZED: 10,
            CurrencyDependency.CRYPTO_LEGAL: 50,
        }

        sovereignty = base_sovereignty.get(dependency, 50)

        # Bonus if you control the currency
        if currency and currency.is_reserve_currency:
            sovereignty = min(100, sovereignty + 20)

        return sovereignty

    def change_currency(
        self,
        country_id: str,
        new_currency_id: str,
        dependency: CurrencyDependency,
        world: Optional["World"] = None
    ) -> Tuple[bool, str, Dict]:
        """Change a country's currency arrangement

        Returns: (success, message, effects)
        """
        new_currency = self.currencies.get(new_currency_id)
        if not new_currency:
            return False, "Monnaie inexistante", {}

        old_status = self.country_status.get(country_id)
        old_currency_id = old_status.currency_id if old_status else None

        effects = {
            "economy": 0,
            "stability": 0,
            "relations": {},
            "sovereignty_change": 0,
        }

        # Calculate sovereignty change
        new_sovereignty = self._calculate_sovereignty(dependency, new_currency)
        old_sovereignty = old_status.monetary_sovereignty if old_status else 50
        effects["sovereignty_change"] = new_sovereignty - old_sovereignty

        # Effects based on transition type
        if dependency == CurrencyDependency.DOLLARIZED:
            # Dollarization: lose sovereignty, gain stability
            effects["stability"] = 10
            effects["economy"] = -5  # Short-term disruption

            # Relation with controller
            if new_currency.controller:
                effects["relations"][new_currency.controller] = 15

            # Negative relation with rivals of controller
            if new_currency.controller == "USA" and world:
                for rival in ["RUS", "CHN", "IRN"]:
                    effects["relations"][rival] = -10

        elif dependency == CurrencyDependency.CRYPTO_LEGAL:
            # Crypto adoption: innovative but risky
            effects["stability"] = -15
            effects["economy"] = 5  # Attract crypto investors

            # Negative relation with IMF/traditional powers
            effects["relations"]["USA"] = -5
            effects["relations"]["EU_BLOC"] = -5

        elif dependency == CurrencyDependency.SOVEREIGN:
            # Gaining sovereignty: short-term instability
            if old_status and old_status.dependency in [
                CurrencyDependency.DOLLARIZED,
                CurrencyDependency.HARD_PEG,
                CurrencyDependency.CURRENCY_UNION
            ]:
                effects["stability"] = -20
                effects["economy"] = -10

                # Damaged relations with former controller
                old_currency = self.currencies.get(old_currency_id)
                if old_currency and old_currency.controller:
                    effects["relations"][old_currency.controller] = -25

        # Create new status
        new_status = MonetaryStatus(
            country_id=country_id,
            currency_id=new_currency_id,
            dependency=dependency,
            monetary_sovereignty=new_sovereignty,
            inflation_rate=new_currency.inflation_base,
            foreign_reserves=old_status.foreign_reserves if old_status else 50,
            gold_reserves=old_status.gold_reserves if old_status else 0,
            crypto_adoption=old_status.crypto_adoption if old_status else 0,
        )

        self.country_status[country_id] = new_status

        msg = f"Passage a {new_currency.name_fr} ({dependency.value})"
        logger.info(f"{country_id} changed to {new_currency_id} ({dependency})")

        return True, msg, effects

    def adopt_crypto(
        self,
        country_id: str,
        level: int = 10,
        as_legal_tender: bool = False
    ) -> Tuple[bool, str, Dict]:
        """Adopt cryptocurrency

        level: 0-100 adoption level
        as_legal_tender: Make crypto legal tender (like El Salvador)
        """
        status = self.country_status.get(country_id)
        if not status:
            return False, "Pays non initialise", {}

        effects = {
            "economy": 0,
            "stability": 0,
            "tech": 0,
            "relations": {},
        }

        if as_legal_tender:
            # Full crypto adoption like El Salvador
            status.crypto_adoption = 100
            status.dependency = CurrencyDependency.CRYPTO_LEGAL
            status.monetary_sovereignty = 50  # Partial sovereignty

            effects["stability"] = -15
            effects["economy"] = 5
            effects["tech"] = 10
            effects["relations"]["USA"] = -10

            # Add to Bitcoin adoption
            btc = self.currencies.get("BTC")
            if btc and country_id not in btc.adoption_countries:
                btc.adoption_countries.append(country_id)

            msg = "Bitcoin adopte comme monnaie legale"
        else:
            # Gradual adoption
            status.crypto_adoption = min(100, status.crypto_adoption + level)
            effects["tech"] = level // 5

            if status.crypto_adoption > 50:
                effects["stability"] = -5

            msg = f"Adoption crypto: {status.crypto_adoption}%"

        return True, msg, effects

    def launch_cbdc(self, country_id: str) -> Tuple[bool, str, Dict]:
        """Launch a Central Bank Digital Currency"""
        status = self.country_status.get(country_id)
        if not status:
            return False, "Pays non initialise", {}

        if status.has_cbdc:
            return False, "CBDC deja lancee", {}

        effects = {
            "economy": 5,
            "tech": 10,
            "stability": 0,
            "surveillance": 20,  # Government control
        }

        status.has_cbdc = True

        # Create CBDC entry if major power
        if status.currency_id in ["USD", "EUR", "CNY", "JPY", "GBP"]:
            cbdc_id = f"CBDC_{status.currency_id}"
            if cbdc_id not in self.currencies:
                base_currency = self.currencies.get(status.currency_id)
                if base_currency:
                    cbdc = Currency(
                        id=cbdc_id,
                        name=f"Digital {base_currency.name}",
                        name_fr=f"{base_currency.name_fr} numerique",
                        symbol=f"e{base_currency.symbol}",
                        type=CurrencyType.CBDC,
                        controller=base_currency.controller,
                        stability=base_currency.stability,
                        inflation_base=base_currency.inflation_base,
                        description_fr=f"Version numerique de {base_currency.name_fr}"
                    )
                    self.currencies[cbdc_id] = cbdc

        return True, "CBDC lancee avec succes", effects

    def trigger_crisis(
        self,
        country_id: str,
        severity: int,
        cause: str,
        year: int
    ) -> CurrencyCrisis:
        """Trigger a currency crisis"""
        status = self.country_status.get(country_id)
        currency_id = status.currency_id if status else "unknown"

        crisis = CurrencyCrisis(
            id=str(uuid4())[:8],
            country_id=country_id,
            currency_id=currency_id,
            year=year,
            severity=severity,
            cause=cause,
            effects={
                "inflation_spike": severity * 5,
                "economy_loss": severity * 3,
                "stability_loss": severity * 4,
                "reserves_drain": severity * 10,
            }
        )

        self.active_crises.append(crisis)

        # Apply immediate effects
        if status:
            status.inflation_rate += severity * 5
            status.foreign_reserves = max(0, status.foreign_reserves - severity * 10)

        logger.warning(f"Currency crisis in {country_id}: {cause} (severity {severity})")

        return crisis

    def resolve_crisis(
        self,
        crisis_id: str,
        method: str
    ) -> Tuple[bool, str, Dict]:
        """Resolve a currency crisis

        Methods: imf_bailout, austerity, default, dollarization, devaluation
        """
        crisis = next((c for c in self.active_crises if c.id == crisis_id), None)
        if not crisis:
            return False, "Crise non trouvee", {}

        effects = {}

        if method == "imf_bailout":
            effects = {
                "debt": 20,
                "economy": -10,  # Austerity conditions
                "stability": 10,
                "sovereignty": -15,
                "relations": {"USA": 10, "EU_BLOC": 10},
            }
        elif method == "austerity":
            effects = {
                "economy": -15,
                "stability": -10,
                "debt": -10,
                "popular_support": -20,
            }
        elif method == "default":
            effects = {
                "debt": -50,
                "economy": -25,
                "stability": -20,
                "relations": {"USA": -30, "EU_BLOC": -30, "CHN": -20},
                "credit_rating": -30,
            }
        elif method == "dollarization":
            # Switch to USD
            success, msg, change_effects = self.change_currency(
                crisis.country_id,
                "USD",
                CurrencyDependency.DOLLARIZED
            )
            effects = change_effects
            effects["stability"] = 15
        elif method == "devaluation":
            effects = {
                "economy": 5,  # Export boost
                "inflation": 20,
                "debt_real_value": 10,  # Debt becomes cheaper
                "imports_cost": 30,
            }

        crisis.resolved = True
        self.active_crises = [c for c in self.active_crises if c.id != crisis_id]

        return True, f"Crise resolue par {method}", effects

    def calculate_trade_currency_effect(
        self,
        country_a: str,
        country_b: str
    ) -> int:
        """Calculate trade bonus/malus based on currency compatibility"""
        status_a = self.country_status.get(country_a)
        status_b = self.country_status.get(country_b)

        if not status_a or not status_b:
            return 0

        # Same currency = bonus
        if status_a.currency_id == status_b.currency_id:
            return 15

        # Both use reserve currencies = small bonus
        curr_a = self.currencies.get(status_a.currency_id)
        curr_b = self.currencies.get(status_b.currency_id)

        if curr_a and curr_b:
            if curr_a.is_reserve_currency and curr_b.is_reserve_currency:
                return 5

            # One is dollarized to the other's currency
            if status_a.dependency == CurrencyDependency.DOLLARIZED:
                if status_a.currency_id == status_b.currency_id:
                    return 10
            if status_b.dependency == CurrencyDependency.DOLLARIZED:
                if status_b.currency_id == status_a.currency_id:
                    return 10

        return 0

    def get_currency_influence(self, currency_id: str) -> Dict:
        """Get the global influence of a currency"""
        currency = self.currencies.get(currency_id)
        if not currency:
            return {}

        # Count countries using this currency
        users = []
        for country_id, status in self.country_status.items():
            if status.currency_id == currency_id:
                users.append(country_id)

        # Add zone members
        users.extend(currency.members)

        # Add adoption countries (crypto)
        users.extend(currency.adoption_countries)

        return {
            "currency_id": currency_id,
            "name_fr": currency.name_fr,
            "global_share": currency.global_share,
            "is_reserve": currency.is_reserve_currency,
            "controller": currency.controller,
            "user_count": len(set(users)),
            "users": list(set(users)),
            "stability": currency.stability,
        }

    def impose_currency(
        self,
        imposer_id: str,
        target_id: str,
        currency_id: str,
        method: str,
        world: Optional["World"] = None
    ) -> Tuple[bool, str, Dict]:
        """Force a country to adopt a currency

        Methods:
        - colonial: Historical colonial imposition (CFA franc)
        - economic_pressure: Trade sanctions until adoption
        - debt_trap: Lend money then demand currency change
        - regime_change: Install friendly government that accepts
        - treaty: Force through unequal treaty
        """
        currency = self.currencies.get(currency_id)
        if not currency:
            return False, "Monnaie inexistante", {}

        target_status = self.country_status.get(target_id)
        imposer_status = self.country_status.get(imposer_id)

        effects = {
            "economy_target": 0,
            "stability_target": 0,
            "sovereignty_target": 0,
            "economy_imposer": 0,
            "soft_power_imposer": 0,
            "relations": {},
            "world_opinion": 0,
        }

        # Check if imposer controls the currency
        if currency.controller != imposer_id:
            return False, "Vous ne controlez pas cette monnaie", {}

        # Calculate resistance based on target strength
        target_strength = 50  # Default
        if world:
            target_country = world.get_country(target_id)
            if target_country:
                target_strength = (
                    target_country.military +
                    target_country.economy +
                    target_country.stability
                ) // 3

        success_chance = 80 - target_strength // 2

        # Method-specific effects
        if method == "colonial":
            effects["sovereignty_target"] = -50
            effects["economy_target"] = -10
            effects["stability_target"] = -20
            effects["soft_power_imposer"] = -30
            effects["world_opinion"] = -40
            effects["relations"][target_id] = -50
            msg_method = "imposition coloniale"

        elif method == "economic_pressure":
            effects["economy_target"] = -25
            effects["stability_target"] = -15
            effects["sovereignty_target"] = -30
            effects["economy_imposer"] = -5  # Sanctions cost both sides
            effects["soft_power_imposer"] = -10
            effects["world_opinion"] = -15
            effects["relations"][target_id] = -30
            msg_method = "pression economique"

        elif method == "debt_trap":
            effects["economy_target"] = -20
            effects["sovereignty_target"] = -40
            effects["economy_imposer"] = 10  # Profit from debt
            effects["soft_power_imposer"] = -20
            effects["world_opinion"] = -25
            effects["relations"][target_id] = -40
            msg_method = "piege de la dette"

        elif method == "regime_change":
            effects["stability_target"] = -40
            effects["sovereignty_target"] = -60
            effects["economy_target"] = -30
            effects["soft_power_imposer"] = -50
            effects["world_opinion"] = -60
            effects["relations"][target_id] = -70
            # Damage relations with allies of target
            for ally in ["RUS", "CHN", "IRN"]:
                if ally != imposer_id:
                    effects["relations"][ally] = -30
            msg_method = "changement de regime"

        elif method == "treaty":
            effects["sovereignty_target"] = -25
            effects["economy_target"] = 5  # Some benefits promised
            effects["soft_power_imposer"] = -5
            effects["world_opinion"] = -10
            effects["relations"][target_id] = -15
            msg_method = "traite inegal"

        else:
            return False, f"Methode inconnue: {method}", {}

        # Apply the currency change
        success, change_msg, change_effects = self.change_currency(
            target_id,
            currency_id,
            CurrencyDependency.DOLLARIZED if method != "treaty" else CurrencyDependency.HARD_PEG,
            world
        )

        if not success:
            return False, f"Echec: {change_msg}", {}

        # Record the imposition
        if target_status:
            target_status.monetary_sovereignty = max(
                0,
                target_status.monetary_sovereignty + effects["sovereignty_target"]
            )

        msg = f"{currency.name_fr} impose a {target_id} par {msg_method}"
        logger.info(f"{imposer_id} imposed {currency_id} on {target_id} via {method}")

        return True, msg, effects

    def resist_currency_imposition(
        self,
        country_id: str,
        imposer_id: str,
        method: str,
        world: Optional["World"] = None
    ) -> Tuple[bool, str, Dict]:
        """Resist currency imposition attempt

        Methods:
        - nationalise: Nationalize foreign assets and create own currency
        - join_rival_bloc: Join opposing economic bloc (BRICS, etc.)
        - default: Default on debt denominated in imposed currency
        - crypto_escape: Adopt crypto to bypass imposed currency
        - popular_uprising: Popular resistance movement
        """
        status = self.country_status.get(country_id)
        if not status:
            return False, "Pays non initialise", {}

        effects = {
            "economy": 0,
            "stability": 0,
            "sovereignty": 0,
            "relations": {},
        }

        if method == "nationalise":
            effects["economy"] = -20
            effects["stability"] = -15
            effects["sovereignty"] = 30
            effects["relations"][imposer_id] = -50
            # Gain support from rival powers
            for rival in ["RUS", "CHN", "IRN"]:
                if rival != imposer_id and rival != country_id:
                    effects["relations"][rival] = 20
            msg = "Nationalisation des actifs etrangers"

        elif method == "join_rival_bloc":
            effects["economy"] = -10
            effects["stability"] = 5
            effects["sovereignty"] = 20
            effects["relations"][imposer_id] = -40
            effects["relations"]["CHN"] = 25
            effects["relations"]["RUS"] = 20
            msg = "Adhesion a un bloc rival"

        elif method == "default":
            effects["economy"] = -30
            effects["stability"] = -20
            effects["sovereignty"] = 25
            effects["relations"][imposer_id] = -60
            effects["relations"]["EU_BLOC"] = -30
            msg = "Defaut sur la dette"

        elif method == "crypto_escape":
            success, crypto_msg, crypto_effects = self.adopt_crypto(
                country_id,
                level=80,
                as_legal_tender=True
            )
            effects.update(crypto_effects)
            effects["sovereignty"] = 15
            effects["relations"][imposer_id] = -20
            msg = "Adoption du Bitcoin comme echappatoire"

        elif method == "popular_uprising":
            effects["stability"] = -30
            effects["sovereignty"] = 20
            effects["economy"] = -15
            effects["relations"][imposer_id] = -30
            msg = "Soulevement populaire contre la domination monetaire"

        else:
            return False, f"Methode inconnue: {method}", {}

        # Update sovereignty
        if status:
            status.monetary_sovereignty = min(
                100,
                status.monetary_sovereignty + effects["sovereignty"]
            )

        logger.info(f"{country_id} resisted {imposer_id}'s currency imposition via {method}")

        return True, msg, effects

    # ==================== PETRO-CURRENCY SYSTEM ====================

    def sign_petro_agreement(
        self,
        oil_exporter: str,
        currency_id: str,
        year: int,
        world: Optional["World"] = None
    ) -> Tuple[bool, str, Dict]:
        """Sign a petro-currency agreement (like petro-dollar)

        This means the oil exporter will sell oil in the specified currency,
        strengthening that currency's global position.
        """
        currency = self.currencies.get(currency_id)
        if not currency:
            return False, "Monnaie inexistante", {}

        if not currency.controller:
            return False, "Cette monnaie n'a pas de controleur", {}

        # Check if exporter has significant oil
        has_oil = False
        if world:
            country = world.get_country(oil_exporter)
            if country and country.resources >= 50:
                has_oil = True
        else:
            # Assume major oil exporters
            has_oil = oil_exporter in [
                "SAU", "RUS", "USA", "IRN", "IRQ", "ARE", "KWT",
                "VEN", "NGA", "LBY", "DZA", "AGO", "KAZ"
            ]

        if not has_oil:
            return False, "Ce pays n'est pas un exportateur de petrole majeur", {}

        agreement_id = f"petro_{oil_exporter}_{currency_id}"

        # Check if already exists
        if agreement_id in self.petro_agreements:
            return False, "Accord deja existant", {}

        effects = {
            "currency_strength": 5,
            "exporter_economy": 5,
            "controller_soft_power": 10,
            "relations": {currency.controller: 20},
        }

        # Create agreement
        agreement = PetroCurrencyAgreement(
            id=agreement_id,
            oil_exporter=oil_exporter,
            currency_id=currency_id,
            controller=currency.controller,
            year_signed=year,
            effects=effects,
        )

        self.petro_agreements[agreement_id] = agreement

        # Boost currency global share
        currency.global_share = min(100, currency.global_share + 2)

        msg = f"Accord petro-{currency.name_fr} signe avec {oil_exporter}"
        logger.info(f"Petro-currency agreement: {oil_exporter} -> {currency_id}")

        return True, msg, effects

    def break_petro_agreement(
        self,
        oil_exporter: str,
        currency_id: str,
        new_currency_id: Optional[str] = None,
        world: Optional["World"] = None
    ) -> Tuple[bool, str, Dict]:
        """Break a petro-currency agreement

        This is a major geopolitical move (like Iraq/Libya trying to leave petro-dollar)
        """
        agreement_id = f"petro_{oil_exporter}_{currency_id}"
        agreement = self.petro_agreements.get(agreement_id)

        if not agreement:
            return False, "Accord inexistant", {}

        old_currency = self.currencies.get(currency_id)
        controller = agreement.controller

        effects = {
            "old_currency_strength": -5,
            "exporter_economy": -10,  # Short-term pain
            "exporter_stability": -15,
            "controller_soft_power": -15,
            "relations": {controller: -50},
            "world_tension": 10,
        }

        # If switching to rival currency, bigger effects
        if new_currency_id:
            new_currency = self.currencies.get(new_currency_id)
            if new_currency and new_currency.controller:
                # Bonus with new controller
                effects["relations"][new_currency.controller] = 30
                # Sign new agreement
                self.sign_petro_agreement(
                    oil_exporter,
                    new_currency_id,
                    agreement.year_signed + 1,  # Placeholder year
                    world
                )

                # Extra tension if switching from USD to CNY or EUR
                if currency_id == "USD" and new_currency_id in ["CNY", "EUR", "RUB"]:
                    effects["world_tension"] = 25
                    effects["relations"][controller] = -70
                    logger.warning(
                        f"MAJOR EVENT: {oil_exporter} leaving petro-dollar for {new_currency_id}"
                    )

        # Remove old agreement
        agreement.is_active = False
        del self.petro_agreements[agreement_id]

        # Weaken old currency
        if old_currency:
            old_currency.global_share = max(0, old_currency.global_share - 2)

        msg = f"{oil_exporter} rompt l'accord petro-{old_currency.name_fr if old_currency else currency_id}"
        logger.info(f"Petro agreement broken: {oil_exporter} leaves {currency_id}")

        return True, msg, effects

    def get_petro_currency_power(self, currency_id: str) -> Dict:
        """Get the petro-currency power of a currency"""
        active_agreements = [
            a for a in self.petro_agreements.values()
            if a.currency_id == currency_id and a.is_active
        ]

        return {
            "currency_id": currency_id,
            "active_agreements": len(active_agreements),
            "oil_exporters": [a.oil_exporter for a in active_agreements],
            "petro_power": len(active_agreements) * 10,  # 0-100 scale
        }

    def calculate_petro_dollar_strength(self) -> int:
        """Calculate current petro-dollar system strength"""
        usd_agreements = len([
            a for a in self.petro_agreements.values()
            if a.currency_id == "USD" and a.is_active
        ])

        total_agreements = len([
            a for a in self.petro_agreements.values()
            if a.is_active
        ])

        if total_agreements == 0:
            return 100  # Default dominance

        return int((usd_agreements / total_agreements) * 100)

    def initialize_petro_dollar_system(self, year: int = 1974):
        """Initialize historical petro-dollar agreements"""
        # Historical petro-dollar countries (post-1974 Nixon-Saudi deal)
        petro_dollar_countries = [
            "SAU",  # Saudi Arabia - cornerstone
            "ARE",  # UAE
            "KWT",  # Kuwait
            "QAT",  # Qatar
            "BHR",  # Bahrain
            "OMN",  # Oman
            "IRQ",  # Iraq (until 2000)
            "NGA",  # Nigeria
            "AGO",  # Angola
            "DZA",  # Algeria
        ]

        for country in petro_dollar_countries:
            self.sign_petro_agreement(country, "USD", year)

        logger.info(f"Petro-dollar system initialized with {len(petro_dollar_countries)} countries")

    def annual_update(self, year: int) -> List[Dict]:
        """Annual monetary system update"""
        events = []

        for country_id, status in self.country_status.items():
            currency = self.currencies.get(status.currency_id)
            if not currency:
                continue

            # Update inflation based on stability and dependency
            base_inflation = currency.inflation_base

            if status.dependency == CurrencyDependency.SOVEREIGN:
                # More variance for sovereign currencies
                status.inflation_rate = base_inflation + (100 - currency.stability) / 20
            elif status.dependency == CurrencyDependency.DOLLARIZED:
                # Inherit controller's inflation
                status.inflation_rate = base_inflation
            elif status.dependency == CurrencyDependency.CRYPTO_LEGAL:
                # High volatility
                status.inflation_rate = base_inflation + currency.volatility / 10

            # Check for potential crisis
            if status.foreign_reserves < 20 and status.inflation_rate > 15:
                crisis = self.trigger_crisis(
                    country_id,
                    severity=5,
                    cause="Reserves epuisees et hyperinflation",
                    year=year
                )
                events.append({
                    "type": "currency_crisis",
                    "country": country_id,
                    "crisis_id": crisis.id,
                })

        return events


# Global instance
currency_manager = CurrencyManager()
