from io import BytesIO

import boto3
import pandas as pd

from config.settings import settings


class S3Service:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token or None,
            region_name=settings.aws_default_region,
        )

    def read_dataframe(self, object_key: str) -> pd.DataFrame:
        response = self.client.get_object(Bucket=settings.s3_bucket_name, Key=object_key)
        payload = response["Body"].read()

        if object_key.endswith(".parquet"):
            return pd.read_parquet(BytesIO(payload))
        if object_key.endswith(".json"):
            return pd.read_json(BytesIO(payload))
        return pd.read_csv(BytesIO(payload))

    def build_object_key(self, file_name: str) -> str:
        prefix = settings.s3_data_prefix.strip("/")
        if prefix:
            return f"{prefix}/{file_name}"
        return file_name
