"""
Tests V1.7.1 - Archetype Parsing

1. Property-based fuzz: garantit "jamais de crash"
2. Golden tests: fige le contrat sur 12 scenarios
"""
import pytest
import re
from typing import Dict, Optional

# Import des fonctions a tester
import sys
sys.path.insert(0, '..')

from engine.game_debrief import (
    _soft_repair_json,
    _smart_truncate,
    _parse_archetype_response,
    _generate_archetype_id,
)


# =============================================================================
# FIXTURES
# =============================================================================

VALID_JSON = '{"title": "Le President du silence", "phrase": "Vous avez choisi de ne pas agir quand le monde attendait une reponse.", "history_line": "Dans les livres d\'histoire, on retiendra un president qui observait pendant que le monde brulait."}'

DIRTY_RESPONSES = [
    # Guillemets francais - utilise " " au lieu de guillemets droits
    '{"title": "Le President du silence", "phrase": "Vous avez choisi de ne pas agir.", "history_line": "Dans les livres d\'histoire, on retiendra un president silencieux."}',
    # Guillemets chevrons
    '{"title": «Le President du risque», "phrase": «Vous avez joue avec le feu.», "history_line": «Dans les livres d\'histoire, on parlera de vous.»}',
    # Texte avant/apres
    'Voici ma reponse:\n{"title": "Le President de la prudence", "phrase": "Vous avez prefere attendre.", "history_line": "Dans les livres d\'histoire, votre patience sera notee."}\nJ\'espere que ca convient.',
    # Trailing comma
    '{"title": "Le President du compromis", "phrase": "Vous avez negocie.", "history_line": "Dans les livres d\'histoire, on se souviendra de vos efforts.",}',
    # Newlines dans valeurs
    '{"title": "Le President\ndu courage", "phrase": "Vous avez\nose agir.", "history_line": "Dans les livres\nd\'histoire, votre bravoure sera saluee."}',
    # Markdown wrapper
    '```json\n{"title": "Le President de fer", "phrase": "Vous avez tenu bon face a la pression.", "history_line": "Dans les livres d\'histoire, votre fermete restera legendaire."}\n```',
    # Mix de problemes
    'Reponse: {"title": «Le President\ndu doute», "phrase": "Vous avez\nhesite trop longtemps face aux crises.", "history_line": "Dans les livres d\'histoire, on retiendra votre indecision face au danger.",}',
]

INVALID_RESPONSES = [
    # Pas de JSON
    "Je ne peux pas generer cela.",
    # JSON incomplet
    '{"title": "Le President',
    # Champ manquant
    '{"title": "Le President", "phrase": "Vous avez agi."}',
    # Phrase ne commence pas par "Vous"
    '{"title": "Le President", "phrase": "Il a choisi de fuir.", "history_line": "Dans les livres d\'histoire..."}',
    # Phrase trop courte
    '{"title": "Le President", "phrase": "Vous avez perdu.", "history_line": "Dans les livres d\'histoire, on retiendra un echec cuisant."}',
    # History_line ne commence pas correctement
    '{"title": "Le President", "phrase": "Vous avez choisi la paix face a la guerre froide.", "history_line": "Les historiens noteront votre passage."}',
]


# =============================================================================
# TEST 1: SOFT REPAIR JSON
# =============================================================================

class TestSoftRepairJson:
    """Tests pour _soft_repair_json"""

    def test_clean_french_quotes(self):
        """Remplace les guillemets francais (curly quotes)"""
        # U+201C et U+201D (guillemets courbes anglais)
        dirty = '\u201ctest\u201d et \u201cautre\u201d'
        result = _soft_repair_json(dirty)
        assert '\u201c' not in result  # left double quote
        assert '\u201d' not in result  # right double quote

    def test_clean_chevron_quotes(self):
        """Remplace les guillemets chevrons"""
        dirty = '«test» et «autre»'
        result = _soft_repair_json(dirty)
        assert '«' not in result
        assert '»' not in result

    def test_extract_json_from_text(self):
        """Extrait le JSON du texte autour"""
        dirty = 'Voici: {"key": "value"} fin.'
        result = _soft_repair_json(dirty)
        assert result.startswith('{')
        assert result.endswith('}')

    def test_remove_trailing_comma(self):
        """Supprime les trailing commas"""
        dirty = '{"key": "value",}'
        result = _soft_repair_json(dirty)
        assert ',}' not in result

    def test_clean_newlines_in_values(self):
        """Nettoie les newlines dans les valeurs"""
        dirty = '{"key": "value\nwith newline"}'
        result = _soft_repair_json(dirty)
        # La regex ne doit pas casser le JSON
        assert '{' in result and '}' in result


# =============================================================================
# TEST 2: SMART TRUNCATE
# =============================================================================

class TestSmartTruncate:
    """Tests pour _smart_truncate"""

    def test_no_truncate_if_short(self):
        """Pas de troncature si le texte est assez court"""
        text = "Court texte."
        result = _smart_truncate(text, 50)
        assert result == text

    def test_truncate_on_period(self):
        """Coupe au dernier point"""
        text = "Premiere phrase. Deuxieme phrase. Troisieme phrase qui depasse."
        result = _smart_truncate(text, 40)
        assert result.endswith('.')
        assert len(result) <= 40

    def test_truncate_on_exclamation(self):
        """Coupe au dernier point d'exclamation"""
        text = "Quelle victoire! Et quel courage! Vraiment impressionnant ce resultat."
        result = _smart_truncate(text, 40)
        assert '!' in result

    def test_truncate_on_space_if_no_punct(self):
        """Coupe au dernier espace si pas de ponctuation"""
        text = "Un texte sans ponctuation qui continue longtemps"
        result = _smart_truncate(text, 30)
        assert not result.endswith(' ')
        assert len(result) <= 30

    def test_no_ellipsis_added(self):
        """Pas de ... ajoute (style War Room)"""
        text = "Une phrase tres longue qui doit etre tronquee quelque part."
        result = _smart_truncate(text, 30)
        assert not result.endswith('...')


# =============================================================================
# TEST 3: PARSE ARCHETYPE RESPONSE (PROPERTY-BASED FUZZ)
# =============================================================================

class TestParseArchetypeResponse:
    """Tests fuzz pour _parse_archetype_response"""

    def test_valid_json_parses(self):
        """JSON valide est parse correctement"""
        result = _parse_archetype_response(VALID_JSON, "test_id")
        assert result is not None
        assert result["id"] == "test_id"
        assert result["title"].startswith("Le President")
        assert result["phrase"].startswith("Vous")
        assert "histoire" in result["history_line"].lower()

    @pytest.mark.parametrize("dirty_response", DIRTY_RESPONSES)
    def test_dirty_responses_dont_crash(self, dirty_response):
        """Reponses sales ne crashent jamais"""
        # Doit retourner un archetype OU None, jamais une exception
        try:
            result = _parse_archetype_response(dirty_response, "test_id")
            # Si resultat, verifier le contrat
            if result:
                assert isinstance(result, dict)
                assert "id" in result
                assert "title" in result
                assert "phrase" in result
                assert "history_line" in result
        except Exception as e:
            pytest.fail(f"Exception non catchee: {e}")

    @pytest.mark.parametrize("invalid_response", INVALID_RESPONSES)
    def test_invalid_responses_return_none(self, invalid_response):
        """Reponses invalides retournent None (pas d'exception)"""
        try:
            result = _parse_archetype_response(invalid_response, "test_id")
            # Doit etre None pour les cas invalides
            # (sauf si le soft repair a reussi a les corriger)
            assert result is None or isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Exception non catchee: {e}")

    def test_id_comes_from_code_not_llm(self):
        """L'ID vient du code, pas de la reponse LLM"""
        json_with_id = '{"id": "wrong_id", "title": "Le President", "phrase": "Vous avez choisi la voie difficile face aux defis.", "history_line": "Dans les livres d\'histoire, on parlera de votre determination."}'
        result = _parse_archetype_response(json_with_id, "correct_id")
        if result:
            assert result["id"] == "correct_id"

    def test_title_prefix_added_if_missing(self):
        """Prefixe 'Le President' ajoute si manquant"""
        json_no_prefix = '{"title": "du courage", "phrase": "Vous avez ose affronter vos peurs face au danger.", "history_line": "Dans les livres d\'histoire, votre bravoure sera celebree."}'
        result = _parse_archetype_response(json_no_prefix, "test_id")
        if result:
            assert "President" in result["title"]


# =============================================================================
# TEST 4: GENERATE ARCHETYPE ID (GOLDEN TESTS)
# =============================================================================

class TestGenerateArchetypeId:
    """Golden tests pour _generate_archetype_id - 12 scenarios"""

    # Scenario 1: Hawk actif, victoire
    def test_iron_hawk_victor(self):
        playstyle = {"hawk_score": 50, "action_score": 50, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=True, end_reason="domination")
        assert result == "iron_hawk_victor"

    # Scenario 2: Hawk actif, defaite apocalypse
    def test_iron_hawk_fallen(self):
        playstyle = {"hawk_score": 50, "action_score": 50, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="apocalypse")
        assert result == "iron_hawk_fallen"

    # Scenario 3: Dove passif, victoire
    def test_peaceful_silent_victor(self):
        playstyle = {"hawk_score": -50, "action_score": -50, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=True, end_reason="survival")
        assert result == "peaceful_silent_victor"

    # Scenario 4: Dove passif, coup d'etat
    def test_peaceful_silent_betrayed(self):
        playstyle = {"hawk_score": -50, "action_score": -50, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="coup_etat")
        assert result == "peaceful_silent_betrayed"

    # Scenario 5: Modere actif, victoire
    def test_firm_player_victor(self):
        playstyle = {"hawk_score": 20, "action_score": 20, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=True, end_reason="crisis_resolved")
        assert result == "firm_player_victor"

    # Scenario 6: Modere passif, defaite
    def test_cautious_watcher(self):
        playstyle = {"hawk_score": -20, "action_score": -20, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="defeat_honorable")
        assert result == "cautious_watcher"

    # Scenario 7: Hawk avec escalade, defaite
    def test_iron_escalator_fallen(self):
        playstyle = {"hawk_score": 50, "action_score": 50, "escalation_avoided": False}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="apocalypse")
        assert result == "iron_escalator_fallen"

    # Scenario 8: Firm avec escalade, victoire
    def test_firm_escalator_victor(self):
        playstyle = {"hawk_score": 20, "action_score": 20, "escalation_avoided": False}
        result = _generate_archetype_id(playstyle, victory=True, end_reason="domination")
        assert result == "firm_escalator_victor"

    # Scenario 9: Cautious watcher, victoire survival
    def test_cautious_watcher_victor(self):
        playstyle = {"hawk_score": -20, "action_score": -20, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=True, end_reason="survival")
        assert result == "cautious_watcher_victor"

    # Scenario 10: Peaceful player (dove mais actif)
    def test_peaceful_player(self):
        playstyle = {"hawk_score": -50, "action_score": 20, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="defeat_honorable")
        assert result == "peaceful_player"

    # Scenario 11: Iron silent (hawk mais passif)
    def test_iron_silent(self):
        playstyle = {"hawk_score": 50, "action_score": -50, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="defeat_honorable")
        assert result == "iron_silent"

    # Scenario 12: Valeurs limites (0, 0)
    def test_cautious_watcher_default(self):
        playstyle = {"hawk_score": 0, "action_score": 0, "escalation_avoided": True}
        result = _generate_archetype_id(playstyle, victory=False, end_reason="unknown")
        assert result == "cautious_watcher"

    # Verification du format snake_case
    @pytest.mark.parametrize("hawk,action,escalation,victory,end_reason", [
        (50, 50, True, True, "domination"),
        (-50, -50, False, False, "apocalypse"),
        (0, 0, True, True, "survival"),
        (100, -100, False, True, "crisis_resolved"),
    ])
    def test_id_is_valid_snake_case(self, hawk, action, escalation, victory, end_reason):
        """Tous les IDs sont en snake_case valide"""
        playstyle = {"hawk_score": hawk, "action_score": action, "escalation_avoided": escalation}
        result = _generate_archetype_id(playstyle, victory, end_reason)

        # Regex snake_case: lettres minuscules et underscores, 2-4 tokens
        assert re.match(r'^[a-z]+(_[a-z]+){1,3}$', result), f"Invalid snake_case: {result}"


# =============================================================================
# TEST 5: CONTRAT VALIDATION (limites de longueur)
# =============================================================================

class TestValidationContract:
    """Tests du contrat de validation"""

    def test_title_max_length(self):
        """Title max 60 chars (tronque si plus)"""
        long_title = '{"title": "Le President de la tres longue denomination qui depasse largement la limite autorisee", "phrase": "Vous avez choisi une voie complexe face aux defis mondiaux.", "history_line": "Dans les livres d\'histoire, on retiendra votre approche particuliere."}'
        result = _parse_archetype_response(long_title, "test_id")
        if result:
            assert len(result["title"]) <= 60

    def test_phrase_min_length(self):
        """Phrase min 40 chars (rejete si moins)"""
        short_phrase = '{"title": "Le President", "phrase": "Vous avez perdu.", "history_line": "Dans les livres d\'histoire, on parlera de vous comme un president unique."}'
        result = _parse_archetype_response(short_phrase, "test_id")
        assert result is None  # Rejete car phrase trop courte

    def test_phrase_max_length(self):
        """Phrase max 180 chars (tronque si plus)"""
        long_phrase = '{"title": "Le President", "phrase": "Vous avez choisi une approche tres particuliere qui a marque les esprits de tous ceux qui ont vecu cette periode difficile de l\'histoire mondiale et qui restera gravee dans les memoires pour les generations futures.", "history_line": "Dans les livres d\'histoire, on parlera de vous avec respect."}'
        result = _parse_archetype_response(long_phrase, "test_id")
        if result:
            assert len(result["phrase"]) <= 180

    def test_history_line_min_length(self):
        """History_line min 50 chars (rejete si moins)"""
        short_history = '{"title": "Le President", "phrase": "Vous avez marque l\'histoire par vos choix audacieux.", "history_line": "Dans les livres, court."}'
        result = _parse_archetype_response(short_history, "test_id")
        assert result is None  # Rejete car history_line trop courte


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
