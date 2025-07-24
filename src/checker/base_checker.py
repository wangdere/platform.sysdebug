# checker/base_checker.py
class BaseChecker:
    def run(self, o_HSDConnection):
        """每个检查器返回 (passed: bool, message: str)"""
        raise NotImplementedError