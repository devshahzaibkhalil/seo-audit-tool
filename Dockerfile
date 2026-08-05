# For hosts that prefer a container (Hugging Face Spaces, Fly.io, Cloud Run).
FROM python:3.12-slim
WORKDIR /app
COPY seo_tool.py .
ENV PORT=7860
EXPOSE 7860
CMD ["python", "seo_tool.py"]
