from typing import List, TypeVar, Optional, Callable, Tuple
import math
from abc import ABC, abstractmethod

T = TypeVar('T')


class SearchResult:
    """Class to represent search results with additional metadata"""
    
    def __init__(self, found: bool, index: Optional[int] = None, value: Optional[T] = None, 
                 comparisons: int = 0, iterations: int = 0):
        self.found = found
        self.index = index
        self.value = value
        self.comparisons = comparisons
        self.iterations = iterations
    
    def __bool__(self) -> bool:
        return self.found
    
    def __repr__(self) -> str:
        if self.found:
            return f"SearchResult(found=True, index={self.index}, comparisons={self.comparisons})"
        return f"SearchResult(found=False, comparisons={self.comparisons})"


class SearchAlgorithm(ABC):
    """Abstract base class for search algorithms"""
    
    @abstractmethod
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """Search for target in array"""
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Return algorithm name"""
        pass


class LinearSearch(SearchAlgorithm):
    """Linear Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Linear search algorithm
        Time Complexity: O(n)
        Space Complexity: O(1)
        """
        comparisons = 0
        target_val = key(target) if key else target
        
        for i, element in enumerate(arr):
            comparisons += 1
            element_val = key(element) if key else element
            
            if element_val == target_val:
                return SearchResult(True, i, element, comparisons, i + 1)
        
        return SearchResult(False, comparisons=comparisons, iterations=len(arr))
    
    def name(self) -> str:
        return "Linear Search"


class BinarySearch(SearchAlgorithm):
    """Binary Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Binary search algorithm (requires sorted array)
        Time Complexity: O(log n)
        Space Complexity: O(1)
        """
        left, right = 0, len(arr) - 1
        comparisons = 0
        iterations = 0
        target_val = key(target) if key else target
        
        while left <= right:
            iterations += 1
            mid = (left + right) // 2
            mid_val = key(arr[mid]) if key else arr[mid]
            comparisons += 1
            
            if mid_val == target_val:
                return SearchResult(True, mid, arr[mid], comparisons, iterations)
            elif mid_val < target_val:
                left = mid + 1
            else:
                right = mid - 1
            
            comparisons += 1  # For the comparison in elif
        
        return SearchResult(False, comparisons=comparisons, iterations=iterations)
    
    def name(self) -> str:
        return "Binary Search"


class RecursiveBinarySearch(SearchAlgorithm):
    """Recursive Binary Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Recursive binary search algorithm
        Time Complexity: O(log n)
        Space Complexity: O(log n) due to recursion
        """
        self._comparisons = 0
        self._iterations = 0
        target_val = key(target) if key else target
        
        result_index = self._binary_search_recursive(arr, target_val, 0, len(arr) - 1, key)
        
        if result_index != -1:
            return SearchResult(True, result_index, arr[result_index], self._comparisons, self._iterations)
        return SearchResult(False, comparisons=self._comparisons, iterations=self._iterations)
    
    def _binary_search_recursive(self, arr: List[T], target_val: any, left: int, right: int, 
                                key: Optional[Callable[[T], any]]) -> int:
        """Recursive helper for binary search"""
        if left > right:
            return -1
        
        self._iterations += 1
        mid = (left + right) // 2
        mid_val = key(arr[mid]) if key else arr[mid]
        self._comparisons += 1
        
        if mid_val == target_val:
            return mid
        elif mid_val < target_val:
            self._comparisons += 1
            return self._binary_search_recursive(arr, target_val, mid + 1, right, key)
        else:
            self._comparisons += 1
            return self._binary_search_recursive(arr, target_val, left, mid - 1, key)
    
    def name(self) -> str:
        return "Recursive Binary Search"


class InterpolationSearch(SearchAlgorithm):
    """Interpolation Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Interpolation search algorithm (requires sorted array of uniformly distributed data)
        Time Complexity: O(log log n) average, O(n) worst case
        Space Complexity: O(1)
        """
        if not arr:
            return SearchResult(False)
        
        left, right = 0, len(arr) - 1
        comparisons = 0
        iterations = 0
        target_val = key(target) if key else target
        
        # Handle non-numeric data by falling back to binary search
        try:
            # Test if we can perform arithmetic operations
            left_val = key(arr[left]) if key else arr[left]
            right_val = key(arr[right]) if key else arr[right]
            _ = (target_val - left_val) / (right_val - left_val)
        except (TypeError, ZeroDivisionError):
            # Fall back to binary search for non-numeric data
            return BinarySearch().search(arr, target, key)
        
        while left <= right:
            iterations += 1
            left_val = key(arr[left]) if key else arr[left]
            right_val = key(arr[right]) if key else arr[right]
            
            comparisons += 1
            if left_val == target_val:
                return SearchResult(True, left, arr[left], comparisons, iterations)
            
            comparisons += 1
            if right_val == target_val:
                return SearchResult(True, right, arr[right], comparisons, iterations)
            
            # Interpolation formula
            if left_val == right_val:
                break
            
            try:
                pos = left + int(((target_val - left_val) / (right_val - left_val)) * (right - left))
                pos = max(left, min(pos, right))  # Ensure pos is within bounds
            except (ZeroDivisionError, OverflowError):
                # Fall back to binary search calculation
                pos = (left + right) // 2
            
            pos_val = key(arr[pos]) if key else arr[pos]
            comparisons += 1
            
            if pos_val == target_val:
                return SearchResult(True, pos, arr[pos], comparisons, iterations)
            elif pos_val < target_val:
                left = pos + 1
            else:
                right = pos - 1
            
            comparisons += 1  # For the elif comparison
        
        return SearchResult(False, comparisons=comparisons, iterations=iterations)
    
    def name(self) -> str:
        return "Interpolation Search"


class ExponentialSearch(SearchAlgorithm):
    """Exponential Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Exponential search algorithm
        Time Complexity: O(log n)
        Space Complexity: O(1)
        """
        if not arr:
            return SearchResult(False)
        
        comparisons = 0
        iterations = 0
        target_val = key(target) if key else target
        
        # If target is at first position
        first_val = key(arr[0]) if key else arr[0]
        comparisons += 1
        if first_val == target_val:
            return SearchResult(True, 0, arr[0], comparisons, 1)
        
        # Find range for binary search
        bound = 1
        while bound < len(arr):
            iterations += 1
            bound_val = key(arr[bound]) if key else arr[bound]
            comparisons += 1
            
            if bound_val >= target_val:
                break
            bound *= 2
        
        # Perform binary search in found range
        left = bound // 2
        right = min(bound, len(arr) - 1)
        
        binary_search = BinarySearch()
        sub_array = arr[left:right + 1]
        result = binary_search.search(sub_array, target, key)
        
        if result.found:
            actual_index = left + result.index
            return SearchResult(True, actual_index, arr[actual_index], 
                              comparisons + result.comparisons, iterations + result.iterations)
        
        return SearchResult(False, comparisons=comparisons + result.comparisons, 
                          iterations=iterations + result.iterations)
    
    def name(self) -> str:
        return "Exponential Search"


class JumpSearch(SearchAlgorithm):
    """Jump Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Jump search algorithm
        Time Complexity: O(√n)
        Space Complexity: O(1)
        """
        if not arr:
            return SearchResult(False)
        
        n = len(arr)
        step = int(math.sqrt(n))
        prev = 0
        comparisons = 0
        iterations = 0
        target_val = key(target) if key else target
        
        # Find the block where element is present
        while prev < n:
            iterations += 1
            current_index = min(step, n) - 1
            current_val = key(arr[current_index]) if key else arr[current_index]
            comparisons += 1
            
            if current_val >= target_val:
                break
            
            prev = step
            step += int(math.sqrt(n))
        
        # Linear search in the identified block
        start = prev
        end = min(step, n)
        
        for i in range(start, end):
            iterations += 1
            element_val = key(arr[i]) if key else arr[i]
            comparisons += 1
            
            if element_val == target_val:
                return SearchResult(True, i, arr[i], comparisons, iterations)
            elif element_val > target_val:
                break
        
        return SearchResult(False, comparisons=comparisons, iterations=iterations)
    
    def name(self) -> str:
        return "Jump Search"


class TernarySearch(SearchAlgorithm):
    """Ternary Search implementation"""
    
    def search(self, arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
        """
        Ternary search algorithm (requires sorted array)
        Time Complexity: O(log₃ n)
        Space Complexity: O(1)
        """
        left, right = 0, len(arr) - 1
        comparisons = 0
        iterations = 0
        target_val = key(target) if key else target
        
        while left <= right:
            iterations += 1
            mid1 = left + (right - left) // 3
            mid2 = right - (right - left) // 3
            
            mid1_val = key(arr[mid1]) if key else arr[mid1]
            mid2_val = key(arr[mid2]) if key else arr[mid2]
            
            comparisons += 1
            if mid1_val == target_val:
                return SearchResult(True, mid1, arr[mid1], comparisons, iterations)
            
            comparisons += 1
            if mid2_val == target_val:
                return SearchResult(True, mid2, arr[mid2], comparisons, iterations)
            
            comparisons += 1
            if target_val < mid1_val:
                right = mid1 - 1
            elif target_val > mid2_val:
                comparisons += 1
                left = mid2 + 1
            else:
                comparisons += 1
                left = mid1 + 1
                right = mid2 - 1
        
        return SearchResult(False, comparisons=comparisons, iterations=iterations)
    
    def name(self) -> str:
        return "Ternary Search"


# Convenience functions
def linear_search(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Linear search convenience function"""
    return LinearSearch().search(arr, target, key)


def binary_search(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Binary search convenience function"""
    return BinarySearch().search(arr, target, key)


def interpolation_search(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Interpolation search convenience function"""
    return InterpolationSearch().search(arr, target, key)


def exponential_search(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Exponential search convenience function"""
    return ExponentialSearch().search(arr, target, key)


def jump_search(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Jump search convenience function"""
    return JumpSearch().search(arr, target, key)


def ternary_search(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Ternary search convenience function"""
    return TernarySearch().search(arr, target, key)


def find_all_occurrences(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> List[int]:
    """Find all occurrences of target in array"""
    indices = []
    target_val = key(target) if key else target
    
    for i, element in enumerate(arr):
        element_val = key(element) if key else element
        if element_val == target_val:
            indices.append(i)
    
    return indices


def find_first_occurrence(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Find first occurrence of target in sorted array using binary search"""
    if not arr:
        return SearchResult(False)
    
    left, right = 0, len(arr) - 1
    result_index = -1
    comparisons = 0
    iterations = 0
    target_val = key(target) if key else target
    
    while left <= right:
        iterations += 1
        mid = (left + right) // 2
        mid_val = key(arr[mid]) if key else arr[mid]
        comparisons += 1
        
        if mid_val == target_val:
            result_index = mid
            right = mid - 1  # Continue searching left for first occurrence
        elif mid_val < target_val:
            comparisons += 1
            left = mid + 1
        else:
            comparisons += 1
            right = mid - 1
    
    if result_index != -1:
        return SearchResult(True, result_index, arr[result_index], comparisons, iterations)
    return SearchResult(False, comparisons=comparisons, iterations=iterations)


def find_last_occurrence(arr: List[T], target: T, key: Optional[Callable[[T], any]] = None) -> SearchResult:
    """Find last occurrence of target in sorted array using binary search"""
    if not arr:
        return SearchResult(False)
    
    left, right = 0, len(arr) - 1
    result_index = -1
    comparisons = 0
    iterations = 0
    target_val = key(target) if key else target
    
    while left <= right:
        iterations += 1
        mid = (left + right) // 2
        mid_val = key(arr[mid]) if key else arr[mid]
        comparisons += 1
        
        if mid_val == target_val:
            result_index = mid
            left = mid + 1  # Continue searching right for last occurrence
        elif mid_val < target_val:
            comparisons += 1
            left = mid + 1
        else:
            comparisons += 1
            right = mid - 1
    
    if result_index != -1:
        return SearchResult(True, result_index, arr[result_index], comparisons, iterations)
    return SearchResult(False, comparisons=comparisons, iterations=iterations)


def search_comparison(arr: List[T], target: T, algorithms: Optional[List[SearchAlgorithm]] = None) -> dict:
    """Compare performance of different search algorithms"""
    import time
    
    if algorithms is None:
        algorithms = [
            LinearSearch(), 
            BinarySearch(), 
            InterpolationSearch(), 
            ExponentialSearch(),
            JumpSearch(),
            TernarySearch()
        ]
    
    results = {}
    
    for algorithm in algorithms:
        start_time = time.time()
        result = algorithm.search(arr, target)
        end_time = time.time()
        
        results[algorithm.name()] = {
            'time': end_time - start_time,
            'result': result,
            'found': result.found,
            'index': result.index,
            'comparisons': result.comparisons,
            'iterations': result.iterations
        }
    
    return results


class PatternSearch:
    """String pattern searching algorithms"""
    
    @staticmethod
    def naive_search(text: str, pattern: str) -> List[int]:
        """
        Naive pattern searching algorithm
        Time Complexity: O(n*m) where n=text length, m=pattern length
        """
        positions = []
        n, m = len(text), len(pattern)
        
        for i in range(n - m + 1):
            if text[i:i + m] == pattern:
                positions.append(i)
        
        return positions
    
    @staticmethod
    def kmp_search(text: str, pattern: str) -> List[int]:
        """
        Knuth-Morris-Pratt pattern searching algorithm
        Time Complexity: O(n + m)
        """
        def compute_lps_array(pattern: str) -> List[int]:
            """Compute Longest Prefix Suffix array"""
            m = len(pattern)
            lps = [0] * m
            length = 0
            i = 1
            
            while i < m:
                if pattern[i] == pattern[length]:
                    length += 1
                    lps[i] = length
                    i += 1
                else:
                    if length != 0:
                        length = lps[length - 1]
                    else:
                        lps[i] = 0
                        i += 1
            
            return lps
        
        positions = []
        n, m = len(text), len(pattern)
        
        if m == 0:
            return positions
        
        lps = compute_lps_array(pattern)
        i = j = 0
        
        while i < n:
            if pattern[j] == text[i]:
                i += 1
                j += 1
            
            if j == m:
                positions.append(i - j)
                j = lps[j - 1]
            elif i < n and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        
        return positions
    
    @staticmethod
    def rabin_karp_search(text: str, pattern: str, prime: int = 101) -> List[int]:
        """
        Rabin-Karp pattern searching algorithm using rolling hash
        Time Complexity: O(n + m) average, O(n*m) worst case
        """
        positions = []
        n, m = len(text), len(pattern)
        
        if m > n:
            return positions
        
        # Calculate hash values
        pattern_hash = 0
        window_hash = 0
        h = 1
        
        # Calculate h = pow(256, m-1) % prime
        for _ in range(m - 1):
            h = (h * 256) % prime
        
        # Calculate initial hash values
        for i in range(m):
            pattern_hash = (256 * pattern_hash + ord(pattern[i])) % prime
            window_hash = (256 * window_hash + ord(text[i])) % prime
        
        # Slide the pattern over text
        for i in range(n - m + 1):
            # Check if hash values match
            if pattern_hash == window_hash:
                # Check character by character
                if text[i:i + m] == pattern:
                    positions.append(i)
            
            # Calculate hash for next window
            if i < n - m:
                window_hash = (256 * (window_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
                if window_hash < 0:
                    window_hash += prime
        
        return positions 