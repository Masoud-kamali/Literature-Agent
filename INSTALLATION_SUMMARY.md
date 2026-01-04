# Literature Agent - Installation Summary

## ✅ Installation Complete!

All dependencies have been successfully installed for the literature-agent project.

## Environment Setup

### 1. Literature Agent Environment (Poetry)
- **Location**: `/home/student.unimelb.edu.au/mkkamali/.cache/pypoetry/virtualenvs/literature-agent-VrwNs22c-py3.10`
- **Python**: 3.10.12
- **Status**: ✅ Fully configured

**Installed packages:**
- pydantic, pydantic-settings
- httpx, beautifulsoup4, lxml
- openai, langgraph, langchain-core
- tenacity, loguru, feedparser, pandas
- python-dateutil
- pytest (dev)

**PyTorch** (installed separately via pip):
- torch==2.9.0+cu128
- torchvision==0.24.0+cu128
- CUDA 12.8 compatible
- GPU access: ✅ NVIDIA L40S-24Q detected

### 2. vLLM Environment (Conda)
- **Location**: `~/miniforge-pypy3/envs/vllm`
- **Python**: 3.10
- **Status**: ✅ Fully configured

**Installed packages:**
- vllm==0.13.0
- torch==2.9.0+cu128
- torchvision==0.24.0+cu128
- All vLLM dependencies

## GPU Configuration

✅ NVIDIA Driver installed and working:
```
Driver Version: 570.124.06
CUDA Version: 12.8
GPU: NVIDIA L40S-24Q (24GB VRAM)
```

✅ PyTorch CUDA access verified in both environments

## Next Steps

### 1. Start vLLM Server

In a **separate terminal window**, run:

```bash
~/start_vllm.sh
```

Or manually:

```bash
source ~/miniforge-pypy3/etc/profile.d/conda.sh
conda activate vllm
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9
```

**Note**: The first run will download the model weights (~16GB for Llama-3.1-8B-Instruct).

### 2. Configure Environment Variables (Optional)

Edit the `.env` file in the literature-agent directory:

```bash
cd ~/literature-agent
nano .env
```

Update `OPENALEX_MAILTO` with your actual email address for better API rate limits.

### 3. Verify vLLM Connection

Once the vLLM server is running, test the connection:

```bash
cd ~/literature-agent
poetry run python scripts/verify_setup.py
```

All checks should pass.

### 4. Run the Literature Agent

Process papers from the last 7 days:

```bash
cd ~/literature-agent
poetry run python scripts/run_weekly.py
```

## Quick Reference

### Activate Literature Agent Environment
```bash
cd ~/literature-agent
poetry shell
```

### Activate vLLM Environment
```bash
source ~/miniforge-pypy3/etc/profile.d/conda.sh
conda activate vllm
```

### Check GPU Status
```bash
nvidia-smi
```

### Check vLLM Server Status
```bash
curl http://localhost:8000/v1/models
```

## Environment Separation

**Why separate environments?**

The literature-agent and vLLM are installed in separate environments to avoid dependency conflicts. This is a best practice when working with complex ML frameworks.

- **literature-agent** (poetry): Contains the application code and dependencies
- **vllm** (conda): Contains vLLM server and its specific PyTorch/CUDA dependencies

Both environments have PyTorch installed with CUDA 12.8 support and can access the GPU.

## Troubleshooting

### vLLM Server Won't Start
- Check GPU memory: `nvidia-smi`
- Reduce `--gpu-memory-utilization` to 0.7 or 0.8
- Try a smaller model (Llama-3.1-8B instead of 70B)

### Out of Memory Errors
- Reduce `--max-model-len` to 2048
- Lower `--gpu-memory-utilization`
- Close other GPU-using processes

### Connection Refused
- Ensure vLLM server is running: `curl http://localhost:8000/v1/models`
- Check firewall settings
- Verify port 8000 is not in use: `lsof -i :8000`

## Documentation

For detailed usage instructions, see:
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [START_HERE.md](START_HERE.md) - Project overview

## Support

For issues or questions:
- Check the troubleshooting section in README.md
- Review the example outputs in EXAMPLE_OUTPUT.md
- Consult the prompts documentation in PROMPTS.md

---

**Installation Date**: January 4, 2026
**Installed By**: Student (mkkamali)
**GPU**: NVIDIA L40S-24Q (24GB)
**CUDA**: 12.8
**Python**: 3.10.12
