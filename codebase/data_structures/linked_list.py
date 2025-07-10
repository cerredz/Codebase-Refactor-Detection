from typing import Optional, Iterator, Any
from dataclasses import dataclass


@dataclass
class ListNode:
    """Node for linked list implementation"""
    value: Any
    next: Optional['ListNode'] = None
    
    def __repr__(self) -> str:
        return f"ListNode({self.value})"


class LinkedList:
    """A singly linked list implementation with common operations"""
    
    def __init__(self):
        self.head: Optional[ListNode] = None
        self.tail: Optional[ListNode] = None
        self._size = 0
    
    def append(self, value: Any) -> None:
        """Add element to the end of the list"""
        new_node = ListNode(value)
        
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        
        self._size += 1
    
    def prepend(self, value: Any) -> None:
        """Add element to the beginning of the list"""
        new_node = ListNode(value)
        
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
        
        self._size += 1
    
    def insert_at(self, index: int, value: Any) -> None:
        """Insert element at specific index"""
        if index < 0 or index > self._size:
            raise IndexError("Index out of range")
        
        if index == 0:
            self.prepend(value)
            return
        
        if index == self._size:
            self.append(value)
            return
        
        new_node = ListNode(value)
        current = self.head
        
        for _ in range(index - 1):
            current = current.next
        
        new_node.next = current.next
        current.next = new_node
        self._size += 1
    
    def remove(self, value: Any) -> bool:
        """Remove first occurrence of value"""
        if not self.head:
            return False
        
        if self.head.value == value:
            self.head = self.head.next
            if not self.head:
                self.tail = None
            self._size -= 1
            return True
        
        current = self.head
        while current.next:
            if current.next.value == value:
                if current.next == self.tail:
                    self.tail = current
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next
        
        return False
    
    def remove_at(self, index: int) -> Any:
        """Remove element at specific index"""
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
        
        if index == 0:
            value = self.head.value
            self.head = self.head.next
            if not self.head:
                self.tail = None
            self._size -= 1
            return value
        
        current = self.head
        for _ in range(index - 1):
            current = current.next
        
        value = current.next.value
        if current.next == self.tail:
            self.tail = current
        current.next = current.next.next
        self._size -= 1
        return value
    
    def find(self, value: Any) -> Optional[int]:
        """Find index of first occurrence of value"""
        current = self.head
        index = 0
        
        while current:
            if current.value == value:
                return index
            current = current.next
            index += 1
        
        return None
    
    def get(self, index: int) -> Any:
        """Get element at specific index"""
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
        
        current = self.head
        for _ in range(index):
            current = current.next
        
        return current.value
    
    def clear(self) -> None:
        """Remove all elements from the list"""
        self.head = None
        self.tail = None
        self._size = 0
    
    def reverse(self) -> None:
        """Reverse the linked list in-place"""
        if not self.head or not self.head.next:
            return
        
        prev = None
        current = self.head
        self.tail = self.head
        
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        
        self.head = prev
    
    def to_list(self) -> list:
        """Convert linked list to Python list"""
        result = []
        current = self.head
        
        while current:
            result.append(current.value)
            current = current.next
        
        return result
    
    def __len__(self) -> int:
        """Return the length of the list"""
        return self._size
    
    def __bool__(self) -> bool:
        """Return True if list is not empty"""
        return self._size > 0
    
    def __iter__(self) -> Iterator[Any]:
        """Make the list iterable"""
        current = self.head
        while current:
            yield current.value
            current = current.next
    
    def __repr__(self) -> str:
        """String representation of the list"""
        return f"LinkedList({self.to_list()})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another linked list"""
        if not isinstance(other, LinkedList):
            return False
        
        if len(self) != len(other):
            return False
        
        current_self = self.head
        current_other = other.head
        
        while current_self:
            if current_self.value != current_other.value:
                return False
            current_self = current_self.next
            current_other = current_other.next
        
        return True


class DoublyLinkedList:
    """A doubly linked list implementation for comparison"""
    
    @dataclass
    class Node:
        value: Any
        next: Optional['DoublyLinkedList.Node'] = None
        prev: Optional['DoublyLinkedList.Node'] = None
    
    def __init__(self):
        self.head: Optional[self.Node] = None
        self.tail: Optional[self.Node] = None
        self._size = 0
    
    def append(self, value: Any) -> None:
        """Add element to the end"""
        new_node = self.Node(value)
        
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        
        self._size += 1
    
    def prepend(self, value: Any) -> None:
        """Add element to the beginning"""
        new_node = self.Node(value)
        
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        
        self._size += 1
    
    def remove(self, value: Any) -> bool:
        """Remove first occurrence of value"""
        current = self.head
        
        while current:
            if current.value == value:
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next
                
                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev
                
                self._size -= 1
                return True
            
            current = current.next
        
        return False
    
    def __len__(self) -> int:
        return self._size
    
    def __iter__(self) -> Iterator[Any]:
        current = self.head
        while current:
            yield current.value
            current = current.next 