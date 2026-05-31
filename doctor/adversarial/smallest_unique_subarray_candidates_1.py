from __future__ import annotations

import pytest

from doctor.adversarial.smallest_unique_subarray_candidates import (
    reference_oracle_wrapper,
    wrong_adjacent_pair_only,
    wrong_distinct_cover_window,
    wrong_set_count_no_order,
    wrong_singleton_unique_only,
)
from doctor.adversarial.smallest_unique_subarray_oracle import (
    brute_force_smallest_unique_subarray,
)


class TestOracle:
    def test_example_all_same(self) -> None:
        assert brute_force_smallest_unique_subarray([3, 3, 3]) == 3

    def test_example_singleton(self) -> None:
        assert brute_force_smallest_unique_subarray([2, 1, 2, 3, 3]) == 1

    def test_example_pair_unique(self) -> None:
        assert brute_force_smallest_unique_subarray([1, 1, 2, 2, 1]) == 2

    def test_single_element(self) -> None:
        assert brute_force_smallest_unique_subarray([5]) == 1

    def test_all_distinct(self) -> None:
        assert brute_force_smallest_unique_subarray([1, 2, 3, 4]) == 1

    def test_two_same(self) -> None:
        assert brute_force_smallest_unique_subarray([7, 7]) == 2

    def test_reference_wrapper_matches(self) -> None:
        cases = [
            [3, 3, 3],
            [2, 1, 2, 3, 3],
            [1, 1, 2, 2, 1],
            [1, 2, 1, 2],
            [1, 2, 3, 1, 2, 3],
        ]
        for nums in cases:
            assert reference_oracle_wrapper(nums) == brute_force_smallest_unique_subarray(nums)

    def test_oracle_raises_on_oversize(self) -> None:
        with pytest.raises(ValueError, match="Oracle bound exceeded"):
            brute_force_smallest_unique_subarray(list(range(100)))


class TestExhaustiveTiny:
    def test_exhaustive_n1(self) -> None:
        for v in range(1, 4):
            assert brute_force_smallest_unique_subarray([v]) == 1, f"n=1 v={v}"

    def test_exhaustive_n2(self) -> None:
        for v1 in range(1, 4):
            for v2 in range(1, 4):
                nums = [v1, v2]
                result = brute_force_smallest_unique_subarray(nums)
                if v1 == v2:
                    assert result == 2, f"n=2 {nums}"
                else:
                    assert result == 1, f"n=2 {nums}"

    def test_exhaustive_n3_over_2vals(self) -> None:
        for v1 in range(1, 3):
            for v2 in range(1, 3):
                for v3 in range(1, 3):
                    nums = [v1, v2, v3]
                    result = brute_force_smallest_unique_subarray(nums)
                    assert 1 <= result <= 3, f"n=3 {nums}"

    def test_exhaustive_n4_over_2vals_no_crash(self) -> None:
        for v1 in range(1, 3):
            for v2 in range(1, 3):
                for v3 in range(1, 3):
                    for v4 in range(1, 3):
                        nums = [v1, v2, v3, v4]
                        result = brute_force_smallest_unique_subarray(nums)
                        assert 1 <= result <= 4, f"n=4 {nums}"


class TestWrongCandidates:
    """Each wrong candidate should fail at least one probe case."""

    def test_wrong_singleton_unique_only_fails(self) -> None:
        nums = [1, 1, 2, 2, 1]  # expected 2, wrong returns 5
        assert wrong_singleton_unique_only(nums) != brute_force_smallest_unique_subarray(nums)

    def test_wrong_distinct_cover_window_fails(self) -> None:
        nums = [1, 1, 2, 2, 1]  # distinct cover returns 2 (same), but also on [1,2,1,2]
        nums2 = [1, 2, 1, 2]  # expected 2, distinct cover returns 2? Actually distinct=2, need to find case
        nums3 = [3, 3, 3]  # expected 3, distinct cover returns 3? distinct=1 so returns n=3
        # Try [1,1,2,3,3] -> expected=1, distinct cover: distinct={1,2,3}, need=3
        # window [1,1,2,3] covers all 3 distinct -> length 4 but best would be smaller
        nums4 = [1, 1, 2, 3, 3]  # expected 1 (singleton 2)
        # Actually some of these might accidentally match. The key failing case:
        # [1,2,3,1,2] -> expected 3 (no singleton, no pair unique)
        # distinct cover: distinct={1,2,3}, need=3, window [1,2,3] length 3
        # That accidentally matches. Let's use a case where answer > distinct_cover
        nums5 = [1, 1, 2, 2, 3, 3]  # expected=2 (pair [1,2] appears once at [0:2]? No, check)
        # [1,1,2,2,3,3]: L=1 counts: 1->2,2->2,3->2 all >1; L=2: (1,1)->1, (1,2)->1... actually
        # This might be 2. Let me just check reference:
        oracle = brute_force_smallest_unique_subarray
        # Order-matters case: [1,2,2,1] expected 2, distinct_cover: distinct={1,2}, min window = 2
        # They match. Use [1,2,3,1,2,3] expected 3, distinct_cover: distinct={1,2,3}, window [1,2,3]=3 match.
        # Hmm, need case where answer > distinct_count
        # [1,1,2,2,3,3]: if answer is 2, distinct_count=3, distinct_cover=2 — match
        # Let me find ANY case where they differ:
        case = [1, 2, 1, 2, 3, 3]  # L=1: 1->2,2->2,3->2; L=2: (1,2)->1 -> answer=2
        # distinct_cover: distinct={1,2,3}, need=3, min window covering all three...
        # [1,2,1,2] covers {1,2} not 3. [1,2,1,2,3] covers all 3 -> length 5. So distinct_cover=5
        # Answer is 2. They DIFFER!
        assert wrong_distinct_cover_window(case) != oracle(case)

    def test_wrong_adjacent_pair_only_fails(self) -> None:
        # Case where answer is 3 but wrong_adjacent_pair_only returns 4 (n)
        nums = [1, 2, 3, 1, 2, 3, 1, 2, 3]  # all triplets appear 3 times
        oracle = brute_force_smallest_unique_subarray(nums)
        pair_result = wrong_adjacent_pair_only(nums)
        assert pair_result != oracle, f"pair_only returned {pair_result}, oracle={oracle}"

    def test_wrong_set_count_no_order_fails(self) -> None:
        # Case where order matters: [1,2,1,2,1,2]
        # All L=1 values appear 3 times. L=2: (1,2)->3, (2,1)->3. L=3: (1,2,1)->2, (2,1,2)->2. L=4: all appear once -> answer=4
        # Set version: L=1 same; L=2: {1,2} frozenset -> 6 (all L=2 subarrays) -> would skip; L=3: {1,2} again all; L=4: {1,2} again all -> returns 6
        nums = [1, 2, 1, 2, 1, 2]
        oracle = brute_force_smallest_unique_subarray(nums)
        set_result = wrong_set_count_no_order(nums)
        assert set_result != oracle, f"set_count returned {set_result}, oracle={oracle}"


class TestCandidatePassRates:
    """The reference oracle should pass all probe cases from the runner."""

    PROBE_CASES = [
        [3, 3, 3],
        [2, 1, 2, 3, 3],
        [1, 1, 2, 2, 1],
        [5, 5, 5, 5],
        [7, 7],
        [9],
        [4, 4, 4, 5],
        [6, 7, 7, 7],
        [1, 2, 1, 2],
        [3, 3, 1, 1, 3, 3],
        [1, 1, 2, 2, 3, 3],
        [1, 2, 1, 2, 1, 2],
        [1, 1, 1, 2, 2, 2],
        [1, 2, 2, 1],
        [1, 2, 1, 2, 2, 1],
        [1, 2, 3, 2, 1, 2, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [1, 1],
        [1, 2],
        [1, 2, 3, 1, 2],
        [2, 2, 1, 2, 2],
    ]

    def test_reference_passes_all(self) -> None:
        for nums in self.PROBE_CASES:
            expected = brute_force_smallest_unique_subarray(nums)
            assert reference_oracle_wrapper(nums) == expected, f"failed on {nums}"
