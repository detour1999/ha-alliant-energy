"""Alliant Energy API Client."""
import logging
from datetime import datetime, date, timedelta
from typing import Optional
import json
import aiohttp
import time

_LOGGER = logging.getLogger(__name__)

class AlliantEnergyData:
    """Class to hold the energy data."""
    def __init__(self):
        self.usage_to_date: float = None
        self.forecasted_usage: float = None
        self.typical_usage: float = None
        self.cost_to_date: float = None
        self.forecasted_cost: float = None
        self.typical_cost: float = None
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.last_api_update: datetime = None
        self.last_meter_read: datetime = None
        self.cost_per_kwh: float = None
        self.customer_charge: float = 0.4932  # Daily customer charge
        self.is_cost_estimated: bool = False

    def calculate_cost(self, kwh: float, days: float) -> float:
        """Calculate cost including customer charge."""
        if self.cost_per_kwh is None or kwh is None or days is None:
            return None
        return (kwh * self.cost_per_kwh) + (days * self.customer_charge)

class AlliantEnergyAuthError(Exception):
    """Exception for authentication errors."""
    pass

class AlliantEnergyClient:
    """Client to handle Alliant Energy API interaction."""

    BASE_URL = "https://alliant-svc.smartcmobile.com"

    def __init__(self, username: str, password: str, store: Optional["Store"] = None):
        self._username = username
        self._password = password
        self._store = store
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._account_number: Optional[str] = None
        self._premise_number: Optional[str] = None
        self._meter_number: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._uuid: Optional[str] = None

    def _get_base_headers(self) -> dict:
        """Get base headers used in all requests."""
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "dnt": "1",
            "origin": "https://myaccount.alliantenergy.com",
            "priority": "u=1, i",
            "pt": "1",
            "referer": "https://myaccount.alliantenergy.com/",
            "sec-ch-ua": '"Not?A_Brand";v="99", "Chromium";v="130"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "uid": "2",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }

    async def _load_cached_auth(self) -> bool:
        """Load cached authentication data."""
        if not self._store:
            return False

        auth_data = await self._store.async_load()
        if not auth_data:
            return False

        now = time.time()
        if now >= auth_data.get("expires_at", 0) - 60:
            _LOGGER.debug("Cached token expired")
            return False

        self._token = auth_data.get("token")
        self._refresh_token = auth_data.get("refresh_token")
        self._token_expires_at = auth_data.get("expires_at")
        self._uuid = auth_data.get("uuid")
        self._account_number = auth_data.get("account_number")
        self._premise_number = auth_data.get("premise_number")
        self._meter_number = auth_data.get("meter_number")

        _LOGGER.debug("Loaded cached authentication data")
        return bool(self._token and self._meter_number)

    async def _save_auth_data(self):
        """Save authentication data to cache."""
        if not self._store:
            return

        auth_data = {
            "token": self._token,
            "refresh_token": self._refresh_token,
            "expires_at": self._token_expires_at,
            "uuid": self._uuid,
            "account_number": self._account_number,
            "premise_number": self._premise_number,
            "meter_number": self._meter_number,
        }

        await self._store.async_save(auth_data)
        _LOGGER.debug("Saved authentication data to cache")

    async def _get_token(self, use_refresh_token: bool = False) -> str:
        """Get authentication token."""
        auth_url = f"{self.BASE_URL}/UsermanagementAPI/api/1/Login/auth"

        payload = {
            "username": self._username,
            "password": self._password,
            "guestToken": "",
            "customattributes": {
                "ip": "",
                "client": "Web",
                "version": "10_15_7",
                "deviceId": "||Chrome||130||Mac OS X||10_15_7||",
                "deviceName": "Chrome",
                "deviceType": 0,
                "os": "Mac OS X"
            }
        }

        headers = {
            **self._get_base_headers(),
            "Content-Type": "application/json",
            "st": "PL",
            "uid": "1"
        }

        _LOGGER.debug("Authenticating with Alliant Energy...")
        async with self._session.post(auth_url, json=payload, headers=headers) as response:
            if response.status != 200:
                raise AlliantEnergyAuthError("Failed to authenticate")

            data = await response.json()
            if data["status"]["type"] != "success":
                raise AlliantEnergyAuthError(f"Authentication failed: {data['status']['message']}")

            self._token = data["data"]["accessToken"]
            self._refresh_token = data["data"]["refreshToken"]
            self._token_expires_at = time.time() + (data["data"]["expiresIn"] * 60)
            self._uuid = data["data"]["user"]["uuid"]

            await self._get_account_details()
            await self._save_auth_data()

            return self._token

    async def _ensure_token(self):
        """Ensure we have a valid token."""
        if not self._token:
            if not await self._load_cached_auth():
                await self._get_token(use_refresh_token=False)
        elif time.time() >= self._token_expires_at - 60:  # Refresh 1 minute before expiration
            try:
                await self._get_token(use_refresh_token=True)
            except AlliantEnergyAuthError:
                await self._get_token(use_refresh_token=False)

    async def _get_account_details(self):
        """Get account and premise numbers."""
        url = f"{self.BASE_URL}/Services/api/1/Addresses/User/{self._uuid}"

        headers = {
            **self._get_base_headers(),
            "Authorization": f"Bearer {self._token}"
        }

        async with self._session.get(url, headers=headers) as response:
            if response.status != 200:
                raise AlliantEnergyAuthError("Failed to get account details")

            data = await response.json()
            if not data["data"]:
                raise AlliantEnergyAuthError("No account found")

            account = data["data"][0]
            self._account_number = account["accountNumber"]
            self._premise_number = account["premiseNumber"]

            await self._get_meter_details()

    async def _get_meter_details(self):
        """Get meter number."""
        url = f"{self.BASE_URL}/Services/api/1/Usages/GetMeterAndPremise"

        headers = {
            **self._get_base_headers(),
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

        payload = {
            "accountNumber": self._account_number,
            "premiseNumber": self._premise_number
        }

        async with self._session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                raise AlliantEnergyAuthError("Failed to get meter details")

            data = await response.json()
            if not data["data"]:
                raise AlliantEnergyAuthError("No meter found")

            self._meter_number = data["data"][0]["meterNumber"]

    async def async_get_data(self) -> AlliantEnergyData:
        """Get the energy data."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        await self._ensure_token()

        today = datetime.now().date()
        first_of_month = today.replace(day=1)
        last_of_month = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)

        data = AlliantEnergyData()
        data.last_api_update = datetime.now()

        # Get historical data first
        historical_url = f"{self.BASE_URL}/UsageAPI/api/V1/Electric"
        historical_params = {
            "AccountNumber": f"{self._premise_number}-{self._account_number}",
            "MeterNumber": self._meter_number,
            "From": today.replace(year=today.year - 1).strftime("%Y-%m-%d"),
            "To": last_of_month.strftime("%Y-%m-%d"),
            "Uom": "kWh",
            "Periodicity": "MO"
        }

        headers = {
            **self._get_base_headers(),
            "Authorization": f"Bearer {self._token}"
        }

        async with self._session.get(historical_url, params=historical_params, headers=headers) as response:
            if response.status == 200:
                historical = (await response.json())["Result"]["electricUsages"]
                if historical:
                    # Sort by reading date for reliability
                    sorted_readings = sorted(
                        historical,
                        key=lambda x: datetime.fromisoformat(x["readingFrom"].replace("Z", "+00:00"))
                    )

                    # Calculate cost per kWh from most recent complete period
                    if sorted_readings:
                        latest_reading = sorted_readings[-1]
                        period_start = datetime.fromisoformat(latest_reading["readingFrom"].replace("Z", "+00:00"))
                        period_end = datetime.fromisoformat(latest_reading["readingTo"].replace("Z", "+00:00"))
                        days_in_period = (period_end - period_start).days
                        total_cost = float(latest_reading["amount"])
                        total_usage = float(latest_reading["consumption"])

                        # Subtract out customer charge
                        customer_charge_total = days_in_period * data.customer_charge
                        energy_cost = total_cost - customer_charge_total

                        if total_usage > 0:
                            data.cost_per_kwh = energy_cost / total_usage
                            _LOGGER.debug(
                                "Calculated cost per kWh from last period: $%.4f "
                                "(total cost: $%.2f - customer charge: $%.2f for %d days = $%.2f energy cost / %.1f kWh)",
                                data.cost_per_kwh,
                                total_cost,
                                data.customer_charge,
                                days_in_period,
                                energy_cost,
                                total_usage
                            )

                    # Calculate average period length for billing period projection
                    period_lengths = []
                    for reading in sorted_readings:
                        start = datetime.fromisoformat(reading["readingFrom"].replace("Z", "+00:00"))
                        end = datetime.fromisoformat(reading["readingTo"].replace("Z", "+00:00"))
                        period_lengths.append((end - start).days)

                    avg_period_length = round(sum(period_lengths) / len(period_lengths))

                    # Get last completed billing period
                    last_period = sorted_readings[-1]
                    last_period_end = datetime.fromisoformat(last_period["readingTo"].replace("Z", "+00:00"))

                    # Calculate current billing period
                    data.start_date = last_period_end.replace(tzinfo=None)
                    data.end_date = data.start_date + timedelta(days=avg_period_length)

                    # Set last meter read
                    data.last_meter_read = datetime.fromisoformat(
                        last_period["readingTo"].replace("Z", "+00:00")
                    )

            elif response.status == 401:
                _LOGGER.error("Authentication failed for historical data. Token may have expired.")
                await self._get_token()
                return await self.async_get_data()

        # Get projected data
        projected_url = f"{self.BASE_URL}/UsageAPI/api/V1/ProjectedElectric"
        projected_params = {
            "AccountNumber": f"{self._premise_number}-{self._account_number}",
            "MeterNumber": self._meter_number,
            "StartDate": first_of_month.strftime("%Y-%m-%d"),
            "EndDate": last_of_month.strftime("%Y-%m-%d"),
            "Type": "0"
        }

        async with self._session.get(projected_url, params=projected_params, headers=headers) as response:
            if response.status == 200:
                projected = (await response.json())["Result"]["projectedElectric"]
                try:
                    data.usage_to_date = float(projected["soFarThisMonthProjectedConsumption"])
                except (ValueError, TypeError):
                    data.usage_to_date = None

                try:
                    data.forecasted_usage = float(projected["projectedConsumption"])
                except (ValueError, TypeError):
                    data.forecasted_usage = None

                try:
                    data.typical_usage = float(projected["averageThisYearConsumption"])
                except (ValueError, TypeError):
                    data.typical_usage = None

                try:
                    api_cost = float(projected["soFarThisMonthProjectedAmount"])
                    if api_cost > 0:
                        data.cost_to_date = api_cost
                    elif data.cost_per_kwh and data.usage_to_date:
                        days_so_far = (datetime.now().replace(tzinfo=None) - data.start_date).days
                        data.cost_to_date = data.calculate_cost(data.usage_to_date, days_so_far)
                        data.is_cost_estimated = True
                except (ValueError, TypeError):
                    if data.cost_per_kwh and data.usage_to_date:
                        days_so_far = (datetime.now().replace(tzinfo=None) - data.start_date).days
                        data.cost_to_date = data.calculate_cost(data.usage_to_date, days_so_far)
                        data.is_cost_estimated = True

                try:
                    api_cost = float(projected["projectedAmount"])
                    if api_cost > 0:
                        data.forecasted_cost = api_cost
                    elif data.cost_per_kwh and data.forecasted_usage:
                        period_days = (data.end_date - data.start_date).days
                        data.forecasted_cost = data.calculate_cost(data.forecasted_usage, period_days)
                        data.is_cost_estimated = True
                except (ValueError, TypeError):
                    if data.cost_per_kwh and data.forecasted_usage:
                        period_days = (data.end_date - data.start_date).days
                        data.forecasted_cost = data.calculate_cost(data.forecasted_usage, period_days)
                        data.is_cost_estimated = True

                try:
                    data.typical_cost = float(projected["averageThisYearAmount"])
                except (ValueError, TypeError):
                    data.typical_cost = None

            elif response.status == 401:
                _LOGGER.error("Authentication failed for projected data. Token may have expired.")
            else:
                _LOGGER.error("Failed to get projected data: %s", response.status)

        return data

    async def async_close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        await self.async_close()
