FROM public.ecr.aws/lambda/python:3.13

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies and the project itself to the Lambda task root
RUN pip install . --target "${LAMBDA_TASK_ROOT}"

# Set the CMD to your handler
CMD [ "flight_deals_engine.entrypoints.lambda_handler.lambda_handler" ]
