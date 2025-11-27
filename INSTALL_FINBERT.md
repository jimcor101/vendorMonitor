# Installing FinBERT Dependencies

PyTorch (torch) requires platform-specific installation. Follow the instructions for your system:

## Quick Install

### Step 1: Check Your System
```bash
# Check if you have Apple Silicon (M1/M2/M3) or Intel Mac
uname -m
# Output: "arm64" = Apple Silicon, "x86_64" = Intel
```

### Step 2: Install PyTorch

#### For Mac (Apple Silicon - M1/M2/M3)
```bash
pip install torch torchvision torchaudio --break-system-packages
```

#### For Mac (Intel)
```bash
pip install torch torchvision torchaudio --break-system-packages
```

#### For Linux
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### For Windows
```bash
pip install torch torchvision torchaudio
```

### Step 3: Install Other Dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

### Step 4: Verify Installation
```bash
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "from transformers import AutoTokenizer; print('Transformers OK')"
```

## Complete Installation (One Command)

### Mac (All versions)
```bash
pip install torch torchvision torchaudio transformers sentencepiece --break-system-packages
```

### Linux (CPU only)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentencepiece
```

### Windows
```bash
pip install torch torchvision torchaudio transformers sentencepiece
```

## Troubleshooting

### Issue: "No matching distribution found for torch"

**Solution**: Use the platform-specific command above instead of pip install from requirements.txt

### Issue: "Could not find a version that satisfies the requirement torch"

**Solution**: Make sure you're using Python 3.8 or later:
```bash
python --version  # Should be 3.8+
```

### Issue: Installation takes forever

**Solution**: PyTorch is large (~2GB). Be patient or use a faster internet connection.

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Solution**: Activate your virtual environment or install in the correct Python environment:
```bash
which python  # Verify you're using the right Python
pip install torch
```

## Minimal Install (Just What You Need)

If you want to minimize download size:

```bash
# Mac
pip install torch --index-url https://download.pytorch.org/whl/cpu --break-system-packages
pip install transformers sentencepiece --break-system-packages

# Linux
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentencepiece
```

## Verify FinBERT Works

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
print('Loading FinBERT model...')
tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')
print('✓ FinBERT successfully installed!')
"
```

## Alternative: Use VADER Only

If PyTorch installation is problematic, you can use VADER (already installed):

```bash
# Just use VADER (no FinBERT needed)
python vendor_monitor.py --analyzer vader
```

VADER is fast and works well for general sentiment, though not as accurate for financial text.

## Disk Space Requirements

- PyTorch: ~2GB
- FinBERT model: ~440MB
- Transformers: ~300MB
- **Total**: ~2.7GB

Make sure you have at least 3GB free space.

## Official Resources

- [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/installation)
- [FinBERT Model Card](https://huggingface.co/ProsusAI/finbert)
