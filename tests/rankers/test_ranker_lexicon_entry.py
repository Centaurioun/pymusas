from dataclasses import FrozenInstanceError
from typing import List, Optional, Tuple

import pytest

from pymusas.lexicon_collection import LexiconType
from pymusas.rankers.lexicon_entry import ContextualRuleBasedRanker, LexicalMatch, LexiconEntryRanker, RankingMetaData


RANKING_META_DATA = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 2, 1,
                                    False, LexicalMatch.TOKEN, 1, 3,
                                    'snow_noun boot_noun', ('Z5', 'Z4'))


def test_lexical_match() -> None:
    expected_name_values = [('TOKEN', 1), ('LEMMA', 2),
                            ('TOKEN_LOWER', 3), ('LEMMA_LOWER', 4)]
    for name, value in expected_name_values:
        assert value == getattr(LexicalMatch, name)
    
    assert 2 < LexicalMatch.LEMMA_LOWER
    assert 2 > LexicalMatch.TOKEN

    eval(LexicalMatch.TOKEN.__repr__())
    assert LexicalMatch.TOKEN == eval(LexicalMatch.TOKEN.__repr__())


def test_ranking_meta_data() -> None:
    assert 2 == RANKING_META_DATA.lexicon_n_gram_length
    assert LexiconType.MWE_NON_SPECIAL == RANKING_META_DATA.lexicon_type
    assert 1 == RANKING_META_DATA.lexicon_wildcard_count
    assert not RANKING_META_DATA.exclude_pos_information
    assert LexicalMatch.TOKEN == RANKING_META_DATA.lexical_match
    assert 1 == RANKING_META_DATA.token_match_start_index
    assert 3 == RANKING_META_DATA.token_match_end_index
    assert 'snow_noun boot_noun' == RANKING_META_DATA.lexicon_entry_match
    assert ('Z5', 'Z4') == RANKING_META_DATA.semantic_tags

    expected_str = ("RankingMetaData(lexicon_type=LexiconType.MWE_NON_SPECIAL, "
                    "lexicon_n_gram_length=2, "
                    "lexicon_wildcard_count=1, exclude_pos_information=False,"
                    " lexical_match=LexicalMatch.TOKEN, "
                    "token_match_start_index=1, token_match_end_index=3,"
                    " lexicon_entry_match='snow_noun boot_noun', "
                    "semantic_tags=('Z5', 'Z4'))")
    assert expected_str == str(RANKING_META_DATA)

    with pytest.raises(FrozenInstanceError):
        for attribute in ['lexicon_n_gram_length', 'lexicon_type',
                          'lexicon_wildcard_count', 'exclude_pos_information',
                          'lexical_match', 'token_match_start_index',
                          'token_match_end_index', 'lexicon_entry_match',
                          'semantic_tags']:
            setattr(RANKING_META_DATA, attribute, 'test')
    
    assert RANKING_META_DATA != RankingMetaData(LexiconType.MWE_NON_SPECIAL, 1,
                                                1, False, LexicalMatch.TOKEN, 1,
                                                3, 'snow_noun boot_noun',
                                                ('Z5', 'Z4'))
    assert RANKING_META_DATA == RankingMetaData(LexiconType.MWE_NON_SPECIAL, 2,
                                                1, False, LexicalMatch.TOKEN, 1,
                                                3, 'snow_noun boot_noun',
                                                ('Z5', 'Z4'))
    eval(RANKING_META_DATA.__repr__())
    assert RANKING_META_DATA == eval(RANKING_META_DATA.__repr__())


def test_lexicon_entry_ranker() -> None:
    
    class TestRanker(LexiconEntryRanker):

        def __call__(self, token_ranking_data: List[List[RankingMetaData]]
                     ) -> Tuple[List[List[int]], List[Optional[RankingMetaData]]]:
            return ([[0]], [None])

    concrete_ranker = TestRanker()
    assert ([[0]], [None]) == concrete_ranker([[RANKING_META_DATA]])
    assert isinstance(concrete_ranker, LexiconEntryRanker)


def test_contextual_rule_based_ranker__init__() -> None:
    ranker = ContextualRuleBasedRanker(0, 0)

    assert isinstance(ranker, LexiconEntryRanker)

    assert 1 == ranker.n_gram_number_indexes
    assert 1 == ranker.wildcards_number_indexes
    assert {} == ranker.n_gram_ranking_dictionary

    ranker = ContextualRuleBasedRanker(10, 10)
    assert 2 == ranker.n_gram_number_indexes
    assert 2 == ranker.wildcards_number_indexes
    assert {1: 10, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1} \
        == ranker.n_gram_ranking_dictionary
    
    ranker = ContextualRuleBasedRanker(10, 2)
    assert 2 == ranker.n_gram_number_indexes
    assert 1 == ranker.wildcards_number_indexes
    assert {1: 10, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1} \
        == ranker.n_gram_ranking_dictionary
    
    ranker = ContextualRuleBasedRanker(2, 10)
    assert 1 == ranker.n_gram_number_indexes
    assert 2 == ranker.wildcards_number_indexes
    assert {1: 2, 2: 1} == ranker.n_gram_ranking_dictionary


def test_contextual_rule_based_ranker__call__() -> None:
    ranker = ContextualRuleBasedRanker(2, 1)
    assert ([], []) == ranker([])

    # Test that it assigns [] and None to tokens that have
    # no rank meta data objects

    token_ranking_data: List[List[RankingMetaData]] = [
        []
    ]
    assert ([[]], [None]) == ranker(token_ranking_data)

    snow = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                           True, LexicalMatch.TOKEN, 1, 2,
                           'Snow', ('Z1',))
    token_ranking_data = [
        [],
        [
            snow
        ]
    ]
    assert ([[], [420211]], [None, snow]) == ranker(token_ranking_data)

    # Test average use case
    snow_wild_mwe = RankingMetaData(LexiconType.MWE_WILDCARD, 2, 1,
                                    False, LexicalMatch.TOKEN, 0, 2,
                                    'Snow_noun *_noun', ('Z1', 'Z2'))
    snow_boot_mwe = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 2, 0,
                                    False, LexicalMatch.LEMMA, 0, 2,
                                    'Snow_noun boot_noun', ('Z1',))
    snow_noun = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                                False, LexicalMatch.TOKEN, 0, 1,
                                'Snow|noun', ('Z1',))
    snow = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                           True, LexicalMatch.TOKEN, 0, 1,
                           'Snow', ('Z1',))
    boot_noun_token = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                                      False, LexicalMatch.TOKEN, 1, 2,
                                      'boot|noun', ('Z1',))
    boot_noun_lemma = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                                      False, LexicalMatch.LEMMA, 1, 2,
                                      'boot|noun', ('Z1',))
    boot_noun_token_lower = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                                            False, LexicalMatch.TOKEN_LOWER, 1, 2,
                                            'boot|noun', ('Z1',))
    boot_noun_lemma_lower = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                                            False, LexicalMatch.LEMMA_LOWER, 1, 2,
                                            'boot|noun', ('Z1',))
    token_ranking_data = [
        [
            snow_wild_mwe,
            snow_boot_mwe,
            snow_noun,
            snow
        ],
        [
            snow_wild_mwe,
            snow_boot_mwe,
            boot_noun_token,
            boot_noun_lemma,
            boot_noun_token_lower,
            boot_noun_lemma_lower,
        ]
    ]
    expected_ranks = [
        [
            211110,
            110120,
            420110,
            420210
        ],
        [
            211110,
            110120,
            420111,
            420121,
            420131,
            420141
        ]
    ]
    expected_lowest_ranked_matches: List[Optional[RankingMetaData]]
    expected_lowest_ranked_matches = [snow_boot_mwe, snow_boot_mwe]
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)
    
    # Testing the global ranking function, in this test we make sure that it can
    # handle ranking global decisions over local.
    north_east_mwe = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 2, 0,
                                     False, LexicalMatch.TOKEN, 0, 2,
                                     'North_noun East_noun', ('Z1',))
    north_noun = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0,
                                 False, LexicalMatch.TOKEN, 0, 1,
                                 'North|noun', ('Z1',))
    east_london_brewery_mwe = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 3, 0,
                                              False, LexicalMatch.TOKEN, 1, 4,
                                              'East_noun London_noun brewery_noun', ('Z1',))
    ranker = ContextualRuleBasedRanker(3, 0)
    token_ranking_data = [
        [
            north_east_mwe,
            north_noun
            
        ],
        [
            north_east_mwe,
            east_london_brewery_mwe
            
        ],
        [
            east_london_brewery_mwe
        ],
        [
            east_london_brewery_mwe
        ]
    ]
    expected_ranks = [
        [
            120110,
            430110
        ],
        [
            120110,
            110111
            
        ],
        [
            110111
        ],
        [
            110111
        ]
    ]
    expected_lowest_ranked_matches = [north_noun, east_london_brewery_mwe,
                                      east_london_brewery_mwe, east_london_brewery_mwe]
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)
    
    # Testing the global ranking function, in this test we make sure that it can
    # handle ranking global decision over local to the extent that the global
    # lowest rank is None due token overlap in the first token.
    token_ranking_data = [
        [
            north_east_mwe
        ],
        [
            east_london_brewery_mwe,
            north_east_mwe
        ],
        [
            east_london_brewery_mwe
        ],
        [
            east_london_brewery_mwe
        ]
    ]
    expected_ranks = [
        [
            120110
        ],
        [
            110111,
            120110
        ],
        [
            110111
        ],
        [
            110111
        ]
    ]
    expected_lowest_ranked_matches = [None, east_london_brewery_mwe,
                                      east_london_brewery_mwe, east_london_brewery_mwe]
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)

    # Testing the global ranking function, in this test we make sure that it can
    # handle ranking global decisions over local, but in this version we have
    # multiple optimal local decision.
    london_brewery_company_owners_mwe = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 4, 0,
                                                        False, LexicalMatch.TOKEN, 2, 6,
                                                        'London_noun brewery_noun company_noun owners_noun',
                                                        ('Z1',))
    ranker = ContextualRuleBasedRanker(4, 0)
    token_ranking_data = [
        [
            north_east_mwe,
            north_noun
        ],
        [
            east_london_brewery_mwe,
            north_east_mwe
        ],
        [
            east_london_brewery_mwe,
            london_brewery_company_owners_mwe
        ],
        [
            east_london_brewery_mwe,
            london_brewery_company_owners_mwe
        ],
        [
            london_brewery_company_owners_mwe
        ],
        [
            london_brewery_company_owners_mwe
        ]
    ]
    expected_ranks = [
        [
            130110,
            440110
        ],
        [
            120111,
            130110
        ],
        [
            120111,
            110112
        ],
        [
            120111,
            110112
        ],
        [
            110112
        ],
        [
            110112
        ]
    ]
    expected_lowest_ranked_matches = [north_east_mwe, north_east_mwe,
                                      london_brewery_company_owners_mwe,
                                      london_brewery_company_owners_mwe,
                                      london_brewery_company_owners_mwe,
                                      london_brewery_company_owners_mwe]
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)

    # Edge case whereby n-gram is greater than 9.
    ski_boot_ten_mwe = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 10, 0, False,
                                       LexicalMatch.TOKEN, 0, 10,
                                       'The_det ski_noun Boot_noun is_det part_det of_det a_det test_det it_det is_det',
                                       ('Z1',))
    ski_boot_nine_mwe = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 9, 0, False,
                                        LexicalMatch.TOKEN, 0, 9,
                                        '*_det ski_noun Boot_noun is_det part_det of_det a_det test_det it_det is_det',
                                        ('Z1',))
    ranker = ContextualRuleBasedRanker(10, 0)
    ranking_data = [
        ski_boot_ten_mwe,
        ski_boot_nine_mwe
    ]
    token_ranking_data = [ranking_data] * 9
    token_ranking_data.append([
        ski_boot_ten_mwe
    ])
    expected_ranks = [
        [10101100,
         10201100]
    ] * 9
    expected_ranks.append([10101100])
    expected_lowest_ranked_matches = [ski_boot_ten_mwe] * 10
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)

    # Edge case of token start index greater than 9
    ski_start_index_ten = RankingMetaData(LexiconType.SINGLE_NON_SPECIAL, 1, 0, False,
                                          LexicalMatch.TOKEN, 10, 11,
                                          'ski_noun',
                                          ('Z1',))
    token_ranking_data.append([ski_start_index_ten])
    expected_ranks.append([41001110])
    expected_lowest_ranked_matches = [ski_boot_ten_mwe] * 10
    expected_lowest_ranked_matches.append(ski_start_index_ten)
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)

    # Edge case whereby the number of wildcards in a token is greater than 9
    # Of which the wildcard that has 10 wildcards and is only 2 gram long
    # should be ranked lower than the 9 wildcards that is a wildcard
    ranker = ContextualRuleBasedRanker(2, 10)
    ski_wild_mwe = RankingMetaData(LexiconType.MWE_WILDCARD, 2, 10, False,
                                   LexicalMatch.TOKEN, 0, 2,
                                   'ski_***** *****_noun', ('Z1',))
    wild_boot_mwe = RankingMetaData(LexiconType.MWE_WILDCARD, 2, 9, False,
                                    LexicalMatch.TOKEN, 0, 2,
                                    '****_noun Boot_*****', ('Z1',))
    ranking_data = [
        ski_wild_mwe,
        wild_boot_mwe
    ]
    token_ranking_data = [ranking_data] * 2
    expected_ranks = [
        [2110110,
         2109110]
    ] * 2
    expected_lowest_ranked_matches = [wild_boot_mwe, wild_boot_mwe]
    assert (expected_ranks, expected_lowest_ranked_matches) \
        == ranker(token_ranking_data)


def test_contextual_rule_based_ranker_int_2_str() -> None:
    assert '2' == ContextualRuleBasedRanker.int_2_str(2, 1)
    assert '02' == ContextualRuleBasedRanker.int_2_str(2, 2)
    assert '312' == ContextualRuleBasedRanker.int_2_str(312, 3)
    assert '0312' == ContextualRuleBasedRanker.int_2_str(312, 4)

    with pytest.raises(ValueError):
        ContextualRuleBasedRanker.int_2_str(312, 2)


def test_contextual_rule_based_ranker_get_global_lowest_ranks() -> None:
    north_east = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 2, 0,
                                 False, LexicalMatch.TOKEN, 0, 2,
                                 'North_noun East_noun', ('Z1',))
    east_london_brewery = RankingMetaData(LexiconType.MWE_NON_SPECIAL, 3, 0,
                                          False, LexicalMatch.TOKEN, 1, 4,
                                          'East_noun London_noun brewery_noun', ('Z1',))
    token_ranking_data = [
        [
            north_east
        ],
        [
            north_east,
            east_london_brewery
        ],
        [
            east_london_brewery
        ],
        [
            east_london_brewery
        ]
    ]
    token_rankings = [[120110], [120110, 110111], [110111], [110111]]
    expected_lowest_ranked_matches = [None, east_london_brewery,
                                      east_london_brewery, east_london_brewery]
    assert (ContextualRuleBasedRanker.get_global_lowest_ranks(token_ranking_data,
                                                              token_rankings, None)
            == expected_lowest_ranked_matches)
    
    # Test that it can exclude matches
    expected_lowest_ranked_matches = [north_east, north_east, None, None]
    ranking_data_to_exclude = {east_london_brewery}
    assert (ContextualRuleBasedRanker.get_global_lowest_ranks(token_ranking_data, token_rankings,
                                                              ranking_data_to_exclude)
            == expected_lowest_ranked_matches)
    
    # Test that it raises assertion errors when the length of the inner and
    # outer lists of token ranking data and rankings do not match.

    # Outer assertion error test
    token_ranking_data = [
        [
            north_east
        ],
        [
            north_east
        ]
    ]
    token_rankings = [[120110]]
    with pytest.raises(AssertionError):
        ContextualRuleBasedRanker.get_global_lowest_ranks(token_ranking_data,
                                                          token_rankings)
    
    # Inner assertion error test
    token_rankings = [[120110], [120110, 110111]]
    with pytest.raises(AssertionError):
        ContextualRuleBasedRanker.get_global_lowest_ranks(token_ranking_data,
                                                          token_rankings)
