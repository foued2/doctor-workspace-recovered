class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        
        def dfs(i, j, idx):
            if idx == len(word): # all characters matched
                return True
            
            if i < 0 or i >= len(board) or j < 0 or j >= len(board[0]) or board[i][j] != word[idx]:
                # out of board bounds or character not matching
                return False
            
            # mark board position as visited
            board[i][j] = '#'
            
            # check adjacent cells
            res = dfs(i+1, j, idx+1) or dfs(i-1, j, idx+1) or dfs(i, j+1, idx+1) or dfs(i, j-1, idx+1)
            
            # unmark board position to make it consider for other paths
            board[i][j] = word[idx]
            
            return res
        
        # iterate board cells and start dfs search
        for i in range(len(board)):
            for j in range(len(board[0])):
                if dfs(i, j, 0):
                    return True
        
        return False