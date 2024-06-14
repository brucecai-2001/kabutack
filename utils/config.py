import yaml

class YAML_Config:
    """
    read the yaml configuration file 
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.config = self._load_config()

    def _load_config(self):
        # 私有方法，用于加载 YAML 配置文件
        with open(self.file_path, 'r') as file:
            return yaml.safe_load(file)

    def get(self, path):
        # 获取配置项的值，path 是一个字符串，如 'server.port'
        keys = path.split('.')
        value = self.config
        for key in keys:
            value = value.get(key)
            if value is None:
                break
        return value
    
    def update(self, key, new_value):
        # 更新配置项的值
        keys = key.split('.')
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = new_value


    def print_config(self):
        # 打印整个配置
        print(self.config)

# Singleton
agent_config = YAML_Config('config.yaml')