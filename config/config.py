import yaml
import dotenv
from pathlib import Path

config_dir = Path(__file__).parent.parent.resolve() / "config"

# load yaml config
with open(config_dir / "config.yml", 'r') as f:
    config_yaml = yaml.safe_load(f)

# load .env config
config_env = dotenv.dotenv_values(config_dir / "config.env")

# config parameters
bot_token = config_yaml["BOT_TOKEN"]
app_id = config_yaml["APP_ID"]
api_hash = config_yaml["API_HASH"]
bot_api = config_yaml["BOT_API"]
api_key = config_yaml["API_KEY"]
test_user_id = config_yaml["TEST_USER_ID"]