# Lamuir task sandbox: the Python environment the agent's generated code runs in.
# Written for Lamuir (Claude Code, 2026-10-29). Debian-based Python 3.11 with the scientific stack at the versions
# the agent was tested against; the agent reads the installed versions at run time and adapts its API notes to them.
FROM python:3.11-slim

RUN pip install --no-cache-dir \
        numpy==2.4.6 pandas==3.1.0 scipy==1.17.1 statsmodels==0.15.0 scikit-learn==1.9.1 \
        matplotlib==3.11.2 seaborn==0.13.2 pyarrow==26.0.0 openpyxl==3.1.5 \
    && mkdir -p /app/data /app/output

WORKDIR /app
