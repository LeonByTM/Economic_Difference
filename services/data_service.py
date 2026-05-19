from io import BytesIO

from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
import streamlit as st

from services.s3_service import S3Service

_BUCKET = "economic-warehouse-curated"
_CACHE_TTL = 3 * 3600  # 3 hours


_CREDS_MSG = "Use the **🔑 Refresh AWS Credentials** panel in the sidebar to enter your temporary credentials."


def _raise_user_friendly_aws_error(err: ClientError) -> None:
    code = err.response.get("Error", {}).get("Code")
    if code in ("ExpiredToken", "InvalidClientTokenId", "InvalidAccessKeyId", "AuthFailure", "SignatureDoesNotMatch"):
        st.error(f"AWS credentials invalid or expired. {_CREDS_MSG}")
        st.stop()
    raise err


def _read(key: str) -> pd.DataFrame:
    svc = S3Service()
    try:
        resp = svc.client.get_object(Bucket=_BUCKET, Key=key)
    except NoCredentialsError:
        st.error(f"No AWS credentials found. {_CREDS_MSG}")
        st.stop()
    except ClientError as err:
        _raise_user_friendly_aws_error(err)
    return pd.read_parquet(BytesIO(resp["Body"].read()))


@st.cache_data(ttl=_CACHE_TTL, show_spinner="Loading development data…")
def load_development_master() -> pd.DataFrame:
    df = _read(
        "warehouse/development_master/part-00000-fccf0d55-016f-4254-920e-1c991347d508-c000.snappy.parquet"
    )
    df.columns = [c.strip() for c in df.columns]
    df["year"] = df["year"].astype(int)
    return df.sort_values(["country", "year"]).reset_index(drop=True)


@st.cache_data(ttl=_CACHE_TTL, show_spinner="Loading macro data…")
def load_macro_master() -> pd.DataFrame:
    """Concatenates all daily macro_master partitions into a single dataframe."""
    svc = S3Service()
    paginator = svc.client.get_paginator("list_objects_v2")
    frames = []
    try:
        page_iterator = paginator.paginate(Bucket=_BUCKET, Prefix="warehouse/macro_master/")
        for page in page_iterator:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".parquet"):
                    continue
                date_str = key.split("Date=")[1].split("/")[0]
                resp = svc.client.get_object(Bucket=_BUCKET, Key=key)
                part = pd.read_parquet(BytesIO(resp["Body"].read()))
                part["date"] = pd.to_datetime(date_str)
                frames.append(part)
    except (ClientError, NoCredentialsError) as err:
        if isinstance(err, NoCredentialsError):
            st.error(f"No AWS credentials found. {_CREDS_MSG}")
            st.stop()
        _raise_user_friendly_aws_error(err)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=_CACHE_TTL, show_spinner="Loading market data…")
def load_market_master() -> pd.DataFrame:
    """Concatenates all daily market_master partitions into a single dataframe."""
    svc = S3Service()
    paginator = svc.client.get_paginator("list_objects_v2")
    frames = []
    try:
        page_iterator = paginator.paginate(Bucket=_BUCKET, Prefix="warehouse/market_master/")
        for page in page_iterator:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".parquet"):
                    continue
                date_str = key.split("Date=")[1].split("/")[0]
                resp = svc.client.get_object(Bucket=_BUCKET, Key=key)
                part = pd.read_parquet(BytesIO(resp["Body"].read()))
                part["date"] = pd.to_datetime(date_str)
                frames.append(part)
    except (ClientError, NoCredentialsError) as err:
        if isinstance(err, NoCredentialsError):
            st.error(f"No AWS credentials found. {_CREDS_MSG}")
            st.stop()
        _raise_user_friendly_aws_error(err)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(["date", "country"]).reset_index(drop=True)


# Legacy helper kept for compatibility
def load_dataset(file_name: str) -> pd.DataFrame:
    svc = S3Service()
    try:
        response = svc.client.get_object(
            Bucket=_BUCKET, Key=svc.build_object_key(file_name)
        )
    except ClientError as err:
        _raise_user_friendly_aws_error(err)
    return pd.read_parquet(BytesIO(response["Body"].read()))
