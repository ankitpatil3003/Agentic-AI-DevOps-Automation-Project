# app/integrations/servicenow_client.py

import os
import requests
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

DEFAULT_RESOLUTION_CODE = os.getenv("DEFAULT_RESOLUTION_CODE", "Resolved by caller")

class ServiceNowClient:
    """
    Thin wrapper around ServiceNow Table API for the incident table.
    Ensures we (a) create with mandatory fields, (b) always PATCH by sys_id,
    and (c) satisfy resolution data policies when moving to state=6.
    """

    INSTANCE_URL = os.getenv("SERVICENOW_INSTANCE_URL")
    USERNAME = os.getenv("SERVICENOW_USERNAME")
    PASSWORD = os.getenv("SERVICENOW_PASSWORD")
    TABLE = "incident"

    HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

    @classmethod
    def _get_auth(cls):
        if not all([cls.INSTANCE_URL, cls.USERNAME, cls.PASSWORD]):
            raise ValueError("Missing ServiceNow credentials in .env file.")
        return (cls.USERNAME, cls.PASSWORD)

    # --------------------- helpers ---------------------

    @classmethod
    def _get_user_sys_id(cls, username: str) -> str | None:
        """
        Resolve a username -> sys_id for caller_id.
        """
        url = f"{cls.INSTANCE_URL}/api/now/table/sys_user"
        params = {"sysparm_query": f"user_name={username}", "sysparm_fields": "sys_id", "sysparm_limit": 1}
        r = requests.get(url, headers=cls.HEADERS, auth=cls._get_auth(), params=params, timeout=30)
        r.raise_for_status()
        rows = r.json().get("result", [])
        return rows[0]["sys_id"] if rows else None

    @classmethod
    @lru_cache(maxsize=1)
    def _resolution_field(cls) -> str:
        """
        Discover which column is labeled 'Resolution code' on incident.
        Many PDIs use u_resolution_code; fallback to 'close_code' otherwise.
        """
        url = f"{cls.INSTANCE_URL}/api/now/table/sys_dictionary"
        params = {
            "sysparm_query": "name=incident^label=Resolution code",
            "sysparm_fields": "element",
            "sysparm_limit": 1,
        }
        r = requests.get(url, headers=cls.HEADERS, auth=cls._get_auth(), params=params, timeout=30)
        r.raise_for_status()
        res = r.json().get("result", [])
        return res[0]["element"] if res else "close_code"

    @classmethod
    def get_incident(cls, sys_id: str) -> dict:
        url = f"{cls.INSTANCE_URL}/api/now/table/{cls.TABLE}/{sys_id}"
        params = {"sysparm_fields": "sys_id,number,state,incident_state,short_description"}
        r = requests.get(url, headers=cls.HEADERS, auth=cls._get_auth(), params=params, timeout=30)
        r.raise_for_status()
        return r.json()["result"]

    # ---------------------- CRUD ----------------------

    @classmethod
    def create_incident(
        cls,
        short_description: str,
        description: str,
        caller_username: str = "integration.incidentuser",
    ) -> dict:
        """
        Create the incident with mandatory fields and return {'sys_id','number'}.
        """
        caller_id = cls._get_user_sys_id(caller_username)
        payload = {
            "short_description": short_description,  # mandatory in your PDI
            "description": description,              # request-specific
            "caller_id": caller_id,                  # mandatory in your PDI
            "urgency": "2",
            "impact": "2",
            "category": "inquiry",
        }

        url = f"{cls.INSTANCE_URL}/api/now/table/{cls.TABLE}"
        r = requests.post(url, json=payload, headers=cls.HEADERS, auth=cls._get_auth(), timeout=30)
        print("CREATE status:", r.status_code, "body:", r.text)  # debug
        r.raise_for_status()

        res = r.json()["result"]
        return {"sys_id": res["sys_id"], "number": res["number"]}

    @classmethod
    def update_incident(cls, sys_id: str, work_notes: str = None,
                        state: str | int = None,
                        close_code: str = None,
                        close_notes: str = None) -> dict:
        """
        PATCH by sys_id. If moving to Resolved (6), include multiple resolution
        fields so we don't need sys_dictionary access. Unknown fields are ignored.
        """
        if not sys_id:
            raise ValueError("update_incident called without sys_id")

        url = f"{cls.INSTANCE_URL}/api/now/table/{cls.TABLE}/{sys_id}"
        payload: dict = {}

        if work_notes:
            payload["work_notes"] = work_notes

        if state is not None:
            # 6 = Resolved (Table API updates are by record sys_id) 
            payload["state"] = 6 if str(state).lower().startswith("resolv") else state
            payload["incident_state"] = payload["state"]

            if str(payload["state"]) == "6":
                # satisfy data policy: set code + notes (send all likely keys)
                code = close_code or DEFAULT_RESOLUTION_CODE
                notes = close_notes or "Automated remediation applied. See work notes."
                payload["close_notes"] = notes
                payload["close_code"] = code           # OOB field
                payload["u_resolution_code"] = code    # common custom field
                payload["resolution_code"] = code      # some PDIs use this

        params = {"sysparm_input_display_value": "true"}  # Table API accepts display labels for choices
        print("PATCH payload ->", payload, "sys_id:", sys_id)

        r = requests.patch(url, headers=cls.HEADERS, auth=cls._get_auth(),
                        json=payload, params=params, timeout=30)
        if not r.ok:
            print("PATCH failed:", r.status_code, r.text)
            r.raise_for_status()
        return r.json()
