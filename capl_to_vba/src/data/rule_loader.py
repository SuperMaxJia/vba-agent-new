import os
from typing import Optional

class RuleLoader:
    """规则加载器类"""
    def __init__(self):
        self.capl_to_vba_map = {}
        self.vba_rule_map = {}
        
    def load_rules(self):
        """加载所有规则"""
        self._load_capl_to_vba_mapping()
        self._load_vba_rules()
        
    def _load_capl_to_vba_mapping(self):
        """加载CAPL到VBA的映射规则"""
        mapping_dir = "/Users/cuisijia/source/rule-reflection/output/reflection"
        for filename in os.listdir(mapping_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(mapping_dir, filename), "r") as f:
                    content = f.read()
                    # 解析文件名获取规则名称
                    rule_name = filename.replace(".txt", "")
                    self.capl_to_vba_map[rule_name] = content
                    
    def _load_vba_rules(self):
        """加载VBA规则"""
        vba_rules_dir = "/Users/cuisijia/source/rules/output/vba-rules-txt"
        for filename in os.listdir(vba_rules_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(vba_rules_dir, filename), "r") as f:
                    content = f.read()
                    rule_name = filename.replace(".txt", "")
                    self.vba_rule_map[rule_name] = content
                    
    def get_capl_mapping(self, capl_rule: str) -> Optional[str]:
        """获取CAPL规则的VBA映射"""
        return self.capl_to_vba_map.get(capl_rule)
        
    def get_vba_rule(self, vba_rule: str) -> Optional[str]:
        """获取VBA规则的详细说明"""
        return self.vba_rule_map.get(vba_rule) 