from typing import Optional, List, Any, Iterator
from collections import deque
import json


class TreeNode:
    """Node for binary tree implementation"""
    
    def __init__(self, value: Any):
        self.value = value
        self.left: Optional['TreeNode'] = None
        self.right: Optional['TreeNode'] = None
        self.parent: Optional['TreeNode'] = None
    
    def __repr__(self) -> str:
        return f"TreeNode({self.value})"
    
    def is_leaf(self) -> bool:
        """Check if node is a leaf (no children)"""
        return self.left is None and self.right is None
    
    def is_full(self) -> bool:
        """Check if node has both children"""
        return self.left is not None and self.right is not None


class BinaryTree:
    """A general binary tree implementation"""
    
    def __init__(self, root_value: Any = None):
        self.root: Optional[TreeNode] = TreeNode(root_value) if root_value is not None else None
        self._size = 1 if root_value is not None else 0
    
    def insert_left(self, parent_node: TreeNode, value: Any) -> TreeNode:
        """Insert a new node as left child"""
        new_node = TreeNode(value)
        new_node.parent = parent_node
        
        if parent_node.left:
            new_node.left = parent_node.left
            parent_node.left.parent = new_node
        
        parent_node.left = new_node
        self._size += 1
        return new_node
    
    def insert_right(self, parent_node: TreeNode, value: Any) -> TreeNode:
        """Insert a new node as right child"""
        new_node = TreeNode(value)
        new_node.parent = parent_node
        
        if parent_node.right:
            new_node.right = parent_node.right
            parent_node.right.parent = new_node
        
        parent_node.right = new_node
        self._size += 1
        return new_node
    
    def find(self, value: Any) -> Optional[TreeNode]:
        """Find a node with the given value using BFS"""
        if not self.root:
            return None
        
        queue = deque([self.root])
        
        while queue:
            current = queue.popleft()
            
            if current.value == value:
                return current
            
            if current.left:
                queue.append(current.left)
            if current.right:
                queue.append(current.right)
        
        return None
    
    def height(self, node: Optional[TreeNode] = None) -> int:
        """Calculate height of tree from given node (or root)"""
        if node is None:
            node = self.root
        
        if node is None:
            return -1
        
        if node.is_leaf():
            return 0
        
        left_height = self.height(node.left) if node.left else -1
        right_height = self.height(node.right) if node.right else -1
        
        return 1 + max(left_height, right_height)
    
    def depth(self, node: TreeNode) -> int:
        """Calculate depth of a node (distance from root)"""
        if node == self.root:
            return 0
        
        depth = 0
        current = node
        
        while current.parent:
            depth += 1
            current = current.parent
        
        return depth
    
    def size(self) -> int:
        """Return number of nodes in tree"""
        return self._size
    
    def is_complete(self) -> bool:
        """Check if tree is complete (all levels filled except possibly last)"""
        if not self.root:
            return True
        
        queue = deque([self.root])
        flag = False
        
        while queue:
            node = queue.popleft()
            
            if node.left:
                if flag:
                    return False
                queue.append(node.left)
            else:
                flag = True
            
            if node.right:
                if flag:
                    return False
                queue.append(node.right)
            else:
                flag = True
        
        return True
    
    def is_full(self) -> bool:
        """Check if tree is full (every node has 0 or 2 children)"""
        if not self.root:
            return True
        
        queue = deque([self.root])
        
        while queue:
            node = queue.popleft()
            
            if (node.left is None) != (node.right is None):
                return False
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        return True
    
    # Traversal methods
    def inorder_traversal(self, node: Optional[TreeNode] = None) -> List[Any]:
        """Inorder traversal (left, root, right)"""
        if node is None:
            node = self.root
        
        if node is None:
            return []
        
        result = []
        result.extend(self.inorder_traversal(node.left))
        result.append(node.value)
        result.extend(self.inorder_traversal(node.right))
        
        return result
    
    def preorder_traversal(self, node: Optional[TreeNode] = None) -> List[Any]:
        """Preorder traversal (root, left, right)"""
        if node is None:
            node = self.root
        
        if node is None:
            return []
        
        result = []
        result.append(node.value)
        result.extend(self.preorder_traversal(node.left))
        result.extend(self.preorder_traversal(node.right))
        
        return result
    
    def postorder_traversal(self, node: Optional[TreeNode] = None) -> List[Any]:
        """Postorder traversal (left, right, root)"""
        if node is None:
            node = self.root
        
        if node is None:
            return []
        
        result = []
        result.extend(self.postorder_traversal(node.left))
        result.extend(self.postorder_traversal(node.right))
        result.append(node.value)
        
        return result
    
    def level_order_traversal(self) -> List[Any]:
        """Level-order traversal (BFS)"""
        if not self.root:
            return []
        
        result = []
        queue = deque([self.root])
        
        while queue:
            node = queue.popleft()
            result.append(node.value)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        return result
    
    def get_leaves(self) -> List[TreeNode]:
        """Get all leaf nodes"""
        if not self.root:
            return []
        
        leaves = []
        queue = deque([self.root])
        
        while queue:
            node = queue.popleft()
            
            if node.is_leaf():
                leaves.append(node)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        return leaves
    
    def __len__(self) -> int:
        return self._size
    
    def __bool__(self) -> bool:
        return self.root is not None
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate through tree in level order"""
        for value in self.level_order_traversal():
            yield value
    
    def __repr__(self) -> str:
        return f"BinaryTree({self.level_order_traversal()})"


class BinarySearchTree(BinaryTree):
    """Binary Search Tree implementation with ordering"""
    
    def __init__(self):
        super().__init__()
    
    def insert(self, value: Any) -> TreeNode:
        """Insert value maintaining BST property"""
        if not self.root:
            self.root = TreeNode(value)
            self._size = 1
            return self.root
        
        return self._insert_recursive(self.root, value)
    
    def _insert_recursive(self, node: TreeNode, value: Any) -> TreeNode:
        """Recursive helper for insertion"""
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
                node.left.parent = node
                self._size += 1
                return node.left
            else:
                return self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
                node.right.parent = node
                self._size += 1
                return node.right
            else:
                return self._insert_recursive(node.right, value)
    
    def search(self, value: Any) -> Optional[TreeNode]:
        """Search for value in BST"""
        return self._search_recursive(self.root, value)
    
    def _search_recursive(self, node: Optional[TreeNode], value: Any) -> Optional[TreeNode]:
        """Recursive helper for search"""
        if node is None or node.value == value:
            return node
        
        if value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)
    
    def delete(self, value: Any) -> bool:
        """Delete value from BST"""
        node_to_delete = self.search(value)
        if not node_to_delete:
            return False
        
        self._delete_node(node_to_delete)
        self._size -= 1
        return True
    
    def _delete_node(self, node: TreeNode) -> None:
        """Delete a specific node"""
        # Case 1: Node is leaf
        if node.is_leaf():
            if node.parent:
                if node.parent.left == node:
                    node.parent.left = None
                else:
                    node.parent.right = None
            else:
                self.root = None
        
        # Case 2: Node has one child
        elif node.left is None or node.right is None:
            child = node.left if node.left else node.right
            
            if node.parent:
                if node.parent.left == node:
                    node.parent.left = child
                else:
                    node.parent.right = child
                child.parent = node.parent
            else:
                self.root = child
                child.parent = None
        
        # Case 3: Node has two children
        else:
            successor = self._find_min(node.right)
            node.value = successor.value
            self._delete_node(successor)
    
    def _find_min(self, node: TreeNode) -> TreeNode:
        """Find minimum value node in subtree"""
        while node.left:
            node = node.left
        return node
    
    def _find_max(self, node: TreeNode) -> TreeNode:
        """Find maximum value node in subtree"""
        while node.right:
            node = node.right
        return node
    
    def is_valid_bst(self, node: Optional[TreeNode] = None, min_val: float = float('-inf'), max_val: float = float('inf')) -> bool:
        """Validate if tree maintains BST property"""
        if node is None:
            node = self.root
        
        if node is None:
            return True
        
        if node.value <= min_val or node.value >= max_val:
            return False
        
        return (self.is_valid_bst(node.left, min_val, node.value) and 
                self.is_valid_bst(node.right, node.value, max_val))


class AVLTree(BinarySearchTree):
    """Self-balancing AVL Tree implementation"""
    
    def __init__(self):
        super().__init__()
    
    def _get_height(self, node: Optional[TreeNode]) -> int:
        """Get height of node (handling None case)"""
        if node is None:
            return 0
        return getattr(node, 'height', 0)
    
    def _update_height(self, node: TreeNode) -> None:
        """Update height of node"""
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
    
    def _get_balance(self, node: TreeNode) -> int:
        """Get balance factor of node"""
        return self._get_height(node.left) - self._get_height(node.right)
    
    def _rotate_right(self, node: TreeNode) -> TreeNode:
        """Perform right rotation"""
        left_child = node.left
        node.left = left_child.right
        left_child.right = node
        
        self._update_height(node)
        self._update_height(left_child)
        
        return left_child
    
    def _rotate_left(self, node: TreeNode) -> TreeNode:
        """Perform left rotation"""
        right_child = node.right
        node.right = right_child.left
        right_child.left = node
        
        self._update_height(node)
        self._update_height(right_child)
        
        return right_child 