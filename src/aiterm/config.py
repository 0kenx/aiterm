import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .default_config import DEFAULT_CONFIG


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: str
    model: str
    instructions: Optional[str] = None
    include_path_commands: bool = False
    include_history_context: bool = False
    history_context_size: int = 500
    api_key: Optional[str] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create ModelConfig from dictionary."""
        return cls(
            provider=data['provider'],
            model=data['model'],
            instructions=data.get('instructions'),
            include_path_commands=data.get('include_path_commands', False),
            include_history_context=data.get('include_history_context', False),
            history_context_size=data.get('history_context_size', 500),
            api_key=data.get('api_key'),
            custom_options={k: v for k, v in data.items()
                          if k not in ['provider', 'model', 'instructions', 'include_path_commands',
                                     'include_history_context', 'history_context_size', 'api_key']}
        )


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderConfig':
        """Create ProviderConfig from dictionary."""
        return cls(
            base_url=data.get('base_url'),
            api_key=data.get('api_key'),
            custom_options={k: v for k, v in data.items() 
                          if k not in ['base_url', 'api_key']}
        )


@dataclass
class Config:
    """Main configuration class with new structure."""
    default_models: List[str] = field(default_factory=lambda: ["gpt4", "claude", "ollama"])
    allowed_commands: List[str] = field(default_factory=lambda: ["pwd", "ls", "echo", "date"])
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    history_file: str = "~/.local/share/aiterm/history.json"
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file."""
        config_path = Path("~/.config/aiterm/config.yaml").expanduser()
        
        if not config_path.exists():
            # Create default configuration
            config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = cls._create_default()
            default_config.save()
            return default_config
        
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        
        # Parse providers
        providers = {}
        if 'providers' in data:
            for name, provider_data in data['providers'].items():
                providers[name] = ProviderConfig.from_dict(provider_data or {})
        
        # Parse models
        models = {}
        if 'models' in data:
            for name, model_data in data['models'].items():
                if model_data and 'provider' in model_data:
                    models[name] = ModelConfig.from_dict(model_data)
        
        return cls(
            default_models=data.get('default_models', ["gpt4", "claude", "ollama"]),
            allowed_commands=data.get('allowed_commands', DEFAULT_CONFIG['allowed_commands']),
            providers=providers,
            models=models,
            history_file=data.get('history_file', DEFAULT_CONFIG['history_file'])
        )
    
    @classmethod
    def _create_default(cls) -> 'Config':
        """Create default configuration."""
        providers = {
            'ollama': ProviderConfig(base_url='http://localhost:11434'),
            'openai': ProviderConfig(),
            'anthropic': ProviderConfig(),
            'test': ProviderConfig()
        }
        
        models = {
            'gpt4': ModelConfig(
                provider='openai',
                model='gpt-4o',
                include_path_commands=False,
                include_history_context=False,
                custom_options={'temperature': 0.7}
            ),
            'gpt3': ModelConfig(
                provider='openai', 
                model='gpt-3.5-turbo',
                include_path_commands=False,
                include_history_context=False
            ),
            'claude': ModelConfig(
                provider='anthropic',
                model='claude-3-sonnet-20240229',
                include_path_commands=False,
                include_history_context=False
            ),
            'ollama': ModelConfig(
                provider='ollama',
                model='llama3.1',
                include_path_commands=True,
                include_history_context=True,
                history_context_size=500
            ),
            'test': ModelConfig(
                provider='test',
                model='test-model',
                include_path_commands=True,
                include_history_context=True,
                history_context_size=200
            )
        }
        
        return cls(
            default_models=['test', 'gpt4', 'claude', 'ollama'],
            allowed_commands=DEFAULT_CONFIG['allowed_commands'],
            providers=providers,
            models=models,
            history_file=DEFAULT_CONFIG['history_file']
        )
    
    def save(self):
        """Save configuration to file."""
        config_path = Path("~/.config/aiterm/config.yaml").expanduser()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for YAML
        data = {
            'default_models': self.default_models,
            'allowed_commands': self.allowed_commands,
            'providers': {},
            'models': {},
            'history_file': self.history_file
        }
        
        # Convert providers
        for name, provider in self.providers.items():
            provider_dict = {}
            if provider.base_url:
                provider_dict['base_url'] = provider.base_url
            if provider.api_key:
                provider_dict['api_key'] = provider.api_key
            if provider.custom_options:
                provider_dict.update(provider.custom_options)
            data['providers'][name] = provider_dict
        
        # Convert models
        for name, model in self.models.items():
            model_dict = {
                'provider': model.provider,
                'model': model.model,
                'include_path_commands': model.include_path_commands,
                'include_history_context': model.include_history_context,
                'history_context_size': model.history_context_size
            }
            if model.instructions:
                model_dict['instructions'] = model.instructions
            if model.api_key:
                model_dict['api_key'] = model.api_key
            if model.custom_options:
                model_dict.update(model.custom_options)
            data['models'][name] = model_dict
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.models.get(model_name)
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider_name)
    
    def get_api_key(self, model_name: str) -> Optional[str]:
        """Get API key for a model, checking model config, provider config, then env vars."""
        model_config = self.get_model_config(model_name)
        if not model_config:
            return None
            
        # Check model-specific API key
        if model_config.api_key:
            return model_config.api_key
            
        # Check provider API key
        provider_config = self.get_provider_config(model_config.provider)
        if provider_config and provider_config.api_key:
            return provider_config.api_key
            
        # Check environment variables
        env_var_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY'
        }
        
        env_var = env_var_map.get(model_config.provider)
        if env_var:
            return os.environ.get(env_var)
            
        return None