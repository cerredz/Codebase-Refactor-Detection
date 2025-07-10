from typing import List, TypeVar, Callable, Optional
import random
import heapq
from abc import ABC, abstractmethod

T = TypeVar('T')


class SortingAlgorithm(ABC):
    """Abstract base class for sorting algorithms"""
    
    @abstractmethod
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """Sort the array"""
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Return algorithm name"""
        pass


class BubbleSort(SortingAlgorithm):
    """Bubble Sort implementation with optimizations"""
    
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """
        Bubble sort with early termination optimization
        Time Complexity: O(n²) worst case, O(n) best case
        Space Complexity: O(1)
        """
        arr = arr.copy()
        n = len(arr)
        
        for i in range(n):
            swapped = False
            
            for j in range(0, n - i - 1):
                # Use key function if provided
                left_val = key(arr[j]) if key else arr[j]
                right_val = key(arr[j + 1]) if key else arr[j + 1]
                
                # Determine comparison based on reverse flag
                should_swap = (left_val > right_val) if not reverse else (left_val < right_val)
                
                if should_swap:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
            
            # If no swapping occurred, array is sorted
            if not swapped:
                break
        
        return arr
    
    def name(self) -> str:
        return "Bubble Sort"


class QuickSort(SortingAlgorithm):
    """Quick Sort implementation with randomized pivot"""
    
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """
        Quick sort with randomized pivot selection
        Time Complexity: O(n log n) average, O(n²) worst case
        Space Complexity: O(log n)
        """
        arr = arr.copy()
        self._quicksort_recursive(arr, 0, len(arr) - 1, key, reverse)
        return arr
    
    def _quicksort_recursive(self, arr: List[T], low: int, high: int, key: Optional[Callable[[T], any]], reverse: bool) -> None:
        """Recursive quicksort implementation"""
        if low < high:
            # Partition and get pivot index
            pivot_index = self._partition(arr, low, high, key, reverse)
            
            # Recursively sort elements before and after partition
            self._quicksort_recursive(arr, low, pivot_index - 1, key, reverse)
            self._quicksort_recursive(arr, pivot_index + 1, high, key, reverse)
    
    def _partition(self, arr: List[T], low: int, high: int, key: Optional[Callable[[T], any]], reverse: bool) -> int:
        """Partition function with randomized pivot"""
        # Randomize pivot to avoid worst-case performance
        random_index = random.randint(low, high)
        arr[random_index], arr[high] = arr[high], arr[random_index]
        
        pivot = key(arr[high]) if key else arr[high]
        i = low - 1
        
        for j in range(low, high):
            element_val = key(arr[j]) if key else arr[j]
            
            # Determine comparison based on reverse flag
            should_swap = (element_val <= pivot) if not reverse else (element_val >= pivot)
            
            if should_swap:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1
    
    def name(self) -> str:
        return "Quick Sort"


class MergeSort(SortingAlgorithm):
    """Merge Sort implementation"""
    
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """
        Merge sort implementation
        Time Complexity: O(n log n)
        Space Complexity: O(n)
        """
        if len(arr) <= 1:
            return arr.copy()
        
        return self._mergesort_recursive(arr, key, reverse)
    
    def _mergesort_recursive(self, arr: List[T], key: Optional[Callable[[T], any]], reverse: bool) -> List[T]:
        """Recursive merge sort implementation"""
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        left = self._mergesort_recursive(arr[:mid], key, reverse)
        right = self._mergesort_recursive(arr[mid:], key, reverse)
        
        return self._merge(left, right, key, reverse)
    
    def _merge(self, left: List[T], right: List[T], key: Optional[Callable[[T], any]], reverse: bool) -> List[T]:
        """Merge two sorted arrays"""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            left_val = key(left[i]) if key else left[i]
            right_val = key(right[j]) if key else right[j]
            
            # Determine comparison based on reverse flag
            take_left = (left_val <= right_val) if not reverse else (left_val >= right_val)
            
            if take_left:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        # Add remaining elements
        result.extend(left[i:])
        result.extend(right[j:])
        
        return result
    
    def name(self) -> str:
        return "Merge Sort"


class HeapSort(SortingAlgorithm):
    """Heap Sort implementation"""
    
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """
        Heap sort implementation
        Time Complexity: O(n log n)
        Space Complexity: O(1)
        """
        arr = arr.copy()
        n = len(arr)
        
        # Build max heap
        for i in range(n // 2 - 1, -1, -1):
            self._heapify(arr, n, i, key, reverse)
        
        # Extract elements from heap one by one
        for i in range(n - 1, 0, -1):
            arr[0], arr[i] = arr[i], arr[0]
            self._heapify(arr, i, 0, key, reverse)
        
        return arr
    
    def _heapify(self, arr: List[T], n: int, i: int, key: Optional[Callable[[T], any]], reverse: bool) -> None:
        """Heapify a subtree rooted at index i"""
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        # Compare with left child
        if left < n:
            left_val = key(arr[left]) if key else arr[left]
            largest_val = key(arr[largest]) if key else arr[largest]
            
            # For heap sort, we want max heap for ascending order
            is_greater = (left_val > largest_val) if not reverse else (left_val < largest_val)
            if is_greater:
                largest = left
        
        # Compare with right child
        if right < n:
            right_val = key(arr[right]) if key else arr[right]
            largest_val = key(arr[largest]) if key else arr[largest]
            
            is_greater = (right_val > largest_val) if not reverse else (right_val < largest_val)
            if is_greater:
                largest = right
        
        # If largest is not root, swap and continue heapifying
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            self._heapify(arr, n, largest, key, reverse)
    
    def name(self) -> str:
        return "Heap Sort"


class InsertionSort(SortingAlgorithm):
    """Insertion Sort implementation"""
    
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """
        Insertion sort implementation
        Time Complexity: O(n²) worst case, O(n) best case
        Space Complexity: O(1)
        """
        arr = arr.copy()
        
        for i in range(1, len(arr)):
            key_element = arr[i]
            j = i - 1
            
            # Move elements that are greater than key_element to one position ahead
            while j >= 0:
                current_val = key(arr[j]) if key else arr[j]
                key_val = key(key_element) if key else key_element
                
                should_move = (current_val > key_val) if not reverse else (current_val < key_val)
                
                if should_move:
                    arr[j + 1] = arr[j]
                    j -= 1
                else:
                    break
            
            arr[j + 1] = key_element
        
        return arr
    
    def name(self) -> str:
        return "Insertion Sort"


class SelectionSort(SortingAlgorithm):
    """Selection Sort implementation"""
    
    def sort(self, arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """
        Selection sort implementation
        Time Complexity: O(n²)
        Space Complexity: O(1)
        """
        arr = arr.copy()
        n = len(arr)
        
        for i in range(n):
            # Find the minimum/maximum element in remaining array
            extreme_idx = i
            
            for j in range(i + 1, n):
                extreme_val = key(arr[extreme_idx]) if key else arr[extreme_idx]
                current_val = key(arr[j]) if key else arr[j]
                
                # For ascending sort, find minimum; for descending, find maximum
                is_better = (current_val < extreme_val) if not reverse else (current_val > extreme_val)
                
                if is_better:
                    extreme_idx = j
            
            # Swap the found element with the first element
            arr[i], arr[extreme_idx] = arr[extreme_idx], arr[i]
        
        return arr
    
    def name(self) -> str:
        return "Selection Sort"


# Convenience functions
def bubble_sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
    """Bubble sort convenience function"""
    return BubbleSort().sort(arr, key, reverse)


def quick_sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
    """Quick sort convenience function"""
    return QuickSort().sort(arr, key, reverse)


def merge_sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
    """Merge sort convenience function"""
    return MergeSort().sort(arr, key, reverse)


def heap_sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
    """Heap sort convenience function"""
    return HeapSort().sort(arr, key, reverse)


def insertion_sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
    """Insertion sort convenience function"""
    return InsertionSort().sort(arr, key, reverse)


def selection_sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
    """Selection sort convenience function"""
    return SelectionSort().sort(arr, key, reverse)


def sort_comparison(arr: List[T], algorithms: Optional[List[SortingAlgorithm]] = None) -> dict:
    """Compare performance of different sorting algorithms"""
    import time
    
    if algorithms is None:
        algorithms = [BubbleSort(), QuickSort(), MergeSort(), HeapSort(), InsertionSort(), SelectionSort()]
    
    results = {}
    
    for algorithm in algorithms:
        start_time = time.time()
        sorted_arr = algorithm.sort(arr)
        end_time = time.time()
        
        results[algorithm.name()] = {
            'time': end_time - start_time,
            'result': sorted_arr
        }
    
    return results


# Hybrid sorting algorithm
class TimSort:
    """
    Simplified TimSort implementation (inspired by Python's built-in sort)
    Combines merge sort and insertion sort
    """
    
    MIN_MERGE = 32
    
    @staticmethod
    def sort(arr: List[T], key: Optional[Callable[[T], any]] = None, reverse: bool = False) -> List[T]:
        """TimSort implementation"""
        arr = arr.copy()
        n = len(arr)
        
        if n < 2:
            return arr
        
        # Sort individual subarrays of size MIN_MERGE using insertion sort
        for start in range(0, n, TimSort.MIN_MERGE):
            end = min(start + TimSort.MIN_MERGE - 1, n - 1)
            TimSort._insertion_sort_range(arr, start, end, key, reverse)
        
        # Start merging from size MIN_MERGE
        size = TimSort.MIN_MERGE
        while size < n:
            for start in range(0, n, size * 2):
                mid = start + size - 1
                end = min(start + size * 2 - 1, n - 1)
                
                if mid < end:
                    TimSort._merge_range(arr, start, mid, end, key, reverse)
            
            size *= 2
        
        return arr
    
    @staticmethod
    def _insertion_sort_range(arr: List[T], left: int, right: int, key: Optional[Callable[[T], any]], reverse: bool) -> None:
        """Insertion sort for a specific range"""
        for i in range(left + 1, right + 1):
            key_element = arr[i]
            j = i - 1
            
            while j >= left:
                current_val = key(arr[j]) if key else arr[j]
                key_val = key(key_element) if key else key_element
                
                should_move = (current_val > key_val) if not reverse else (current_val < key_val)
                
                if should_move:
                    arr[j + 1] = arr[j]
                    j -= 1
                else:
                    break
            
            arr[j + 1] = key_element
    
    @staticmethod
    def _merge_range(arr: List[T], left: int, mid: int, right: int, key: Optional[Callable[[T], any]], reverse: bool) -> None:
        """Merge function for specific range"""
        left_part = arr[left:mid + 1]
        right_part = arr[mid + 1:right + 1]
        
        i = j = 0
        k = left
        
        while i < len(left_part) and j < len(right_part):
            left_val = key(left_part[i]) if key else left_part[i]
            right_val = key(right_part[j]) if key else right_part[j]
            
            take_left = (left_val <= right_val) if not reverse else (left_val >= right_val)
            
            if take_left:
                arr[k] = left_part[i]
                i += 1
            else:
                arr[k] = right_part[j]
                j += 1
            k += 1
        
        while i < len(left_part):
            arr[k] = left_part[i]
            i += 1
            k += 1
        
        while j < len(right_part):
            arr[k] = right_part[j]
            j += 1
            k += 1 