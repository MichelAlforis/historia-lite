"""Tests for economy system"""
import pytest
from unittest.mock import MagicMock

from engine.economy import (
    EconomyManager,
    TradeType,
    DebtHolder,
    TradeAgreement,
    NationalDebt,
    ForeignReserves,
)


class MockCountry:
    """Mock country for testing"""
    def __init__(self, country_id: str, **kwargs):
        self.id = country_id
        self.name = kwargs.get("name", country_id)
        self.name_fr = kwargs.get("name_fr", country_id)
        self.economy = kwargs.get("economy", 50)
        self.stability = kwargs.get("stability", 50)

    def modify_relation(self, other_id: str, delta: int):
        pass


class MockWorld:
    """Mock world for testing"""
    def __init__(self):
        self.year = 2025
        self.countries = {}

    def get_country(self, country_id: str):
        return self.countries.get(country_id)

    def get_all_countries(self):
        return list(self.countries.values())

    def add_country(self, country):
        self.countries[country.id] = country


class TestEconomyManager:
    """Test EconomyManager class"""

    def setup_method(self):
        """Setup for each test"""
        self.manager = EconomyManager()
        self.world = MockWorld()

    def test_init(self):
        """Test manager initialization"""
        assert self.manager.trade_agreements == {}
        assert self.manager.national_debts == {}
        assert self.manager.foreign_reserves == {}

    def test_reset(self):
        """Test reset clears state"""
        self.manager.trade_agreements["test"] = MagicMock()
        self.manager.reset()
        assert self.manager.trade_agreements == {}


class TestTradeAgreements:
    """Test trade agreement functionality"""

    def setup_method(self):
        self.manager = EconomyManager()
        self.world = MockWorld()
        self.world.add_country(MockCountry("USA"))
        self.world.add_country(MockCountry("CHN"))
        self.world.add_country(MockCountry("DEU"))

    def test_create_trade_agreement(self):
        """Test creating a trade agreement"""
        agreement = self.manager.create_trade_agreement(
            country_a="USA",
            country_b="CHN",
            trade_type=TradeType.STANDARD,
            volume=60,
            year=2025,
        )

        assert agreement.country_a == "USA"
        assert agreement.country_b == "CHN"
        assert agreement.volume == 60
        assert agreement.trade_type == TradeType.STANDARD
        assert agreement.is_active

    def test_get_trade_partners(self):
        """Test getting trade partners"""
        self.manager.create_trade_agreement("USA", "CHN", TradeType.STANDARD, 50, 2025)
        self.manager.create_trade_agreement("USA", "DEU", TradeType.FREE_TRADE, 70, 2025)

        partners = self.manager.get_trade_partners("USA")
        assert len(partners) == 2

        partner_ids = [p[0] for p in partners]
        assert "CHN" in partner_ids
        assert "DEU" in partner_ids

    def test_get_trade_volume(self):
        """Test calculating total trade volume"""
        self.manager.create_trade_agreement("USA", "CHN", TradeType.STANDARD, 50, 2025)
        self.manager.create_trade_agreement("USA", "DEU", TradeType.FREE_TRADE, 70, 2025)

        volume = self.manager.get_trade_volume("USA")
        assert volume == 120

    def test_get_trade_volume_excludes_embargo(self):
        """Test that embargo doesn't count in volume"""
        self.manager.create_trade_agreement("USA", "CHN", TradeType.STANDARD, 50, 2025)
        self.manager.create_trade_agreement("USA", "RUS", TradeType.EMBARGO, 0, 2025)

        volume = self.manager.get_trade_volume("USA")
        assert volume == 50

    def test_get_trade_balance(self):
        """Test calculating trade balance"""
        agreement = self.manager.create_trade_agreement("USA", "CHN", TradeType.STANDARD, 50, 2025)
        agreement.balance = -20  # USA has deficit with China

        balance = self.manager.get_trade_balance("USA")
        assert balance == -20

        # China should have surplus
        balance_chn = self.manager.get_trade_balance("CHN")
        assert balance_chn == 20


class TestNationalDebt:
    """Test national debt functionality"""

    def setup_method(self):
        self.manager = EconomyManager()

    def test_get_or_create_debt(self):
        """Test debt record creation"""
        debt = self.manager.get_or_create_debt("USA")

        assert debt.country_id == "USA"
        assert debt.debt_to_gdp == 50  # Default
        assert not debt.is_in_default

    def test_increase_debt(self):
        """Test increasing debt"""
        debt = self.manager.increase_debt("USA", 20, DebtHolder.FOREIGN)

        assert debt.debt_to_gdp == 70
        assert "foreign" in debt.debt_holders

    def test_increase_debt_updates_rating(self):
        """Test debt affects credit rating"""
        # Low debt = good rating
        debt = self.manager.get_or_create_debt("USA")
        debt.debt_to_gdp = 25  # Below 30 threshold for AAA
        self.manager._update_credit_rating(debt)
        assert debt.credit_rating == "AAA"

        # High debt = poor rating
        debt.debt_to_gdp = 160
        self.manager._update_credit_rating(debt)
        assert debt.credit_rating == "CCC"

    def test_pay_debt(self):
        """Test paying down debt"""
        self.manager.increase_debt("USA", 30, DebtHolder.FOREIGN)
        debt = self.manager.pay_debt("USA", 10)

        assert debt.debt_to_gdp == 70  # 50 + 30 - 10

    def test_debt_default(self):
        """Test debt default at high levels"""
        debt = self.manager.get_or_create_debt("GRC")
        debt.debt_to_gdp = 250
        self.manager._update_credit_rating(debt)

        assert debt.credit_rating == "D"
        assert debt.is_in_default


class TestForeignReserves:
    """Test foreign reserves functionality"""

    def setup_method(self):
        self.manager = EconomyManager()

    def test_get_or_create_reserves(self):
        """Test reserves record creation"""
        reserves = self.manager.get_or_create_reserves("CHN")

        assert reserves.country_id == "CHN"
        assert reserves.total_reserves == 50  # Default

    def test_add_reserves(self):
        """Test adding reserves"""
        self.manager.add_reserves("CHN", 20)
        reserves = self.manager.get_or_create_reserves("CHN")

        assert reserves.total_reserves == 70

    def test_add_reserves_max(self):
        """Test reserves capped at 100"""
        self.manager.add_reserves("CHN", 100)
        reserves = self.manager.get_or_create_reserves("CHN")

        assert reserves.total_reserves == 100

    def test_spend_reserves_success(self):
        """Test spending reserves when sufficient"""
        reserves = self.manager.get_or_create_reserves("CHN")
        reserves.total_reserves = 50

        result = self.manager.spend_reserves("CHN", 20)

        assert result is True
        assert reserves.total_reserves == 30

    def test_spend_reserves_insufficient(self):
        """Test spending reserves when insufficient"""
        reserves = self.manager.get_or_create_reserves("ARG")
        reserves.total_reserves = 10

        result = self.manager.spend_reserves("ARG", 20)

        assert result is False
        assert reserves.total_reserves == 10  # Unchanged


class TestEconomicSummary:
    """Test economic summary functionality"""

    def setup_method(self):
        self.manager = EconomyManager()

    def test_get_economic_summary(self):
        """Test comprehensive economic summary"""
        # Setup some data
        self.manager.create_trade_agreement("USA", "CHN", TradeType.STANDARD, 60, 2025)
        self.manager.increase_debt("USA", 20, DebtHolder.FOREIGN)
        self.manager.add_reserves("USA", 10)

        summary = self.manager.get_economic_summary("USA")

        assert "trade" in summary
        assert "debt" in summary
        assert "reserves" in summary
        assert "health" in summary

        assert summary["trade"]["partners"] == 1
        assert summary["debt"]["debt_to_gdp"] == 70

    def test_calculate_economic_health_excellent(self):
        """Test excellent economic health"""
        debt = NationalDebt(country_id="CHE", debt_to_gdp=30)
        reserves = ForeignReserves(country_id="CHE", total_reserves=70)

        health = self.manager._calculate_economic_health(debt, reserves, 40)
        assert health == "excellent"

    def test_calculate_economic_health_critical(self):
        """Test critical economic health"""
        debt = NationalDebt(country_id="VEN", debt_to_gdp=200, is_in_default=True)
        reserves = ForeignReserves(country_id="VEN", total_reserves=5)

        health = self.manager._calculate_economic_health(debt, reserves, -50)
        assert health == "critical"


class TestTradeAgreementModel:
    """Test TradeAgreement model"""

    def test_get_partner_country_a(self):
        """Test getting partner when you are country_a"""
        agreement = TradeAgreement(
            id="test",
            country_a="USA",
            country_b="CHN",
        )

        partner = agreement.get_partner("USA")
        assert partner == "CHN"

    def test_get_partner_country_b(self):
        """Test getting partner when you are country_b"""
        agreement = TradeAgreement(
            id="test",
            country_a="USA",
            country_b="CHN",
        )

        partner = agreement.get_partner("CHN")
        assert partner == "USA"

    def test_get_partner_not_in_agreement(self):
        """Test getting partner when not in agreement"""
        agreement = TradeAgreement(
            id="test",
            country_a="USA",
            country_b="CHN",
        )

        partner = agreement.get_partner("DEU")
        assert partner is None
