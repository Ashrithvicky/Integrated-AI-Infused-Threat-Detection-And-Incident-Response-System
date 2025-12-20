# services/drift/rules_engine.py
"""
Simple policy drift rules engine for IAM, S3 and Security Groups.

Input: a config snapshot dict like:
{
  "iam": {
    "users": [
      {"name": "alice", "policies": [ { "Statement": [...] }, ... ]}
    ]
  },
  "s3": {
    "buckets": [
      {"name": "my-bucket", "public": true, "policies": [ ... ]}
    ]
  },
  "security_groups": [
    {
      "name": "default",
      "inbound": [ {"port": 22, "cidr": "0.0.0.0/0"} ],
      "outbound": [ ... ]
    }
  ]
}

Output: list of findings dicts with "issue", "severity", "details"/other fields.
"""

from typing import List, Dict, Any

def check_s3_public(bucket_conf: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues = []
    name = bucket_conf.get("name", "unknown-bucket")

    # 1) Direct "public" flag
    if bucket_conf.get("public", False):
        issues.append({
            "issue": "s3_public_bucket",
            "severity": "high",
            "bucket": name,
            "details": f"S3 bucket {name} is marked public"
        })

    # 2) Policy-based public
    for pol in bucket_conf.get("policies", []):
        statements = pol.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]
        for s in statements:
            effect = (s.get("Effect") or "").lower()
            if effect != "allow":
                continue
            principal = s.get("Principal")
            action = s.get("Action", [])
            if isinstance(action, str):
                actions = [action]
            else:
                actions = action

            # if Principal == "*" and we allow wide S3 privileges
            if principal == "*" or principal == {"AWS": "*"}:
                if any(a in ("s3:*", "s3:GetObject", "s3:PutObject") for a in actions):
                    issues.append({
                        "issue": "s3_overpermissive_policy",
                        "severity": "high",
                        "bucket": name,
                        "policy": pol,
                        "details": f"S3 bucket {name} policy allows public access"
                    })
    return issues


def check_iam_policy(iam_conf: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues = []
    for user in iam_conf.get("users", []):
        uname = user.get("name", "unknown-user")
        for pol in user.get("policies", []):
            statements = pol.get("Statement", [])
            if isinstance(statements, dict):
                statements = [statements]
            for stmt in statements:
                eff = (stmt.get("Effect") or "").lower()
                if eff != "allow":
                    continue
                action = stmt.get("Action", [])
                if isinstance(action, str):
                    acts = [action]
                else:
                    acts = action

                # basic privilege escalation actions
                for a in acts:
                    if a in ("iam:CreateUser", "iam:AttachUserPolicy",
                             "iam:PutUserPolicy", "iam:CreateAccessKey"):
                        issues.append({
                            "issue": "iam_privilege_escalation",
                            "severity": "high",
                            "user": uname,
                            "action": a,
                            "details": f"User {uname} can perform {a}"
                        })
    return issues


def check_security_groups(sgs: Any) -> List[Dict[str, Any]]:
    issues = []
    for sg in sgs or []:
        name = sg.get("name", "sg-unknown")
        for rule in sg.get("inbound", []):
            port = rule.get("port")
            cidr = rule.get("cidr", "0.0.0.0/0")
            # common dangerous cases: SSH/RDP open to world
            if cidr == "0.0.0.0/0" and port in (22, 3389):
                issues.append({
                    "issue": "wide_open_ssh_rdp",
                    "severity": "high",
                    "sg": name,
                    "port": port,
                    "cidr": cidr,
                    "details": f"SecurityGroup {name} allows {port}/tcp from {cidr}"
                })
    return issues


def run_policy_checks(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Top-level policy checker.
    """
    findings: List[Dict[str, Any]] = []

    iam_conf = snapshot.get("iam", {})
    s3_conf = snapshot.get("s3", {})
    sg_conf = snapshot.get("security_groups", [])

    findings.extend(check_iam_policy(iam_conf))

    if isinstance(s3_conf, dict):
        for b in s3_conf.get("buckets", []):
            findings.extend(check_s3_public(b))

    findings.extend(check_security_groups(sg_conf))

    return findings


if __name__ == "__main__":
    # quick self-test
    example = {
        "iam": {
            "users": [
                {
                    "name": "alice",
                    "policies": [
                        {"Statement":[{"Effect":"Allow","Action":"iam:CreateUser"}]}
                    ]
                }
            ]
        },
        "s3": {
            "buckets": [
                {"name":"logs-bucket","public":True,"policies":[]}
            ]
        },
        "security_groups": [
            {
                "name":"default",
                "inbound":[{"port":22,"cidr":"0.0.0.0/0"}],
                "outbound":[]
            }
        ]
    }
    print(run_policy_checks(example))
