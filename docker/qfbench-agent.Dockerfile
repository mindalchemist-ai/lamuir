# Agent layer for running on QF-Bench: QF-Bench's own sandbox image plus the agent.
# Build context is the repository root. scripts/run_qfbench.py builds this image and then each
# task's own environment/Dockerfile on top of it, so a task's data and extra packages are installed
# exactly as QF-Bench defines them.
ARG BASE
FROM ${BASE}

LABEL org.opencontainers.image.title="lamuir" \
      org.opencontainers.image.description="Quant finance coding agent; model: NVIDIA Nemotron, served on Nebius Token Factory"

# The agent's own interpreter, kept apart from the sandbox Python the task code runs in: Python 3.13
# with the exact packages of the environment the agent was developed in (docker/agent-requirements.txt).
COPY docker/agent-requirements.txt /tmp/agent-requirements.txt
RUN pip install --no-cache-dir uv==0.9.5 \
    && UV_PYTHON_INSTALL_DIR=/opt/agent-python uv venv --python 3.13 /opt/agent \
    && uv pip install --no-cache --python /opt/agent/bin/python -r /tmp/agent-requirements.txt \
    && rm /tmp/agent-requirements.txt

# litellm would otherwise fetch its price map over the network on import.
ENV LITELLM_LOCAL_MODEL_COST_MAP=True \
    MSWEA_COST_TRACKING=ignore_errors \
    MSWEA_SILENT_STARTUP=1 \
    MSWEA_CONFIGURED=true

COPY agent/ /opt/

ENTRYPOINT ["python", "/opt/solve.py"]
