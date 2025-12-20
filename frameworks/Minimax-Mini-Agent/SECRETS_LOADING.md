# MiniMax API Key Loading from Secrets File

## ✅ Implementation Complete

The Mini Agent has been configured to **always load the API key from `/adapt/secrets/m2.env`**.

## 🔐 Configuration Priority

1. **First priority**: `/adapt/secrets/m2.env` (if exists)
2. **Second priority**: `config.yaml` file

## 📁 Files Modified

### 1. `/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/config.py`

Modified the `from_yaml()` method to:
- Check for `/adapt/secrets/m2.env`
- Extract `MiniMax_M2_CODE_PLAN_API_KEY` from the secrets file
- Override the config.yaml API key with the secrets file value
- Show a 🔐 indicator when using secrets file

**Key changes:**
```python
# Load API key from secrets file first
secrets_file = Path("/adapt/secrets/m2.env")
if secrets_file.exists():
    for line in f:
        if line.startswith('MiniMax_M2_CODE_PLAN_API_KEY='):
            secrets_api_key = key_value
            break

# Use secrets API key if available
api_key = secrets_api_key if secrets_api_key else data["api_key"]
```

## ✅ Verification

When you run `mini-agent`, you should see:
```
🔐 Using API key from secrets file: /adapt/secrets/m2.env
```

This confirms the secrets file is being used.

## 🚀 Usage

```bash
# Run Mini Agent - automatically loads API key from /adapt/secrets/m2.env
mini-agent

# Or with resume
mini-agent --resume

# Or with workspace
mini-agent --workspace ./my-project
```

## 📝 Troubleshooting

If you see the error "Please configure a valid API Key":

1. Make sure `/adapt/secrets/m2.env` exists and contains:
   ```bash
   MiniMax_M2_CODE_PLAN_API_KEY="your-key-here"
   ```

2. Verify the file permissions:
   ```bash
   ls -la /adapt/secrets/m2.env
   ```

3. Test the API key extraction:
   ```bash
   python3 -c "
   from mini_agent.config import Config
   config = Config.load()
   print(f'✅ API key loaded: {config.llm.api_key[:20]}...')
   "
   ```

## 🔒 Security Benefits

- API key never stored in git-tracked config.yaml
- Secrets file in protected directory `/adapt/secrets/`
- Clear audit trail of where API key is loaded from
- Fallback to config.yaml if secrets file unavailable

## 🎯 Summary

✅ API key loads automatically from `/adapt/secrets/m2.env`
✅ No need to configure in config.yaml
✅ All other settings still loaded from config.yaml
✅ Error messages updated to reflect both sources
✅ Working and tested
